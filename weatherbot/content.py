from __future__ import annotations

from pathlib import Path

from django.conf import settings

from .models import ForecastType
from .weather_api import DayForecast

VIDEO_BY_WEATHER = {
    "sunny": "sunny.mp4",
    "cloudy": "cloudy.mp4",
    "rain": "rain.mp4",
    "snow": "snow.mp4",
    "thunderstorm": "thunderstorm.mp4",
}

TITLE_BY_FORECAST = {
    ForecastType.TODAY: "Сегодня",
    ForecastType.TOMORROW: "Завтра",
    ForecastType.THREE_DAYS: "Ближайшие 3 дня",
}


def build_caption(city_name: str, forecast_type: str, forecast: list[DayForecast]) -> str:
    title = TITLE_BY_FORECAST[forecast_type]

    if forecast_type in {ForecastType.TODAY, ForecastType.TOMORROW}:
        day = forecast[0]
        return (
            f"🌤 Погода в {city_name}\n\n"
            f"{title}:\n"
            f"Температура: {round(day.temp_min)}..{round(day.temp_max)}°C\n"
            f"Описание: {day.weather_label_ru}\n\n"
            "Хорошего дня ☀️"
        )

    lines = [f"🌤 Погода в {city_name}", "", f"{title}:"]
    for day in forecast:
        lines.append(
            f"{day.date}: {round(day.temp_min)}..{round(day.temp_max)}°C, {day.weather_label_ru}"
        )
    lines.extend(["", "Отличной погоды ☀️"])
    return "\n".join(lines)


def pick_video_path(weather_type: str) -> Path:
    filename = VIDEO_BY_WEATHER.get(weather_type, "cloudy.mp4")
    return Path(settings.MEDIA_ROOT) / "videos" / filename
