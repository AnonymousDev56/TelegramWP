from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Dict, List

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


WEATHER_TYPE_BY_CODE = {
    0: "sunny",
    1: "cloudy",
    2: "cloudy",
    3: "cloudy",
    45: "cloudy",
    48: "cloudy",
    51: "rain",
    53: "rain",
    55: "rain",
    56: "rain",
    57: "rain",
    61: "rain",
    63: "rain",
    65: "rain",
    66: "rain",
    67: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    77: "snow",
    80: "rain",
    81: "rain",
    82: "rain",
    85: "snow",
    86: "snow",
    95: "thunderstorm",
    96: "thunderstorm",
    99: "thunderstorm",
}

RUS_WEATHER_LABEL = {
    "sunny": "ясно",
    "cloudy": "облачно",
    "rain": "дождь",
    "snow": "снег",
    "thunderstorm": "гроза",
}


@dataclass
class DayForecast:
    date: str
    temp_min: float
    temp_max: float
    weather_code: int
    humidity_mean: float | None = None
    wind_speed_max: float | None = None
    precipitation_probability_max: float | None = None

    @property
    def weather_type(self) -> str:
        weather_type = WEATHER_TYPE_BY_CODE.get(self.weather_code)
        if weather_type is None:
            logger.warning("Unknown weather code=%s, fallback to 'cloudy'", self.weather_code)
            return "cloudy"
        return weather_type

    @property
    def weather_label_ru(self) -> str:
        return RUS_WEATHER_LABEL[self.weather_type]


class WeatherClient:
    def __init__(self) -> None:
        self.base_url = settings.WEATHER_API_BASE_URL
        self.timeout = settings.DEFAULT_REQUEST_TIMEOUT

    def geocode_city(self, city_name: str) -> Dict[str, float]:
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city_name, "count": 1, "language": "ru", "format": "json"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        if not results:
            raise ValueError(f"Город не найден: {city_name}")

        first = results[0]
        return {"latitude": first["latitude"], "longitude": first["longitude"]}

    def get_daily_forecast(self, latitude: float, longitude: float, days: int = 3) -> List[DayForecast]:
        response = requests.get(
            self.base_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "relative_humidity_2m_mean,wind_speed_10m_max,precipitation_probability_max"
                ),
                "forecast_days": max(days, 1),
                "timezone": "auto",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()

        daily = payload.get("daily", {})
        dates = daily.get("time", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        weather_codes = daily.get("weather_code") or daily.get("weathercode", [])
        humidity_mean = daily.get("relative_humidity_2m_mean", [])
        wind_speed_max = daily.get("wind_speed_10m_max", [])
        precipitation_probability_max = daily.get("precipitation_probability_max", [])

        forecast = []
        for index, date in enumerate(dates):
            try:
                forecast.append(
                    DayForecast(
                        date=date,
                        temp_min=temp_min[index],
                        temp_max=temp_max[index],
                        weather_code=weather_codes[index],
                        humidity_mean=humidity_mean[index] if index < len(humidity_mean) else None,
                        wind_speed_max=wind_speed_max[index] if index < len(wind_speed_max) else None,
                        precipitation_probability_max=(
                            precipitation_probability_max[index]
                            if index < len(precipitation_probability_max)
                            else None
                        ),
                    )
                )
            except IndexError:
                logger.warning("Incomplete weather payload for date=%s", date)

        if not forecast:
            raise ValueError("Пустой прогноз от weather API")
        return forecast
