import json
from datetime import datetime
from pathlib import Path

import config


class MemoryManager:
    def __init__(self):
        self.mem = config.AGENT_FS_ROOT / "memories"
        for sub in ["open_trades", "closed_trades", "watchlist", "signals_log"]:
            (self.mem / sub).mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # Lessons
    # -----------------------------------------------------------------------
    def get_lessons(self) -> str:
        path = self.mem / "lessons.md"
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        return ""

    # -----------------------------------------------------------------------
    # Open trades
    # -----------------------------------------------------------------------
    def get_open_trades(self) -> list[dict]:
        entries = self._read_dir("open_trades")
        best: dict[str, dict] = {}
        for e in entries:
            tkr = (e.get("ticker") or self._ticker_from_filename(e.get("file", "")) or "").upper()
            if not tkr:
                continue
            if tkr not in best or e["file"] > best[tkr]["file"]:
                best[tkr] = e
        return list(best.values())

    @staticmethod
    def _next_filename(subdir: str, ticker: str) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        d = config.AGENT_FS_ROOT / "memories" / subdir
        d.mkdir(parents=True, exist_ok=True)
        seq = 0
        while True:
            suffix = f"--{seq}" if seq else ""
            candidate = d / f"{today}--{ticker}{suffix}.md"
            if not candidate.exists():
                return candidate
            seq += 1

    def write_pick(self, ticker: str, direction: str, rationale: str,
                   signals: list | None = None, entry_price: float | None = None,
                   signal_names: list | None = None) -> str:
        fp = self._next_filename("open_trades", ticker)
        today = datetime.now().strftime("%Y-%m-%d")
        signals_str = json.dumps(signal_names or [])
        body = (
            f"---\n"
            f"date: {today}\n"
            f"ticker: {ticker}\n"
            f"direction: {direction}\n"
            f"entry_price: {entry_price if entry_price else 'null'}\n"
            f"exit_price: null\n"
            f"rationale: >\n"
            f"  {rationale}\n"
            f"signals_used: {signals_str}\n"
            f"outcome: TODO\n"
            f"return_realized_pct: null\n"
            f"lessons: >\n"
            f"  \n"
            f"---\n"
        )
        fp.write_text(body, encoding="utf-8")
        return str(fp)

    # -----------------------------------------------------------------------
    # Watchlist / rejects
    # -----------------------------------------------------------------------
    def write_watchlist_entry(self, ticker: str, direction: str = "watch",
                              rationale: str = "", condition: str = "") -> str:
        fp = self._next_filename("watchlist", ticker)
        today = datetime.now().strftime("%Y-%m-%d")
        body = (
            f"---\n"
            f"date: {today}\n"
            f"ticker: {ticker}\n"
            f"direction: {direction}\n"
            f"condition_summary: >\n"
            f"  {condition or rationale}\n"
            f"entry_price: null\n"
            f"exit_price: null\n"
            f"rationale: >\n"
            f"  {rationale}\n"
            f"signals_used: []\n"
            f"outcome: {'TODO' if direction == 'watch' else 'completed'}\n"
            f"return_realized_pct: null\n"
            f"---\n"
        )
        fp.write_text(body, encoding="utf-8")
        return str(fp)

    def write_reject(self, ticker: str, rationale: str) -> str:
        return self.write_watchlist_entry(ticker, direction="reject", rationale=rationale)

    # -----------------------------------------------------------------------
    # Signals log
    # -----------------------------------------------------------------------
    def update_signal_log(self, signal_name: str, triggered_correctly: bool):
        slug = signal_name.lower().replace(" ", "_").replace("-", "_")
        fp = self.mem / "signals_log" / f"{slug}.md"
        stats = {"signal": signal_name, "triggered_correctly": 0,
                 "triggered_falsely": 0, "win_rate": None,
                 "last_updated": datetime.now().strftime("%Y-%m-%d")}
        if fp.exists():
            text = fp.read_text(encoding="utf-8")
            for line in text.split("\n"):
                line_s = line.strip()
                if line_s.startswith("triggered_correctly:"):
                    stats["triggered_correctly"] = int(line_s.split(":", 1)[1].strip())
                elif line_s.startswith("triggered_falsely:"):
                    stats["triggered_falsely"] = int(line_s.split(":", 1)[1].strip())
        if triggered_correctly:
            stats["triggered_correctly"] += 1
        else:
            stats["triggered_falsely"] += 1
        total = stats["triggered_correctly"] + stats["triggered_falsely"]
        stats["win_rate"] = round(stats["triggered_correctly"] / total * 100, 1) if total > 0 else None
        stats["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        body = (
            f"---\n"
            f"signal: {stats['signal']}\n"
            f"triggered_correctly: {stats['triggered_correctly']}\n"
            f"triggered_falsely: {stats['triggered_falsely']}\n"
            f"win_rate: {stats['win_rate']}\n"
            f"last_updated: {stats['last_updated']}\n"
            f"---\n"
        )
        fp.write_text(body, encoding="utf-8")

    def get_signals_log(self) -> list[dict]:
        sig_dir = self.mem / "signals_log"
        results = []
        if sig_dir.is_dir():
            for fp in sorted(sig_dir.glob("*.md")):
                try:
                    text = fp.read_text(encoding="utf-8")
                    entry = {}
                    if text.startswith("---"):
                        end = text.index("---", 3)
                        for line in text[3:end].strip().split("\n"):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                entry[k.strip()] = v.strip()
                    if entry:
                        results.append(entry)
                except Exception:
                    continue
        return results

    # -----------------------------------------------------------------------
    # Closed trades
    # -----------------------------------------------------------------------
    def get_closed_trades_for_tickers(self, tickers: set[str]) -> list[dict]:
        closed_dir = self.mem / "closed_trades"
        results = []
        if not closed_dir.is_dir():
            return results
        try:
            closed_files = sorted(closed_dir.glob("*.md"), reverse=True)
        except OSError:
            return results
        for f in closed_files:
            tkr = self._ticker_from_filename(f.stem)
            if tkr and tkr.upper() in tickers:
                try:
                    text = f.read_text(encoding="utf-8")
                    results.append({"file": f.stem, "content": text})
                except Exception:
                    continue
        return results

    # -----------------------------------------------------------------------
    # Daily context builder (replaces inject_daily_context)
    # -----------------------------------------------------------------------
    def build_daily_context(self, query: str, include_watchlist: bool = False) -> str:
        blocks = []
        lessons_text = self.get_lessons()
        if lessons_text:
            blocks.append(
                "### LESSONS LEARNED (principles to inform judgment — "
                "NOT mechanical rules to pattern-match against)\n"
                f"{lessons_text}"
            )
        open_trades = self.get_open_trades()
        if open_trades:
            entries = "\n\n".join(
                f"### Open trade — {e['file'].replace('.md','')}\n"
                f"{{'ticker': '{e.get('symbol','')}', "
                f"'direction': '{e.get('direction','')}', "
                f"'entry_price': '{e.get('entry_price','')}', "
                f"'rationale': '{e.get('rationale','')}'}}"
                for e in open_trades
            )
            blocks.append(
                "### OPEN TRADES REQUIRING REVIEW\n"
                "For each open trade below: pull fresh full technicals "
                "(force_refresh=True), then use your own current judgment — "
                "informed by the lessons above — to decide whether to hold, "
                "tighten the stop, take partial profit, or close.\n\n"
                + entries
            )
        if include_watchlist:
            watch_dir = self.mem / "watchlist"
            if watch_dir.is_dir():
                watch_files = sorted(watch_dir.glob("*.md"))
                if watch_files:
                    entries = "\n\n".join(
                        f"### Watchlist item — {f.stem}\n{f.read_text(encoding='utf-8')}"
                        for f in watch_files
                    )
                    blocks.append(
                        "### WATCHLIST — re-evaluate each with fresh full "
                        "technicals (force_refresh=True). The condition_summary "
                        "is last session's judgment, not today's answer — form "
                        "your own current view.\n\n" + entries
                    )
        signals_log = self.get_signals_log()
        if signals_log:
            sig_entries = "\n".join(
                f"  - {s.get('signal','?')}: "
                f"{s.get('win_rate','?')}% win rate "
                f"({s.get('triggered_correctly','0')}/{s.get('triggered_falsely','0')})"
                for s in signals_log
            )
            blocks.append(
                "### SIGNAL PERFORMANCE (win rates from history)\n"
                f"{sig_entries}"
            )
        if not blocks:
            return query
        preamble = "\n\n".join(blocks)
        return f"{preamble}\n\n---\n\nNow answer:\n\n{query}"

    @staticmethod
    def _read_dir(subdir: str) -> list[dict]:
        d = config.AGENT_FS_ROOT / "memories" / subdir
        results = []
        if d.is_dir():
            for fp in sorted(d.glob("*.md")):
                try:
                    text = fp.read_text(encoding="utf-8")
                    # Skip stale pointer files
                    if text.strip().startswith("MOVED to"):
                        continue
                    entry = {"file": fp.name}
                    if text.startswith("---"):
                        end = text.index("---", 3)
                        for line in text[3:end].strip().split("\n"):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                entry[k.strip()] = v.strip().strip("'\"")
                    results.append(entry)
                except Exception:
                    continue
        return results

    @staticmethod
    def _ticker_from_filename(filename: str) -> str | None:
        stem = filename.rsplit(".", 1)[0] if "." in filename else filename
        parts = stem.split("--", 1)
        if len(parts) == 2:
            return parts[1]
        return stem

