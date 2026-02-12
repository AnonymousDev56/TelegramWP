import logging

from django.core.management.base import BaseCommand, CommandError

from weatherbot.models import ForecastType
from weatherbot.publisher import WeatherPublisher

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Publish weather forecast to active Telegram channels"

    def add_arguments(self, parser):
        parser.add_argument("forecast_type", choices=[choice[0] for choice in ForecastType.choices])

    def handle(self, *args, **options):
        forecast_type = options["forecast_type"]
        try:
            count = WeatherPublisher().publish(forecast_type)
        except Exception as exc:  # noqa: BLE001
            logger.exception("publish_forecast failed")
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Published successfully: {count}"))
