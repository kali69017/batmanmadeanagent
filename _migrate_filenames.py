"""Fix B migration: Rename non-dated open_trade/watchlist files to YYYY-MM-DD--TICKER.md format."""
import os, re
from datetime import datetime
from pathlib import Path

AGENT_FS = Path("D:\\Fasset\\agent_fs\\memories")
DATED_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}--.+\.md$")

def migrate_dir(subdir):
    d = AGENT_FS / subdir
    actions = []
    for fp in sorted(d.glob("*.md")):
        if DATED_PATTERN.match(fp.name):
            continue
        mtime = fp.stat().st_mtime
        date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        stem = fp.stem
        new_name = f"{date_str}--{stem}.md"
        dest = d / new_name
        if dest.exists():
            seq = 0
            while dest.exists():
                seq += 1
                new_name = f"{date_str}--{stem}--{seq}.md"
                dest = d / new_name
        fp.rename(dest)
        actions.append((fp.name, new_name))
    return actions

print("=== Open Trades ===")
for old, new in migrate_dir("open_trades"):
    print(f"  {old:40s} -> {new}")

print()
print("=== Watchlist ===")
for old, new in migrate_dir("watchlist"):
    print(f"  {old:40s} -> {new}")

print()
print("Done.")
