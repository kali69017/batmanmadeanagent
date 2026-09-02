"""
Deterministic signal win-rate reinforcement.

After each run, recompute per-signal win rates from closed-trade outcomes and
write the computed counts into the shared signals_log/*.md files (which the
agent reads in Phase 0) plus the SignalLog DB rows. This replaces the LLM's
manual, drift-prone counting.

Attribution rules:
- A closed trade contributes to a signal only if the trade file records it in
  `signals_used: [...]` (the agent is instructed to always write this).
- Win/loss is decided from numbers: `return_realized_pct` when present,
  otherwise `outcome`, otherwise exit vs entry price.
- A signal's counts are recomputed only once it has at least one explicit
  outcome. Until then the previously recorded (manual) counts are preserved as
  a seed, so the first run does not wipe valid history.
"""
from pathlib import Path

import config

from .memory_sync import parse_frontmatter, _parse_float, _signals_as_text

import re as _re

# Token-boundary match patterns — treat underscore as a boundary so
# "stopped_out" matches "stopped" and "stop_loss_hit" matches "loss".
# Uses (?:^|_)word(?:$|_) to avoid substring false positives like
# "stop" matching inside "nonstop" while still matching underscore-joined tokens.
_LEFT = r"(?:^|_|\s)"
_RIGHT = r"(?:$|_|\s)"

_WIN_PATTERNS = (
    r"win", r"profit", r"positive", r"gain",
    r"target", r"closed_at_t1", r"t1",
)
_LOSS_PATTERNS = (
    r"loss", r"stop", r"miss", r"stopped", r"cut",
)
_WIN_RE = _re.compile(
    "|".join(_LEFT + p + _RIGHT for p in _WIN_PATTERNS), _re.IGNORECASE
)
_LOSS_RE = _re.compile(
    "|".join(_LEFT + p + _RIGHT for p in _LOSS_PATTERNS), _re.IGNORECASE
)


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


def _outcome_win(fm: dict) -> bool | None:
    """Deterministic win/loss for a closed trade; None if undecidable."""
    pct = (
        _parse_float(fm.get("return_realized_pct"))
        or _parse_float(fm.get("return_pct"))
        or _parse_float(fm.get("pnl"))
    )
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
    """signal name -> (current notes text, file path), from signals_log dir.

    The file path is returned so callers never have to reconstruct it from the
    `signal:` field — the frontmatter value can differ from the on-disk
    filename (e.g. it may contain spaces), which used to produce a
    FileNotFoundError.
    """
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


def _scan_explicit_outcomes() -> dict[str, list[bool]]:
    """signal name -> list of win(bool) from closed trades with signals_used."""
    outcomes: dict[str, list[bool]] = {}
    for d in _closed_trade_dirs():
        for fp in d.glob("*.md"):
            raw = fp.read_text(encoding="utf-8", errors="replace")
            fm = parse_frontmatter(raw)
            if fm.get("status") == "open":
                continue
            signals = _signals_as_text(fm.get("signals_used"))
            if not signals:
                continue
            win = _outcome_win(fm)
            if win is None:
                continue
            for name in (s.strip() for s in signals.split(",")):
                if name:
                    outcomes.setdefault(name, []).append(win)
    return outcomes


def _read_recorded_counts(fp: Path) -> tuple[int, int]:
    fm = parse_frontmatter(fp.read_text(encoding="utf-8", errors="replace"))
    return (
        int(fm.get("triggered_correctly") or 0),
        int(fm.get("triggered_falsely") or 0),
    )


def _write_signal_file(fp: Path, name: str, correct: int, false: int, notes: str) -> None:
    total = correct + false
    win_rate = round(correct / total, 3) if total else None
    body = (
        "---\n"
        f"signal: {name}\n"
        f"triggered_correctly: {correct}\n"
        f"triggered_falsely: {false}\n"
    )
    if win_rate is not None:
        body += f"win_rate: {win_rate:.3f}\n"
    if notes:
        indented = "\n".join(("  " + line) for line in notes.splitlines()) or "  "
        body += f"notes: >\n{indented}\n"
    body += "---\n"
    fp.write_text(body, encoding="utf-8")


def reinforce_learning() -> dict:
    """Recompute signal win rates from closed-trade outcomes.

    Returns a summary dict with per-signal changes for the run log.
    """
    from .models import SignalLog

    signals_dir = config.SHARED_MEMORY_ROOT / "signals_log"
    if not signals_dir.is_dir():
        signals_dir.mkdir(parents=True, exist_ok=True)

    explicit = _scan_explicit_outcomes()
    known = _known_signals()
    all_names = sorted(set(known) | set(explicit))
    summary = {}

    for name in all_names:
        notes, fp = known.get(name, ("", signals_dir / f"{name}.md"))
        if fp.exists():
            recorded_correct, recorded_false = _read_recorded_counts(fp)
        else:
            # Brand-new signal (no file yet) — nothing recorded to seed from.
            recorded_correct, recorded_false = 0, 0
        wins = explicit.get(name)
        if wins is not None and wins:
            correct = sum(1 for w in wins if w)
            false = len(wins) - correct
        else:
            correct, false = recorded_correct, recorded_false
        _write_signal_file(fp, name, correct, false, notes)
        total = correct + false
        win_rate = round(correct / total, 3) if total else None
        SignalLog.objects.update_or_create(
            name=name,
            defaults={
                "triggered_correctly": correct,
                "triggered_falsely": false,
                "win_rate": win_rate,
                "notes": notes,
            },
        )
        summary[name] = {
            "correct": correct,
            "false": false,
            "win_rate": win_rate,
            "recomputed": bool(wins),
        }
    return summary
