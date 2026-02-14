from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from weatherbot.content import build_caption, choose_visual_weather_type
from weatherbot.models import ForecastType
from weatherbot.weather_api import DayForecast


class ContentTests(TestCase):
    def test_build_caption_today(self):
        day = DayForecast(
            date="2026-02-12",
            temp_min=-2,
            temp_max=3,
            weather_code=0,
            humidity_mean=70,
            wind_speed_max=12.2,
            precipitation_probability_max=20,
        )
        caption = build_caption("Москва", ForecastType.TODAY, [day])
        self.assertIn("Погода в Москва", caption)
        self.assertIn("Описание: ясно", caption)
        self.assertIn("Влажность: 70%", caption)
        self.assertIn("Ветер: до 12 км/ч", caption)
        self.assertIn("Осадки: 20%", caption)

    def test_build_caption_three_days(self):
        days = [
            DayForecast(date="2026-02-12", temp_min=-2, temp_max=3, weather_code=0, humidity_mean=60),
            DayForecast(date="2026-02-13", temp_min=-1, temp_max=2, weather_code=61, wind_speed_max=18),
            DayForecast(
                date="2026-02-14",
                temp_min=-5,
                temp_max=1,
                weather_code=71,
                precipitation_probability_max=45,
            ),
        ]
        caption = build_caption("Казань", ForecastType.THREE_DAYS, days)
        self.assertIn("Ближайшие 3 дня", caption)
        self.assertIn("2026-02-14", caption)
        self.assertIn("Влажность: 60%", caption)
        self.assertIn("Ветер: до 18 км/ч", caption)
        self.assertIn("Осадки: 45%", caption)

    def test_choose_visual_weather_type_three_days_uses_priority(self):
        days = [
            DayForecast(date="2026-02-12", temp_min=-2, temp_max=3, weather_code=3),   # cloudy
            DayForecast(date="2026-02-13", temp_min=-1, temp_max=2, weather_code=63),  # rain
            DayForecast(date="2026-02-14", temp_min=-5, temp_max=1, weather_code=71),  # snow
        ]
        visual_type = choose_visual_weather_type(ForecastType.THREE_DAYS, days)
        self.assertEqual(visual_type, "snow")


class InternalPublishEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    @override_settings(CRON_SECRET_TOKEN="secret-123")
    def test_internal_publish_requires_valid_token(self):
        response = self.client.post("/internal/publish/today/")
        self.assertEqual(response.status_code, 401)

    @override_settings(CRON_SECRET_TOKEN="secret-123")
    @patch("weatherbot.views.WeatherPublisher")
    def test_internal_publish_success(self, mocked_publisher_cls):
        mocked_publisher_cls.return_value.publish.return_value = 1
        response = self.client.post(
            "/internal/publish/today/",
            HTTP_X_CRON_TOKEN="secret-123",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["published"], 1)
        mocked_publisher_cls.return_value.publish.assert_called_once_with("today")
