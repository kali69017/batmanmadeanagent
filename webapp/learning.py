"""
Deterministic, evidence-based signal reinforcement.

After each run, recompute per-signal statistics from closed-trade outcomes and
write them into the shared signals_log/*.md files (which the agent reads in
Phase 0) plus the SignalLog DB rows. This replaces the LLM's manual,
drift-prone counting.

Attribution rules (unchanged):
- A closed trade contributes to a signal only if the trade file records it in
  `signals_used: [...]`.
- Win/loss is decided from numbers: `return_realized_pct` when present,
  otherwise `outcome`, otherwise exit vs entry price.
- A stopped-out trade counts as a loss for every signal in signals_used.

New (learning upgrade): we keep the *realized return magnitude* per trade, not
just a boolean, and derive expectancy + verdict via `signal_stats`. Scoring a
signal on win rate alone was proven misleading by the backtester (a 56%-win
fast exit returned less than half the wealth of a 46%-win signal). The verdict
ladder (insufficient / confirmed / promising / unproven / failing) is what the
agent prompt now acts on.
"""
from pathlib import Path

import config

from .memory_sync import parse_frontmatter, _parse_float, _signals_as_text
from .signal_stats import compute_signal_stats, MIN_SIGNAL_TRADES

import re as _re

# Token-boundary match patterns — treat underscore as a boundary so
# "stopped_out" matches "stopped" and "stop_loss_hit" matches "loss".
_LEFT = r"(?:^|_|\s)"
_RIGHT = r"(?:$|_|\s)"

_WIN_PATTERNS = (
    r"win", r"profit", r"positive", r"gain",
    r"target", r"closed_at_t1", r"t1",
)
_LOSS_PATTERNS = (
    r"loss", r"stop", r"miss", r"stopped", r"cut",
)
_WIN_RE = _re.compile("|".join(_LEFT + p + _RIGHT for p in _WIN_PATTERNS), _re.IGNORECASE)
_LOSS_RE = _re.compile("|".join(_LEFT + p + _RIGHT for p in _LOSS_PATTERNS), _re.IGNORECASE)


def _closed_trade_dirs() -> list[Path]:
    dirs: list[Path] = []
    if config.USERS_ROOT.is_dir():
        for user_root in sorted(config.USERS_ROOT.iterdir()):
            d = user_root / "memories" / "closed_trades"
            if d.is_dir():
                dirs.append(d)
    legacy = config.SHARED_MEMORY_ROOT / "closed_trades"
    if legacy.is_dir() and legacy not in dirs:
        dirs.append(legacy)
    return dirs


def _trade_return(fm: dict) -> float | None:
    """Realized return percent for a closed trade, or None if undecidable."""
    pct = _parse_float(fm.get("return_realized_pct"))
    if pct is None:
        pct = _parse_float(fm.get("return_pct"))
    if pct is None:
        pct = _parse_float(fm.get("pnl"))
    if pct is not None:
        return pct
    outcome = (fm.get("outcome") or "").lower()
    if outcome:
        if _WIN_RE.search(outcome):
            # No numeric return but outcome says a win; we can't know magnitude,
            # so we can't include it in expectancy. Return None (counts missing).
            return None
        if _LOSS_RE.search(outcome):
            return None
    entry = _parse_float(fm.get("entry_price"))
    exit_p = _parse_float(fm.get("exit_price"))
    if entry is not None and exit_p is not None and entry != 0:
        return (exit_p / entry - 1.0) * 100.0
    return None


def _outcome_win(fm: dict) -> bool | None:
    """Legacy boolean win/loss (kept for back-compat counts)."""
    pct = _trade_return(fm)
    if pct is not None:
        return pct >= 0
    outcome = (fm.get("outcome") or "").lower()
    if outcome:
        if _WIN_RE.search(outcome):
            return True
        if _LOSS_RE.search(outcome):
            return False
    entry = _parse_float(fm.get("entry_price"))
    exit_p = _parse_float(fm.get("exit_price"))
    if entry is not None and exit_p is not None:
        return exit_p >= entry
    return None


def _known_signals() -> dict[str, tuple[str, Path]]:
    """signal name -> (current notes text, file path)."""
    out: dict[str, tuple[str, Path]] = {}
    signals_dir = config.SHARED_MEMORY_ROOT / "signals_log"
    if not signals_dir.is_dir():
        return out
    for fp in sorted(signals_dir.glob("*.md")):
        raw = fp.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(raw)
        name = (fm.get("signal") or fp.stem).strip()
        if name:
            out[name] = (fm.get("notes") or "", fp)
    return out


def _scan_explicit_returns() -> dict[str, list[float]]:
    """signal name -> list of realized returns from closed trades with signals_used.

    A trade with no computable numeric return is still recorded as None in the
    list so we can count `n_missing_return`; compute_signal_stats handles None.
    """
    returns: dict[str, list[float | None]] = {}
    for d in _closed_trade_dirs():
        for fp in d.glob("*.md"):
            raw = fp.read_text(encoding="utf-8", errors="replace")
            fm = parse_frontmatter(raw)
            if fm.get("status") == "open":
                continue
            signals = _signals_as_text(fm.get("signals_used"))
            if not signals:
                continue
            ret = _trade_return(fm)
            for name in (s.strip() for s in signals.split(",")):
                if name:
                    returns.setdefault(name, []).append(ret)
    return returns


def _read_recorded_counts(fp: Path) -> tuple[int, int]:
    fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="replace"))
    return (
        int(fm.get("triggered_correctly") or 0),
        int(fm.get("triggered_falsely") or 0),
    )


def _fmt(v):
    return "" if v is None else f"{v:.4f}"


def _write_signal_file(fp: Path, name: str, correct: int, false: int,
                       notes: str, stats=None) -> None:
    """Write the signals_log/<name>.md rollup.

    `stats` is a SignalStats from compute_signal_stats; when provided it drives
    the expectancy fields and verdict. Back-compat counts (correct/false/win_rate)
    are always written so existing readers keep working.
    """
    total = correct + false
    win_rate = round(correct / total, 3) if total else None
    body = (
        "---\n"
        f"signal: {name}\n"
        f"n_trades: {stats.n if stats else 0}\n"
        f"triggered_correctly: {correct}\n"
        f"triggered_falsely: {false}\n"
    )
    if win_rate is not None:
        body += f"win_rate: {win_rate:.3f}\n"
    if stats is not None:
        body += f"n_missing_return: {stats.n_missing_return}\n"
        for k in ("mean_return_pct", "median_return_pct", "total_return_pct",
                  "best_return_pct", "worst_return_pct"):
            body += f"{k}: {_fmt(getattr(stats, k))}\n"
        body += f"verdict: {stats.verdict}\n"
        if stats.evidence_note:
            indented = "\n".join(("  " + line) for line in stats.evidence_note.splitlines())
            body += f"evidence_note: >\n{indented}\n"
    if notes:
        indented = "\n".join(("  " + line) for line in notes.splitlines()) or "  "
        body += f"notes: >\n{indented}\n"
    body += "---\n"
    fp.write_text(body, encoding="utf-8")


def reinforce_learning() -> dict:
    """Recompute per-signal evidence from closed-trade outcomes.

    Returns a summary dict with per-signal stats for the run log.
    """
    from .models import SignalLog

    signals_dir = config.SHARED_MEMORY_ROOT / "signals_log"
    if not signals_dir.is_dir():
        signals_dir.mkdir(parents=True, exist_ok=True)

    explicit = _scan_explicit_returns()
    known = _known_signals()
    all_names = sorted(set(known) | set(explicit))
    summary = {}

    for name in all_names:
        notes, fp = known.get(name, ("", signals_dir / f"{name}.md"))
        returns = explicit.get(name, [])
        # Back-compat boolean counts, used both as seeds and informational.
        if returns:
            wins = sum(1 for r in returns if r is not None and r >= 0)
            losses = sum(1 for r in returns if r is not None and r < 0)
            correct, false = wins, losses
        else:
            if fp.exists():
                recorded_correct, recorded_false = _read_recorded_counts(fp)
            else:
                recorded_correct, recorded_false = 0, 0
            correct, false = recorded_correct, recorded_false

        # Compute expectancy + verdict from realized returns (None tolerated).
        stats = compute_signal_stats(returns, note_hint=notes)
        _write_signal_file(fp, name, correct, false, notes, stats=stats)

        total = correct + false
        win_rate = round(correct / total, 3) if total else None
        SignalLog.objects.update_or_create(
            name=name,
            defaults={
                "triggered_correctly": correct,
                "triggered_falsely": false,
                "win_rate": win_rate,
                "notes": notes,
                "n_trades": stats.n,
                "n_missing_return": stats.n_missing_return,
                "mean_return_pct": stats.mean_return_pct,
                "median_return_pct": stats.median_return_pct,
                "total_return_pct": stats.total_return_pct,
                "best_return_pct": stats.best_return_pct,
                "worst_return_pct": stats.worst_return_pct,
                "verdict": stats.verdict,
                "evidence_note": stats.evidence_note,
            },
        )
        summary[name] = {
            "correct": correct,
            "false": false,
            "win_rate": win_rate,
            "n_trades": stats.n,
            "mean_return_pct": stats.mean_return_pct,
            "verdict": stats.verdict,
            "evidence_note": stats.evidence_note,
            "recomputed": bool(returns),
        }
    return summary
