"""DRY RUN: Show what Fix B migration would do without actually renaming."""

import os, re
from datetime import datetime
from pathlib import Path

AGENT_FS = Path("D:\\Fasset\\agent_fs\\memories")
DATED_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}--.+\.md$")

for subdir in ["open_trades", "watchlist"]:
    d = AGENT_FS / subdir
    print()
    print(f"=== {subdir}/ ===")
    for fp in sorted(d.glob("*.md")):
        if DATED_PATTERN.match(fp.name):
            print(f"  [OK]  {fp.name}")
        else:
            mtime = fp.stat().st_mtime
            date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            stem = fp.stem
            new_name = f"{date_str}--{stem}.md"
            if (d / new_name).exists():
                seq = 0
                while (d / f"{date_str}--{stem}--{seq}.md").exists():
                    seq += 1
                new_name = f"{date_str}--{stem}--{seq}.md"
            print(f"  [MIGRATE]  {fp.name:40s} -> {new_name}")
