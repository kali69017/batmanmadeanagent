"""Run a scan for a user — the scheduled/background scan entry point.

Usage:
    python manage.py run_scan <username> [--mode full|fasset]

This replaces the client-triggered scan stream. A cron job or Celery beat
should call this on a schedule (e.g. daily pre-market). It runs the agent
synchronously, then syncs memory, recomputes signal win rates, and generates
today's picks — the full post-run pipeline without an SSE stream.
"""
import sys

from django.core.management.base import BaseCommand

import config
from webapp.agent_service import AgentRunner


class Command(BaseCommand):
    help = "Run a market scan for a user (scheduled/background)."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--mode", default="full", choices=["full", "fasset"])

    def handle(self, *args, **options):
        username = options["username"]
        mode = options["mode"]

        from webapp.views import FASSET_SCAN_QUERY, FULL_SCAN_QUERY

        query = FASSET_SCAN_QUERY if mode == "fasset" else FULL_SCAN_QUERY

        self.stdout.write(f"Starting {mode} scan for {username}…")

        events = []
        runner = AgentRunner(username=username)
        job = runner.run(query, scan=True)

        # Drive the job synchronously, collecting events
        def collect(event):
            events.append(event)

        job(collect)

        errors = [e for e in events if e.get("type") == "error"]
        if errors:
            self.stderr.write(self.style.ERROR(f"Scan completed with {len(errors)} error(s):"))
            for e in errors:
                self.stderr.write(self.style.ERROR(f"  {e.get('message')}"))
            sys.exit(1)

        scan_result = next((e for e in events if e.get("type") == "scan_result"), None)
        if scan_result:
            positions = scan_result.get("positions", {})
            self.stdout.write(self.style.SUCCESS(
                f"Scan complete: {len(positions.get('open', []))} open, "
                f"{len(positions.get('pending', []))} pending."
            ))
        else:
            self.stdout.write(self.style.SUCCESS("Scan complete."))
