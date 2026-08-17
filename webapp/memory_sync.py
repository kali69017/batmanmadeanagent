"""
Memory <-> DB sync for the webapp.

The agent owns the filesystem memory tree; these helpers project it into the
Django DB (Trade/Lesson/SignalLog) so the UI and learning stats are queryable.
`load_positions` is DB-backed and mirrors the response shape the frontend
already expects.
"""
from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model

import config

from .models import Lesson, SignalLog, Trade

TERMINAL_STATUSES = {
    "closed",
    "missed",
    "pending_only",
    "stopped_out",
    "cancelled",
    "moved",
    "pending_converted_to_filled",
}

# Maps frontmatter key -> Trade model field.
_FIELD_MAP = {
    "ticker": "ticker",
    "symbol": "ticker",
    "date": "date",
    "direction": "direction",
    "status": "status",
    "conviction": "conviction",
    "entry_price": "entry_price",
    "entry_zone": "entry_zone",
    "stop_loss": "stop_loss",
    "stop": "stop_loss",
    "exit_price": "exit_price",
    "targets": "targets",
    "outcome": "outcome",
    "note": "note",
    "rationale": "rationale",
    "thesis": "rationale",
    "rejection_reason": "rationale",
    "condition_summary": "note",
    "conditions_to_watch": "note",
    "entry_conditions": "note",
    "horizon": "horizon",
    "signals_used": "signals_used",
    "risk_reward": "risk_reward",
}


# ---------------------------------------------------------------------------
# Frontmatter parsing (shared with the runner)
# ---------------------------------------------------------------------------
def parse_frontmatter(text: str) -> dict:
    """Defensive YAML-ish frontmatter parser.

    Handles: missing frontmatter, an opening '---' with no closing delimiter
    (legacy files), scalar values, folded (>), literal block (|), and list (-)
    values that span indented lines.
    """
    out: dict = {}
    lstrip = text.lstrip()
    if not lstrip.startswith("---"):
        return out
    lines = lstrip.split("\n")
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].lstrip().startswith("---"):
            end_idx = i
            break
    block = lines[1:end_idx] if end_idx is not None else lines[1:]

    i = 0
    while i < len(block):
        line = block[i]
        if not line.strip() or ":" not in line:
            i += 1
            continue
        k, v = line.split(":", 1)
        k = k.strip().lower().replace(" ", "_")
        v = v.strip()
        if v in ("", ">"):
            # Folded scalar or bare indented block — join continuation lines.
            parts = []
            j = i + 1
            while j < len(block) and block[j][:1] in (" ", "\t"):
                stripped = block[j].strip()
                if stripped.startswith("- "):
                    parts.append(stripped[2:].strip())
                else:
                    parts.append(stripped)
                j += 1
            v = " ".join(parts) if parts else ""
            i = j
        elif v == "|":
            # Literal block scalar — preserve as a newline-separated string.
            parts = []
            j = i + 1
            while j < len(block) and block[j][:1] in (" ", "\t"):
                parts.append(block[j].strip())
                j += 1
            v = "\n".join(parts) if parts else ""
            i = j
        else:
            v = v.strip("'\"")
            i += 1
        if v.lower() in ("null", "none"):
            v = None
        elif v.lower() == "true":
            v = True
        elif v.lower() == "false":
            v = False
        out[k] = v
    return out


def ticker_from_stem(stem: str) -> str:
    parts = stem.split("--")
    return (parts[-1] if len(parts) > 1 else parts[0]).upper()


# ---------------------------------------------------------------------------
# Trade sync
# ---------------------------------------------------------------------------
def _parse_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").replace("%", "").replace("~", "").strip())
    except (TypeError, ValueError):
        return None


def _trade_from_file(fp: Path, kind: str, text: str | None = None) -> dict | None:
    raw = text if text is not None else fp.read_text(encoding="utf-8", errors="replace")
    if raw.lstrip().startswith("MOVED to"):
        return None
    fm = parse_frontmatter(raw)
    if kind in ("open", "pending") and fm.get("status") in TERMINAL_STATUSES:
        return None
    ticker = (fm.get("ticker") or fm.get("symbol") or ticker_from_stem(fp.stem)).upper()
    entry = {
        "file_name": fp.name,
        "ticker": ticker,
        "date": str(fm.get("date") or fp.stem.split("--")[0]),
        "kind": kind,
    }
    for src, dst in _FIELD_MAP.items():
        value = fm.get(src)
        if not value:
            continue
        if dst == "ticker" and not value:
            continue
        entry[dst] = value
    # Default direction from type/kind if frontmatter doesn't specify
    if not entry.get("direction"):
        ftype = fm.get("type") or ""
        if ftype == "filled" or kind == "open":
            entry["direction"] = "long"
        elif ftype == "pending" or kind == "pending":
            entry["direction"] = "pending"
        elif fm.get("status") in ("reject", "rejected_for_now") or kind == "watchlist":
            entry["direction"] = "reject"
    entry["signals_used"] = _signals_as_text(fm.get("signals_used"))
    entry["return_realized_pct"] = (
        _parse_float(fm.get("return_realized_pct"))
        or _parse_float(fm.get("return_pct"))
        or _parse_float(fm.get("pnl"))
    )
    for k in ("entry_price", "stop_loss", "exit_price", "targets"):
        entry[k] = "" if entry.get(k) is None else str(entry[k])
    entry["raw"] = raw
    return entry


def _signals_as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("["):
            return ", ".join(
                x.strip().strip("'\"").lower().replace(" ", "_")
                for x in s.strip("[]").split(",")
                if x.strip()
            )
        return s
    if isinstance(value, list):
        return ", ".join(str(x).strip().lower().replace(" ", "_") for x in value)
    return str(value)


def sync_user_trades(username: str) -> int:
    """Upsert Trade rows from a user's memory root. Returns row count."""
    User = get_user_model()
    user = User.objects.filter(username=username).first()
    if not user:
        return 0
    root = config.user_memory_root(username)
    if not root.is_dir():
        return 0

    count = 0
    for sub, kind in (
        ("open_trades", Trade.KIND_OPEN),
        ("pending_entries", Trade.KIND_PENDING),
        ("watchlist", Trade.KIND_WATCHLIST),
        ("closed_trades", Trade.KIND_CLOSED),
    ):
        subdir = root / sub
        if not subdir.is_dir():
            continue
        seen: set[str] = set()
        for fp in sorted(subdir.glob("*.md")):
            try:
                entry = _trade_from_file(fp, kind)
            except OSError:
                continue
            if entry is None:
                continue
            seen.add(fp.name)
            entry["owner"] = user
            obj, _created = Trade.objects.update_or_create(
                owner=user, kind=kind, file_name=fp.name, defaults=entry
            )
            count += 1
        Trade.objects.filter(owner=user, kind=kind).exclude(file_name__in=seen).delete()
    return count


def sync_shared_lessons() -> int:
    """Sync lessons.md into the shared Lesson row (single row)."""
    fp = config.SHARED_MEMORY_ROOT / "lessons.md"
    if not fp.exists():
        return 0
    content = fp.read_text(encoding="utf-8", errors="replace")
    obj, _ = Lesson.objects.update_or_create(pk=1, defaults={"content": content})
    return 1


def sync_shared_signals() -> int:
    """Sync signals_log/*.md into shared SignalLog rows."""
    signals_dir = config.SHARED_MEMORY_ROOT / "signals_log"
    if not signals_dir.is_dir():
        return 0
    count = 0
    seen: set[str] = set()
    for fp in sorted(signals_dir.glob("*.md")):
        raw = fp.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(raw)
        name = (fm.get("signal") or fp.stem).strip()
        if not name:
            continue
        seen.add(name)
        correct = _parse_int(fm.get("triggered_correctly"))
        false = _parse_int(fm.get("triggered_falsely"))
        total = (correct or 0) + (false or 0)
        win_rate = round(correct / total, 3) if total else None
        SignalLog.objects.update_or_create(
            name=name,
            defaults={
                "triggered_correctly": correct or 0,
                "triggered_falsely": false or 0,
                "win_rate": win_rate,
                "notes": fm.get("notes") or "",
            },
        )
        count += 1
    SignalLog.objects.exclude(name__in=seen).delete()
    return count


def _parse_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def sync_all(username: str) -> None:
    """Full sync for a user (trades + shared lessons + shared signals)."""
    sync_user_trades(username)
    sync_shared_lessons()
    sync_shared_signals()


# ---------------------------------------------------------------------------
# DB-backed read for the UI
# ---------------------------------------------------------------------------
def _entry_from_trade(t: "Trade") -> dict:
    return {
        "file": t.file_name,
        "ticker": t.ticker,
        "date": t.date,
        "type": t.kind,
        "direction": t.direction,
        "status": t.status,
        "conviction": t.conviction,
        "entry_price": t.entry_price or None,
        "entry_zone": t.entry_zone or None,
        "stop_loss": t.stop_loss or None,
        "exit_price": t.exit_price or None,
        "targets": t.targets or None,
        "horizon": t.horizon or None,
        "risk_reward": t.risk_reward or None,
        "outcome": t.outcome,
        "note": t.note,
        "rationale": t.rationale,
        "signals_used": t.signals_used or "",
        "raw": (t.raw or "")[:4000],
    }


# Cache of latest prices loaded once per request
_live_price_cache: dict[str, float | None] = {}
_live_price_loaded = False


def _load_live_prices() -> dict[str, float | None]:
    """Load latest closing prices from cached yfinance data."""
    global _live_price_cache, _live_price_loaded
    if _live_price_loaded:
        return _live_price_cache

    import json as _json
    cache_dir = config.CACHE_DIR
    if not cache_dir.is_dir():
        _live_price_loaded = True
        return _live_price_cache

    for fp in sorted(cache_dir.glob("*.json")):
        ticker = fp.stem.upper()
        if ticker in _live_price_cache:
            continue
        try:
            raw = fp.read_text(encoding="utf-8", errors="replace")
            data = _json.loads(raw)
            fi = data.get("fast_info")
            if isinstance(fi, dict):
                lp = fi.get("lastPrice")
                if lp is not None:
                    _live_price_cache[ticker] = float(lp)
        except Exception:
            continue

    # Also read from combined_history.csv for any missing tickers
    csv_path = config.CACHE_DIR / "combined_history.csv"
    if csv_path.exists():
        try:
            import pandas as pd
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            if "Close" in df.columns:
                latest = df["Close"].iloc[-1] if isinstance(df["Close"].iloc[-1], float) else df["Close"].iloc[-1]
                # Per-ticker from columns or single symbol
                for col in df.columns:
                    upper = col.upper()
                    if upper not in _live_price_cache and upper in config.WATCHLIST:
                        try:
                            val = df[col].dropna().iloc[-1]
                            if val and not pd.isna(val):
                                _live_price_cache[upper] = float(val)
                        except Exception:
                            continue
        except Exception:
            pass

    _live_price_loaded = True
    return _live_price_cache


def _enrich_with_live_price(entry: dict) -> dict:
    """Add live_price and pnl_pct to a position entry."""
    prices = _load_live_prices()
    ticker = (entry.get("ticker") or "").upper()
    live = prices.get(ticker)
    entry["live_price"] = live
    entry_p = _parse_float(entry.get("entry_price"))
    if entry_p and entry_p > 0 and live:
        entry["pnl_pct"] = round((live - entry_p) / entry_p * 100, 2)
        entry["pnl_direction"] = "up" if entry["pnl_pct"] >= 0 else "down"
    else:
        entry["pnl_pct"] = None
        entry["pnl_direction"] = None
    return entry


def load_positions(username: str) -> dict:
    """Latest per-ticker positions for a user, grouped by memory kind."""
    User = get_user_model()
    user = User.objects.filter(username=username).first()
    if not user:
        return {"open": [], "pending": [], "watchlist": [], "closed": []}

    def _list(kind: str) -> list[dict]:
        qs = (
            Trade.objects.filter(owner=user, kind=kind)
            .order_by("-date", "-updated_at")
            .values(
                "file_name", "ticker", "date", "kind", "direction", "status",
                "conviction", "entry_price", "entry_zone", "stop_loss", "exit_price",
                "targets", "horizon", "risk_reward", "outcome", "note", "rationale",
                "signals_used", "raw",
            )
        )
        return [_enrich_with_live_price({
            "file": r["file_name"],
            "ticker": r["ticker"],
            "date": r["date"],
            "type": r["kind"],
            "direction": r["direction"],
            "status": r["status"],
            "conviction": r["conviction"],
            "entry_price": r["entry_price"] or None,
            "entry_zone": r["entry_zone"] or None,
            "stop_loss": r["stop_loss"] or None,
            "exit_price": r["exit_price"] or None,
            "targets": r["targets"] or None,
            "horizon": r["horizon"] or None,
            "risk_reward": r["risk_reward"] or None,
            "outcome": r["outcome"],
            "note": r["note"],
            "rationale": r["rationale"],
            "signals_used": r["signals_used"] or "",
            "raw": (r["raw"] or "")[:4000],
        }) for r in qs]

    watchlist = _list(Trade.KIND_WATCHLIST)
    latest: dict[str, dict] = {}
    for e in watchlist:
        key = e["ticker"]
        if key not in latest or e["date"] > latest[key]["date"]:
            latest[key] = e
    return {
        "open": _list(Trade.KIND_OPEN),
        "pending": _list(Trade.KIND_PENDING),
        "watchlist": sorted(latest.values(), key=lambda e: e["date"], reverse=True),
        "closed": _list(Trade.KIND_CLOSED),
    }


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def memory_dirs() -> dict[str, Path]:
    """Per-subdir paths under the active memory root."""
    root = config.active_memories_root()
    return {
        "open": root / "open_trades",
        "pending": root / "pending_entries",
        "watch": root / "watchlist",
        "closed": root / "closed_trades",
    }
