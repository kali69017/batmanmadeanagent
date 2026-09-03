"""Pure, deterministic signal statistics + verdicts for the learning system.

This module has NO Django or filesystem coupling: it takes a list of realized
per-trade returns (percent) and returns statistics + a verdict. Both
`webapp/learning.py` and `webapp/memory_sync.sync_shared_signals` call
`compute_signal_stats` so live and sync scoring can never drift apart. The
backtester's `backtest/validate.py` uses the same logic so backtest and live
agree on what "confirmed" means.

Why this exists: scoring signals on win rate alone is misleading (proven by
the backtester -- a 56% win-rate fast-exit returned less than half the wealth
of a 46% win-rate signal). What matters for deciding whether to trade a signal
is EXPECTANCY (mean return per trade), the SAMPLE SIZE behind it, and whether
it still works on recent trades.

Verdict ladder (derived, deterministic):
    insufficient : n < MIN_SIGNAL_TRADES          -> "treat as unproven"
    confirmed    : n>=MIN and mean>0 and win>=CONFIRM_WIN_RATE
    promising    : n>=MIN and mean>0 and win<CONFIRM_WIN_RATE
    unproven     : n>=MIN and |mean|<=EXPECTANCY_EPS
    failing      : n>=MIN and mean<0

Recency: if enough recent closed trades show materially worse expectancy than
the older ones, downgrade one step (confirmed->promising->unproven). Recency
only ever DOWNGRADES, never upgrades, because a few live trades are noisy.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean, median

# ---- Tunable thresholds (live-tunable defaults) ---------------------------
MIN_SIGNAL_TRADES = 10          # below this a signal is "insufficient"
CONFIRM_WIN_RATE = 0.50         # win rate needed (with +expectancy) for "confirmed"
EXPECTANCY_EPS = 0.05           # |mean return %| below this treated as zero
RECENT_MIN = 5                  # need this many recent trades to flag recency
RECENT_FRAC = 0.20              # newest fraction of trades treated as "recent"
RECENT_DEGRADE_RATIO = 0.5      # recent mean < older mean * this => deterioration


@dataclass(frozen=True)
class SignalStats:
    n: int
    win_rate: float | None
    mean_return_pct: float | None
    median_return_pct: float | None
    total_return_pct: float | None
    best_return_pct: float | None
    worst_return_pct: float | None
    n_with_return: int
    n_missing_return: int
    verdict: str
    evidence_note: str


def compute_signal_stats(returns: list[float], *, note_hint: str = "") -> SignalStats:
    """Compute stats + verdict from a list of realized per-trade returns (%)."""
    # Drop None/non-numeric; count how many were unusable.
    cleaned: list[float] = []
    missing = 0
    for r in returns:
        if r is None or (isinstance(r, float) and math.isnan(r)):
            missing += 1
            continue
        try:
            cleaned.append(float(r))
        except (TypeError, ValueError):
            missing += 1
    n = len(cleaned)
    if n == 0:
        return SignalStats(
            n=0, win_rate=None, mean_return_pct=None, median_return_pct=None,
            total_return_pct=None, best_return_pct=None, worst_return_pct=None,
            n_with_return=0, n_missing_return=missing,
            verdict="insufficient",
            evidence_note=note_hint or "No closed trades with a computable return yet.",
        )

    wins = sum(1 for r in cleaned if r >= 0)
    win_rate = wins / n
    mean_r = mean(cleaned)
    median_r = median(cleaned)
    total_r = sum(cleaned)
    best_r = max(cleaned)
    worst_r = min(cleaned)

    verdict = _verdict(n, mean_r, win_rate)
    # Recency downgrade (only downgrades).
    older, recent = _chrono_split(cleaned, RECENT_FRAC)
    if len(recent) >= RECENT_MIN and len(older) > 0:
        older_mean = mean(older)
        recent_mean = mean(recent)
        # Deterioration: recent expectancy is clearly worse (and negative or
        # much lower) than the established older mean.
        if older_mean > EXPECTANCY_EPS and recent_mean < older_mean * RECENT_DEGRADE_RATIO:
            verdict = _downgrade(verdict)
            note_hint = (note_hint or "") + (
                " Recent returns deteriorated vs older trades -- re-evaluate before sizing."
            )

    evidence_note = _build_note(n, win_rate, mean_r, median_r, verdict, note_hint)
    return SignalStats(
        n=n, win_rate=round(win_rate, 4), mean_return_pct=round(mean_r, 4),
        median_return_pct=round(median_r, 4), total_return_pct=round(total_r, 4),
        best_return_pct=round(best_r, 4), worst_return_pct=round(worst_r, 4),
        n_with_return=n, n_missing_return=missing,
        verdict=verdict, evidence_note=evidence_note,
    )


def _verdict(n: int, mean_r: float, win_rate: float) -> str:
    if n < MIN_SIGNAL_TRADES:
        return "insufficient"
    if mean_r > EXPECTANCY_EPS:
        if win_rate >= CONFIRM_WIN_RATE:
            return "confirmed"
        return "promising"          # positive expectancy, low hit rate
    if mean_r < -EXPECTANCY_EPS:
        return "failing"
    return "unproven"               # expectancy ~ 0


_VERDICT_ORDER = {"confirmed": 0, "promising": 1, "unproven": 2, "failing": 3,
                  "insufficient": 4}


def _downgrade(verdict: str) -> str:
    order = ["confirmed", "promising", "unproven", "failing"]
    if verdict in order:
        idx = order.index(verdict)
        return order[min(idx + 1, len(order) - 1)]
    return verdict


def _chrono_split(values: list[float], frac: float):
    """Oldest (1-frac) vs newest (frac), preserving order."""
    if len(values) < 2:
        return values, []
    cut = max(1, int(len(values) * (1 - frac)))
    return values[:cut], values[cut:]


def _build_note(n, win_rate, mean_r, median_r, verdict, hint) -> str:
    if n == 0:
        return hint or "insufficient data"
    parts = [
        f"{n} closed trade(s); mean {mean_r:+.2f}%/trade, win {win_rate*100:.0f}%",
    ]
    if median_r is not None:
        parts.append(f"median {median_r:+.2f}%")
    label = {
        "confirmed": "positive edge confirmed; size normally",
        "promising": "positive expectancy but low hit rate; let winners run, do not over-trade",
        "unproven": "no confirmed edge yet",
        "failing": "negative expectancy; do not use until corrected",
        "insufficient": "insufficient sample -- treat as unproven, do not weight",
    }.get(verdict, verdict)
    note = "; ".join(parts) + f". Verdict: {label}."
    if hint:
        note = f"{note} {hint}".strip()
    return note
