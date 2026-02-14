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

WEATHER_TYPE_PRIORITY = {
    "thunderstorm": 5,
    "snow": 4,
    "rain": 3,
    "cloudy": 2,
    "sunny": 1,
}


def choose_visual_weather_type(forecast_type: str, forecast: list[DayForecast]) -> str:
    if not forecast:
        return "cloudy"
    if forecast_type in {ForecastType.TODAY, ForecastType.TOMORROW}:
        return forecast[0].weather_type
    return max(forecast, key=lambda day: WEATHER_TYPE_PRIORITY.get(day.weather_type, 0)).weather_type


def _format_description(day: DayForecast) -> str:
    if settings.WEATHER_INCLUDE_CODE_IN_CAPTION:
        return f"{day.weather_label_ru} (код: {day.weather_code})"
    return day.weather_label_ru


def _format_extra_metrics(day: DayForecast) -> list[str]:
    lines = []
    if day.humidity_mean is not None:
        lines.append(f"Влажность: {round(day.humidity_mean)}%")
    if day.wind_speed_max is not None:
        lines.append(f"Ветер: до {round(day.wind_speed_max)} км/ч")
    if day.precipitation_probability_max is not None:
        lines.append(f"Осадки: {round(day.precipitation_probability_max)}%")
    return lines


def build_caption(city_name: str, forecast_type: str, forecast: list[DayForecast]) -> str:
    title = TITLE_BY_FORECAST[forecast_type]

    if forecast_type in {ForecastType.TODAY, ForecastType.TOMORROW}:
        day = forecast[0]
        return (
            f"🌤 Погода в {city_name}\n\n"
            f"{title}:\n"
            f"Температура: {round(day.temp_min)}..{round(day.temp_max)}°C\n"
            f"Описание: {_format_description(day)}\n"
            f"{chr(10).join(_format_extra_metrics(day))}\n\n"
            "Хорошего дня ☀️"
        )

    lines = [f"🌤 Погода в {city_name}", "", f"{title}:"]
    for day in forecast:
        line = f"{day.date}: {round(day.temp_min)}..{round(day.temp_max)}°C, {_format_description(day)}"
        extras = _format_extra_metrics(day)
        if extras:
            line = f"{line}; " + ", ".join(extras)
        lines.append(line)
    lines.extend(["", "Отличной погоды ☀️"])
    return "\n".join(lines)


def pick_video_path(weather_type: str) -> Path:
    filename = VIDEO_BY_WEATHER.get(weather_type, "cloudy.mp4")
    return Path(settings.MEDIA_ROOT) / "videos" / filename
