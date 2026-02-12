import logging
import signal
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from django.utils import timezone

from weatherbot.models import Schedule

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run scheduler for weather publications"

    def handle(self, *args, **options):
        scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone())

        stop_event = threading.Event()

        def shutdown_handler(signum, frame):  # noqa: ARG001
            logger.info("Received signal %s, stopping scheduler", signum)
            stop_event.set()

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        self._sync_jobs(scheduler)
        scheduler.start()
        logger.info("Scheduler started")

        try:
            while not stop_event.is_set():
                time.sleep(30)
                self._sync_jobs(scheduler)
        finally:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def _sync_jobs(self, scheduler: BackgroundScheduler) -> None:
        try:
            schedules = list(Schedule.objects.filter(active=True))
        except OperationalError:
            logger.warning("Database is not ready yet for schedules")
            return

        active_ids = set()
        for schedule in schedules:
            job_id = f"publish_{schedule.forecast_type}"
            active_ids.add(job_id)
            trigger = CronTrigger(
                hour=schedule.publish_time.hour,
                minute=schedule.publish_time.minute,
            )

            scheduler.add_job(
                self._run_publication,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                args=[schedule.forecast_type],
                max_instances=1,
                coalesce=True,
                misfire_grace_time=600,
            )

        for job in scheduler.get_jobs():
            if job.id not in active_ids:
                scheduler.remove_job(job.id)

    @staticmethod
    def _run_publication(forecast_type: str) -> None:
        logger.info("Trigger publication type=%s", forecast_type)
        call_command("publish_forecast", forecast_type)
