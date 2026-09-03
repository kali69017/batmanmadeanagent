"""Generate clean daily trading signals — deterministic, no LLM call.

After the main scan, the positions are already written to memory files with
entry zones, targets, stops, and rationale. This module extracts those fields
deterministically and produces a clean signal list — no separate LLM call, so
it's instant and never hangs.

Each signal has: ticker, direction, entry range, TP1, TP2, stop loss, reason.
"""
import json
import logging
import re
from datetime import date

from django.utils import timezone

import config

logger = logging.getLogger(__name__)


def _parse_targets(targets) -> tuple[float | None, float | None]:
    """Parse a targets value (string/list) into (tp1, tp2)."""
    if targets is None:
        return None, None
    # Could be a JSON-ish list, a "1, 2" string, or a list already
    items = []
    if isinstance(targets, (list, tuple)):
        items = targets
    else:
        s = str(targets)
        # Strip brackets
        s = s.strip("[]")
        # Split on commas OR whitespace (targets may be "1.0, 2.0" or "1.0 2.0")
        parts = re.split(r"[,\s]+", s.strip())
        items = [p for p in parts if p]
    nums = []
    for it in items:
        m = re.search(r"[-+]?\d*\.?\d+", str(it))
        if m:
            nums.append(float(m.group()))
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], None
    return None, None


def _parse_zone(entry_zone, entry_price) -> tuple[float | None, float | None]:
    """Parse an entry zone string (e.g. "41.50 - 43.00") into (low, high)."""
    if entry_zone:
        nums = re.findall(r"[-+]?\d*\.?\d+", str(entry_zone))
        if len(nums) >= 2:
            return float(nums[0]), float(nums[1])
        if len(nums) == 1:
            v = float(nums[0])
            return v, v
    if entry_price:
        v = float(entry_price)
        return v, v
    return None, None


def _parse_float(v) -> float | None:
    if v in (None, "", "null", "None"):
        return None
    try:
        return float(str(v).replace(",", "").replace("%", "").replace("~", "").strip())
    except (TypeError, ValueError):
        return None


def _clean_reason(text) -> str:
    """Extract a clean, readable reason from thesis/rationale/note."""
    if not text:
        return ""
    s = str(text)
    # Strip YAML folded markers and bullet prefixes
    lines = []
    for line in s.split("\n"):
        line = line.strip()
        if line.startswith(">"):
            line = line[1:].strip()
        line = line.lstrip("- ").strip()
        if line and not line.startswith("---") and not line.startswith("symbol:"):
            lines.append(line)
    # Take the first sentence or ~180 chars
    joined = " ".join(lines).strip()
    if not joined:
        return ""
    # Truncate at first sentence boundary after 60 chars
    if len(joined) > 180:
        cut = joined[:180]
        # Try to cut at a sentence boundary
        for marker in (". ", "! ", "? "):
            idx = cut.rfind(marker)
            if idx > 60:
                cut = cut[:idx + 1]
                break
        joined = cut + "…"
    return joined


def generate_daily_signals(username: str) -> list[dict]:
    """Extract today's signals from memory files (open + pending positions).

    Returns a list of signal dicts. Deterministic and instant — no LLM call.
    """
    from .memory_sync import load_positions
    from .models import DailySignal, ScanRun
    from django.contrib.auth import get_user_model

    positions = load_positions(username)
    open_positions = positions.get("open", [])
    pending = positions.get("pending", [])

    today = timezone.localdate()
    User = get_user_model()
    user = User.objects.filter(username=username).first()
    if not user:
        return []

    # Clear today's previous signals
    DailySignal.objects.filter(owner=user, scan_date=today).delete()

    signals = []
    emitted: set[str] = set()

    def _emit(ticker, direction, entry_low, entry_high, tp1, tp2, stop, reason):
        if ticker not in config.WATCHLIST:
            return
        # One signal per ticker per day. load_positions can return the same
        # ticker more than once (multiple open files, or a ticker in both open
        # and pending); the (owner, scan_date, ticker) UNIQUE constraint would
        # reject the second insert. Keep the first — open/hold wins over
        # pending/buy.
        if ticker in emitted:
            return
        emitted.add(ticker)
        obj = DailySignal.objects.create(
            owner=user,
            scan_date=today,
            ticker=ticker,
            direction=direction,
            entry_low=entry_low,
            entry_high=entry_high,
            tp1=tp1,
            tp2=tp2,
            stop_loss=stop,
            reason=reason,
        )
        signals.append({
            "ticker": obj.ticker,
            "direction": obj.direction,
            "entry_low": obj.entry_low,
            "entry_high": obj.entry_high,
            "tp1": obj.tp1,
            "tp2": obj.tp2,
            "stop_loss": obj.stop_loss,
            "reason": obj.reason,
        })

    # Open positions → "hold" signals
    for p in open_positions:
        ticker = (p.get("ticker") or "").upper()
        entry_low, entry_high = _parse_zone(p.get("entry_zone"), p.get("entry_price"))
        tp1, tp2 = _parse_targets(p.get("targets"))
        stop = _parse_float(p.get("stop_loss"))
        reason = _clean_reason(p.get("rationale") or p.get("note"))
        _emit(ticker, "hold", entry_low, entry_high, tp1, tp2, stop, reason)

    # Pending entries → "buy" signals
    for p in pending:
        ticker = (p.get("ticker") or "").upper()
        entry_low, entry_high = _parse_zone(p.get("entry_zone"), p.get("entry_price"))
        tp1, tp2 = _parse_targets(p.get("targets"))
        stop = _parse_float(p.get("stop_loss"))
        reason = _clean_reason(p.get("rationale") or p.get("note"))
        _emit(ticker, "buy", entry_low, entry_high, tp1, tp2, stop, reason)

    ScanRun.objects.create(
        owner=user,
        scan_date=today,
        mode="full",
        signal_count=len(signals),
    )

    return signals
