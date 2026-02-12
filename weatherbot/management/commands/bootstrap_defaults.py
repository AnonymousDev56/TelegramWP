from datetime import time

from django.core.management.base import BaseCommand

from weatherbot.models import BotConfig, ForecastType, Schedule


class Command(BaseCommand):
    help = "Create default bot config and schedules"

    def handle(self, *args, **options):
        BotConfig.get_solo()

        defaults = {
            ForecastType.TODAY: time(hour=8, minute=0),
            ForecastType.TOMORROW: time(hour=13, minute=0),
            ForecastType.THREE_DAYS: time(hour=18, minute=0),
        }

        for forecast_type, publish_time in defaults.items():
            Schedule.objects.update_or_create(
                forecast_type=forecast_type,
                defaults={"publish_time": publish_time, "active": True},
            )

        self.stdout.write(self.style.SUCCESS("Defaults are ready"))
