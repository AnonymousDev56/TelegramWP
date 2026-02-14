from django.test import TestCase

from weatherbot.content import build_caption, choose_visual_weather_type
from weatherbot.models import ForecastType
from weatherbot.weather_api import DayForecast


class ContentTests(TestCase):
    def test_build_caption_today(self):
        day = DayForecast(date="2026-02-12", temp_min=-2, temp_max=3, weather_code=0)
        caption = build_caption("Москва", ForecastType.TODAY, [day])
        self.assertIn("Погода в Москва", caption)
        self.assertIn("Описание: ясно", caption)

    def test_build_caption_three_days(self):
        days = [
            DayForecast(date="2026-02-12", temp_min=-2, temp_max=3, weather_code=0),
            DayForecast(date="2026-02-13", temp_min=-1, temp_max=2, weather_code=61),
            DayForecast(date="2026-02-14", temp_min=-5, temp_max=1, weather_code=71),
        ]
        caption = build_caption("Казань", ForecastType.THREE_DAYS, days)
        self.assertIn("Ближайшие 3 дня", caption)
        self.assertIn("2026-02-14", caption)

    def test_choose_visual_weather_type_three_days_uses_priority(self):
        days = [
            DayForecast(date="2026-02-12", temp_min=-2, temp_max=3, weather_code=3),   # cloudy
            DayForecast(date="2026-02-13", temp_min=-1, temp_max=2, weather_code=63),  # rain
            DayForecast(date="2026-02-14", temp_min=-5, temp_max=1, weather_code=71),  # snow
        ]
        visual_type = choose_visual_weather_type(ForecastType.THREE_DAYS, days)
        self.assertEqual(visual_type, "snow")
