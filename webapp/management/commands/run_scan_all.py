"""Run a scan for every active client — the cron entry point.

Usage:
    python manage.py run_scan_all [--mode full|fasset]

Wire this to cron (weekdays pre-market). On Unix:
    0 6 * * 1-5  cd /path/to/fasset && .venv/bin/python manage.py run_scan_all --mode full

On Windows, use Task Scheduler with an equivalent daily trigger pointing at
`.venv\\Scripts\\python.exe manage.py run_scan_all --mode full`.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run a scan for every active client (cron entry point)."

    def add_arguments(self, parser):
        parser.add_argument("--mode", default="full", choices=["full", "fasset"])
        parser.add_argument("--clients-only", action="store_true", help="Skip staff/superuser accounts.")

    def handle(self, *args, **options):
        from django.core.management import call_command

        User = get_user_model()
        mode = options["mode"]
        clients_only = options["clients_only"]

        qs = User.objects.filter(is_active=True)
        if clients_only:
            qs = qs.filter(is_staff=False, is_superuser=False)
        usernames = list(qs.values_list("username", flat=True))

        if not usernames:
            self.stdout.write(self.style.WARNING("No active users to scan."))
            return

        failed = 0
        for username in usernames:
            self.stdout.write(f"→ Scanning {username} ({mode})…")
            try:
                call_command("run_scan", username, mode=mode, stdout=self.stdout, stderr=self.stderr)
            except SystemExit as e:
                if e.code not in (0, None):
                    failed += 1
            except Exception as exc:  # noqa: BLE001 — keep going across users
                self.stderr.write(self.style.ERROR(f"  {username}: {exc}"))
                failed += 1

        if failed:
            self.stderr.write(self.style.ERROR(f"{failed} scan(s) failed."))
        else:
            self.stdout.write(self.style.SUCCESS(f"All {len(usernames)} scan(s) complete."))
