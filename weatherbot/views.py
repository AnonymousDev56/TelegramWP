from __future__ import annotations

import logging

from django.conf import settings
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import BotConfig, Channel, City, ForecastType, Schedule
from .publisher import WeatherPublisher

logger = logging.getLogger(__name__)


def home(request):
    config = BotConfig.get_solo()
    context = {
        "service_enabled": config.service_enabled,
        "default_city": config.default_city.name if config.default_city else "Не выбран",
        "channels_count": Channel.objects.filter(active=True).count(),
        "cities_count": City.objects.filter(active=True).count(),
        "schedules": Schedule.objects.filter(active=True).order_by("publish_time"),
    }
    return render(request, "weatherbot/home.html", context)


@csrf_exempt
def internal_publish(request, forecast_type: str):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    cron_token = settings.CRON_SECRET_TOKEN
    if not cron_token:
        return JsonResponse({"detail": "CRON_SECRET_TOKEN is not configured"}, status=503)

    provided_token = request.headers.get("X-Cron-Token", "")
    if provided_token != cron_token:
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    allowed_types = {choice for choice, _label in ForecastType.choices}
    if forecast_type not in allowed_types:
        return JsonResponse({"detail": "Invalid forecast_type"}, status=400)

    try:
        published = WeatherPublisher().publish(forecast_type)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Internal publish failed type=%s", forecast_type)
        return JsonResponse({"detail": str(exc)}, status=500)

    return JsonResponse(
        {
            "status": "ok",
            "forecast_type": forecast_type,
            "published": published,
        }
    )
