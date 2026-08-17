"""Migrate the legacy shared memory tree into a per-user memory root.

Moves the four position directories (open_trades, pending_entries, watchlist,
closed_trades) out of the shared brain and into agent_fs/users/<username>/.
The learning brain (lessons.md, signals_log/) stays shared. Then seeds the DB
via the normal sync path.

Usage:
    python manage.py import_memories alice [--source agent_fs/memories]
"""
import shutil

from django.core.management.base import BaseCommand

import config
from webapp.memory_sync import sync_all

_SUBDIRS = ("open_trades", "pending_entries", "watchlist", "closed_trades")


class Command(BaseCommand):
    help = "Move the shared position memory tree into a per-user memory root."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument(
            "--source",
            default=None,
            help="Legacy shared memory root (default: agent_fs/memories).",
        )

    def handle(self, *args, **options):
        username = options["username"]
        source = config.SHARED_MEMORY_ROOT if not options["source"] else config.AGENT_FS_ROOT / options["source"]
        dest = config.user_memory_root(username)
        dest.mkdir(parents=True, exist_ok=True)

        moved = 0
        for sub in _SUBDIRS:
            src_dir = source / sub
            if not src_dir.is_dir():
                continue
            dst_dir = dest / sub
            dst_dir.mkdir(parents=True, exist_ok=True)
            for fp in sorted(src_dir.glob("*.md")):
                if (dst_dir / fp.name).exists():
                    self.stdout.write(self.style.WARNING(f"Exists, skipping: {fp.name}"))
                    continue
                shutil.move(str(fp), str(dst_dir / fp.name))
                moved += 1
            try:
                src_dir.rmdir()
            except OSError:
                pass

        sync_all(username)
        self.stdout.write(self.style.SUCCESS(
            f"Moved {moved} memory file(s) into {dest} and synced DB for '{username}'."
        ))
