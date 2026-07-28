"""Find ticker-collision pairs and stale pointer files in open_trades."""
import sys; sys.path.insert(0, 'D:\\Fasset')
from pathlib import Path
from collections import defaultdict

d = Path("D:\\Fasset\\agent_fs\\memories\\open_trades")

# Group files by ticker
by_ticker = defaultdict(list)
for fp in sorted(d.glob("*.md")):
    stem = fp.stem
    # Handle sequenced names: YYYY-MM-DD--TICKER--N.md
    parts = stem.split("--")
    if len(parts) >= 2:
        date_part = parts[0]
        # Check if date_part is a valid date
        import re
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_part):
            ticker = parts[1]
        else:
            ticker = parts[0]
    else:
        ticker = stem
    by_ticker[ticker].append(fp)

print("=== Ticker-collision pairs (multiple files for same ticker) ===")
found_collision = False
for ticker, files in sorted(by_ticker.items()):
    if len(files) > 1:
        found_collision = True
        print(f"\n  {ticker}:")
        for fp in files:
            raw = fp.read_text(encoding="utf-8")
            first_line = raw.split("\n")[0].strip()
            frontmatter = raw.startswith("---")
            is_stale = first_line.startswith("MOVED to") or first_line.startswith("# Stale")
            tag = "STALE (pointer)" if is_stale else ("FRONTMATTER" if frontmatter else "NO FRONTMATTER")
            print(f"    {fp.name:45s} [{tag}] {first_line[:60]}")

if not found_collision:
    print("  (none)")

print("\n=== Files with no YAML frontmatter (potential stales) ===")
found_no_fm = False
for ticker, files in sorted(by_ticker.items()):
    for fp in files:
        raw = fp.read_text(encoding="utf-8")
        if not raw.startswith("---"):
            found_no_fm = True
            first_line = raw.split("\n")[0].strip()
            tag = "STALE" if first_line.startswith("MOVED to") else "UNKNOWN"
            print(f"  {fp.name:45s} [{tag}] {first_line[:60]}")

if not found_no_fm:
    print("  (all files have YAML frontmatter)")
