"""
Agent streaming service for the webapp.

Runs the Deep Agents pipeline in a background thread, normalizes LangGraph
stream chunks into JSON-serializable events, and enforces a global run-lock
(shared filesystem memory is not safe under concurrent runs).

Each run is bound to the logged-in user: the agent's filesystem backend routes
that user's positions to `agent_fs/users/<u>/memories`, while the learning
brain (lessons.md, signals_log/) stays shared. After each run the memory tree
is synced to the Django DB and signal win-rates are recomputed deterministically.
"""
import re
import threading
from datetime import datetime
from pathlib import Path

import config
from tools import _save_intraday_cache

from .memory_sync import load_positions, memory_dirs, sync_all
from .learning import reinforce_learning
from .models import ChatMessage

RUN_LOCK = threading.Lock()

TOOLS_THAT_TAKE_SYMBOL = {
    "get_price_data", "get_technical_analysis", "get_fundamentals",
    "get_relative_strength", "get_risk_adjusted_returns",
    "get_momentum_indicators", "get_trend_indicators",
    "get_volatility_indicators", "get_volume_indicators",
    "get_pivot_points", "get_quant_factors",
    "get_insider_transactions", "get_candlestick_patterns",
}

_MAX_HISTORY_TURNS = 10


# ---------------------------------------------------------------------------
# Per-user chat history (DB-backed)
# ---------------------------------------------------------------------------
def get_history(username: str, session_key: str) -> list[dict]:
    if not username or not session_key:
        return []
    qs = ChatMessage.objects.filter(
        owner__username=username, session_key=session_key
    ).order_by("created_at")
    return [{"role": m.role, "content": m.content} for m in qs]


def reset_history(username: str, session_key: str) -> None:
    if username and session_key:
        ChatMessage.objects.filter(
            owner__username=username, session_key=session_key
        ).delete()


# ---------------------------------------------------------------------------
# Stream normalization
# ---------------------------------------------------------------------------
_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def _split_think(content: str):
    m = _THINK_RE.search(content)
    if not m:
        return None, content.strip()
    after = content[m.end():].strip()
    return m.group(1).strip(), after


def _normalize_chunk(chunk, tool_called: set, written: set, reviewed: set) -> list[dict]:
    events: list[dict] = []
    namespace = None
    if isinstance(chunk, tuple) and len(chunk) == 2:
        ns, updates = chunk
        namespace = " > ".join(str(n) for n in ns) if ns else "main"
    else:
        updates = chunk

    if namespace:
        events.append({"type": "namespace", "name": namespace})
    if not isinstance(updates, dict):
        return events

    for node_name, node_output in updates.items():
        events.append({"type": "node", "name": node_name})
        if isinstance(node_output, dict):
            for msg in node_output.get("messages", []):
                mtype = getattr(msg, "type", type(msg).__name__)
                if mtype == "ai":
                    content = getattr(msg, "content", "") or ""
                    if content:
                        think, rest = _split_think(content)
                        if think:
                            events.append({"type": "thinking", "content": think})
                        if rest:
                            events.append({"type": "response", "content": rest})
                    for tc in getattr(msg, "tool_calls", []) or []:
                        name = tc.get("name", "?") if isinstance(tc, dict) else getattr(tc, "name", "?")
                        args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
                        if name == "task" and isinstance(args, dict):
                            events.append({
                                "type": "subagent",
                                "name": args.get("agent") or args.get("ticker") or "task",
                                "args": args,
                            })
                        else:
                            events.append({"type": "tool_call", "name": name, "args": args})
                        if name in TOOLS_THAT_TAKE_SYMBOL and isinstance(args, dict) and args.get("symbol"):
                            tool_called.add(args["symbol"].upper())
                        if name in ("write_file", "edit_file") and isinstance(args, dict):
                            fp = args.get("file_path", "")
                            if "/memories/" in fp:
                                written.add(fp)
                        if name == "read_file" and isinstance(args, dict):
                            fp = args.get("file_path", "")
                            if "/memories/" in fp and ("open_trades" in fp or "pending_entries" in fp):
                                reviewed.add(fp)
                elif mtype == "tool":
                    events.append({
                        "type": "tool_result",
                        "name": getattr(msg, "name", "?"),
                        "content": (getattr(msg, "content", "") or "")[:2000],
                    })
                elif mtype == "human":
                    events.append({"type": "user", "content": (getattr(msg, "content", "") or "")[:500]})
            for k, v in node_output.items():
                if k == "messages":
                    continue
                events.append({"type": "state", "key": k, "value": str(v)[:300]})
        elif isinstance(node_output, list):
            for item in node_output:
                events.append({"type": "state", "key": "output", "value": str(item)[:200]})
        else:
            events.append({"type": "state", "key": node_name, "value": str(node_output)[:300]})
    return events


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
class AgentRunner:
    def __init__(self, username: str | None = None, session_key: str | None = None):
        self.username = username
        self.session_key = session_key
        self._agent = None
        self._backend = None

    def _get_agent(self):
        if self._agent is None:
            from agents import build_agent
            self._agent, self._backend = build_agent(self.username)
        return self._agent, self._backend

    def _build_messages(self, query: str, scan: bool) -> list[dict]:
        if scan:
            return [{"role": "user", "content": query}]
        history = (
            get_history(self.username, self.session_key)
            if self.username and self.session_key
            else []
        )
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": query})
        return messages

    def run(self, query: str, scan: bool = False):
        def job(event_cb):
            if RUN_LOCK.locked():
                event_cb({"type": "status", "message": "Queued — a run is already in progress."})
            with RUN_LOCK:
                config.set_active_memories_root(
                    config.user_memory_root(self.username) if self.username else None
                )
                event_cb({"type": "status", "message": "Run started."})
                scan_payload = None
                try:
                    scan_payload = self._execute(query, event_cb, scan)
                except Exception as exc:  # noqa: BLE001 — surfaced to the UI
                    event_cb({"type": "error", "message": f"{type(exc).__name__}: {exc}"})
                finally:
                    config.set_active_memories_root(None)
                    try:
                        summary = reinforce_learning()
                        if self.username:
                            sync_all(self.username)
                        if summary:
                            event_cb({
                                "type": "learning",
                                "summary": summary,
                            })
                    except Exception as exc:
                        import logging
                        logging.getLogger(__name__).exception(
                            "Post-run learning/sync failed for user %s", self.username
                        )
                        event_cb({
                            "type": "error",
                            "message": f"Post-run sync failed: {type(exc).__name__}: {exc}",
                        })
                    if scan and scan_payload is not None:
                        event_cb({"type": "scan_result", "positions": scan_payload})
                    # Generate clean daily signals after a scan (separate LLM call)
                    if scan and self.username:
                        try:
                            from .daily_signals import generate_daily_signals
                            signals = generate_daily_signals(self.username)
                            event_cb({
                                "type": "daily_signals",
                                "count": len(signals),
                                "signals": signals,
                            })
                        except Exception as exc:
                            import logging
                            logging.getLogger(__name__).exception(
                                "Daily signals generation failed for %s", self.username
                            )
                    event_cb({"type": "done"})
        return job

    def _execute(self, query: str, event_cb, scan: bool):
        agent, _backend = self._get_agent()
        tool_called: set[str] = set()
        written: set[str] = set()
        reviewed: set[str] = set()
        last_response = ""

        pre_open: set[str] = set()
        if scan:
            dirs = memory_dirs()
            for d in (dirs["open"], dirs["pending"]):
                if d.is_dir():
                    pre_open |= {f.stem for f in d.glob("*.md")}

        for chunk in agent.stream(
            {"messages": self._build_messages(query, scan)},
            stream_mode="updates",
            subgraphs=True,
        ):
            for ev in _normalize_chunk(chunk, tool_called, written, reviewed):
                if ev["type"] == "response" and ev["content"].strip():
                    last_response = ev["content"]
                event_cb(ev)

        _save_intraday_cache()

        if scan:
            self._compliance(event_cb, pre_open, written, reviewed, tool_called)
            if self.username:
                sync_all(self.username)
            return load_positions(self.username)
        self._store_turn(query, last_response)
        return None

    def _store_turn(self, query: str, answer: str):
        if not self.username or not self.session_key:
            return

        from .models import ChatSession

        user_id = self._user_id()
        session, _ = ChatSession.objects.get_or_create(
            session_key=self.session_key,
            defaults={"owner_id": user_id, "title": "New chat"},
        )
        session.save(update_fields=["updated_at"])  # bump updated_at

        ChatMessage.objects.create(
            owner_id=user_id, session=session, session_key=self.session_key,
            role="user", content=query,
        )
        if answer.strip():
            ChatMessage.objects.create(
                owner_id=user_id, session=session, session_key=self.session_key,
                role="assistant", content=answer,
            )
        # Trim history beyond the turn cap.
        ids = list(
            ChatMessage.objects.filter(
                owner_id=user_id, session_key=self.session_key
            ).values_list("id", flat=True)
        )
        excess = len(ids) - _MAX_HISTORY_TURNS * 2
        if excess > 0:
            ChatMessage.objects.filter(id__in=ids[:excess]).delete()

    def _user_id(self) -> int:
        from django.contrib.auth import get_user_model
        return get_user_model().objects.get(username=self.username).pk

    # -- compliance (mirrors the CLI's post-run reconciliation) -------------
    def _tracked_symbols(self, written: set[str]) -> set[str]:
        tracked: set[str] = set()
        for fp in written:
            parts = Path(fp).stem.split("--")
            tkr = (parts[-1] if len(parts) > 1 else parts[0]).upper()
            if tkr in config.WATCHLIST:
                tracked.add(tkr)
        dirs = memory_dirs()
        for d in (dirs["open"], dirs["pending"], dirs["watch"], dirs["closed"]):
            if d.is_dir():
                for f in d.glob("*.md"):
                    parts = f.stem.split("--")
                    tkr = (parts[-1] if len(parts) > 1 else parts[0]).upper()
                    if tkr in config.WATCHLIST:
                        tracked.add(tkr)
        return tracked

    def _compliance(self, event_cb, pre_open, written, reviewed, tool_called):
        reviewed_roots = {
            Path(fp).stem for fp in (written | reviewed)
            if fp.startswith("/memories/open_trades/") or fp.startswith("/memories/pending_entries/")
        }
        unresolved = pre_open - reviewed_roots
        if unresolved:
            event_cb({"type": "compliance", "level": "warn",
                      "message": f"{len(unresolved)} carryover open trade(s) were not reviewed during this run: {', '.join(sorted(unresolved))}"})
        else:
            event_cb({"type": "compliance", "level": "ok",
                      "message": f"All {len(pre_open)} carryover open trade(s) reviewed." if pre_open else "No carryover open trades."})

        missing = tool_called - self._tracked_symbols(written)
        if missing:
            today = datetime.now().strftime("%Y-%m-%d")
            watch_dir = memory_dirs()["watch"]
            watch_dir.mkdir(parents=True, exist_ok=True)
            for sym in sorted(missing):
                fp = watch_dir / f"{sym}.md"
                body = (
                    f"---\n"
                    f"date: {today}\n"
                    f"ticker: {sym}\n"
                    f"direction: reject\n"
                    f"entry_price: null\n"
                    f"exit_price: null\n"
                    f"rationale: >\n"
                    f"  Auto-logged by compliance check.\n"
                    f"signals_used: []\n"
                    f"outcome: completed\n"
                    f"return_realized_pct: null\n"
                    f"lessons: >\n"
                    f"  Agent oversight: analyzed but did not log.\n"
                    f"---\n"
                )
                fp.write_text(body, encoding="utf-8")
            event_cb({"type": "compliance", "level": "warn",
                      "message": f"Auto-logged {len(missing)} analyzed symbol(s) missing a memory entry: {', '.join(sorted(missing))}"})
        else:
            event_cb({"type": "compliance", "level": "ok",
                      "message": f"Scan compliance OK — all {len(tool_called)} analyzed symbols tracked." if tool_called else "Scan compliance OK — no symbols analyzed."})
