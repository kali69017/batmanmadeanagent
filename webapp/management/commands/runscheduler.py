import logging
from datetime import date

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.core.management import call_command
from django.core.management.base import BaseCommand

from webapp.market_holidays import is_market_holiday

logger = logging.getLogger(__name__)


def market_open_scan_job():
    today = date.today()
    if is_market_holiday(today):
        logger.info("Market holiday (%s), skipping scan.", today)
        return
    logger.info("Market open scan starting.")
    call_command("run_scan_all", mode="full", clients_only=True)
    logger.info("Market open scan finished.")


class Command(BaseCommand):
    help = "Starts the in-process scheduler. Run via a PythonAnywhere Always-on Task."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone="America/New_York")
        scheduler.add_jobstore(DjangoJobStore(), "default")
        scheduler.add_job(
            market_open_scan_job,
            trigger=CronTrigger(
                day_of_week="mon-fri",
                hour=9,
                minute=40,
                timezone="America/New_York",
            ),
            id="market_open_scan",
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=300,
        )
        register_events(scheduler)
        self.stdout.write(self.style.SUCCESS("Scheduler running. Job: market_open_scan (mon-fri 9:40 AM ET)."))
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
