from __future__ import annotations

import logging
from datetime import date
from typing import Iterable

from django.db import IntegrityError, transaction

from .content import build_caption, pick_video_path
from .models import BotConfig, Channel, City, ForecastType, PublicationLog
from .telegram_api import TelegramClient
from .weather_api import WeatherClient

logger = logging.getLogger(__name__)


class WeatherPublisher:
    def __init__(self) -> None:
        self.weather = WeatherClient()
        self.telegram = TelegramClient()

    def publish(self, forecast_type: str) -> int:
        config = BotConfig.get_solo()
        if not config.service_enabled:
            logger.info("Service disabled: skip publish for %s", forecast_type)
            return 0

        city = self._resolve_city(config)
        channels = list(Channel.objects.filter(active=True))
        if not channels:
            logger.info("No active channels found")
            return 0

        forecast = self.weather.get_daily_forecast(city.latitude, city.longitude, days=3)
        selected_days = self._select_days(forecast_type, forecast)
        primary_day = selected_days[0]
        target_date = date.fromisoformat(primary_day.date)

        caption = build_caption(city.name, forecast_type, selected_days)
        video_path = pick_video_path(primary_day.weather_type)

        successful = 0
        for channel in channels:
            if self._is_already_published(channel, forecast_type, target_date):
                logger.info(
                    "Skip duplicated publication channel=%s type=%s date=%s",
                    channel.chat_id,
                    forecast_type,
                    target_date,
                )
                continue

            try:
                message_id = self.telegram.send_video(channel.chat_id, caption, video_path)
                self._save_log(channel, city, forecast_type, target_date, True, message_id, "")
                successful += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("Publish failed channel=%s type=%s", channel.chat_id, forecast_type)
                self._save_log(channel, city, forecast_type, target_date, False, "", str(exc))

        logger.info("Publish completed type=%s successful=%s", forecast_type, successful)
        return successful

    def _resolve_city(self, config: BotConfig) -> City:
        city = config.default_city or City.objects.filter(active=True).first()
        if not city:
            raise ValueError("Не найден активный город для публикации")

        if city.latitude is None or city.longitude is None:
            geo = self.weather.geocode_city(city.name)
            city.latitude = geo["latitude"]
            city.longitude = geo["longitude"]
            city.save(update_fields=["latitude", "longitude", "updated_at"])
        return city

    @staticmethod
    def _select_days(forecast_type: str, forecast):
        if forecast_type == ForecastType.TODAY:
            return [forecast[0]]
        if forecast_type == ForecastType.TOMORROW:
            if len(forecast) < 2:
                raise ValueError("Недостаточно данных для прогноза на завтра")
            return [forecast[1]]
        return forecast[:3]

    @staticmethod
    def _is_already_published(channel: Channel, forecast_type: str, target_date: date) -> bool:
        return PublicationLog.objects.filter(
            channel=channel,
            forecast_type=forecast_type,
            target_date=target_date,
            success=True,
        ).exists()

    @staticmethod
    def _save_log(
        channel: Channel,
        city: City,
        forecast_type: str,
        target_date: date,
        success: bool,
        message_id: str,
        error: str,
    ) -> None:
        try:
            with transaction.atomic():
                PublicationLog.objects.create(
                    channel=channel,
                    city=city,
                    forecast_type=forecast_type,
                    target_date=target_date,
                    success=success,
                    message_id=message_id,
                    error=error,
                )
        except IntegrityError:
            logger.warning(
                "Concurrent duplicate publication detected channel=%s type=%s date=%s",
                channel.chat_id,
                forecast_type,
                target_date,
            )
