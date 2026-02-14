from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import BotConfig, Channel, City, ForecastType, PublicationLog, Schedule
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

    diagnostics = _build_publish_diagnostics(forecast_type, published)
    return JsonResponse(
        {
            "status": "ok",
            "forecast_type": forecast_type,
            "published": published,
            "diagnostics": diagnostics,
        }
    )


def _build_publish_diagnostics(forecast_type: str, published: int) -> dict:
    config = BotConfig.get_solo()
    active_channels = list(Channel.objects.filter(active=True))
    active_city = config.default_city or City.objects.filter(active=True).first()

    today = timezone.localdate()
    target_date = today
    if forecast_type == ForecastType.TOMORROW:
        target_date = today + timedelta(days=1)

    successful_today = PublicationLog.objects.filter(
        channel__in=active_channels,
        forecast_type=forecast_type,
        target_date=target_date,
        success=True,
    ).count()

    reasons = []
    if not config.service_enabled:
        reasons.append("service_disabled")
    if not active_channels:
        reasons.append("no_active_channels")
    if not active_city:
        reasons.append("no_active_city")
    if published == 0 and successful_today > 0:
        reasons.append("already_published_for_target_date")

    return {
        "service_enabled": config.service_enabled,
        "active_channels": len(active_channels),
        "active_city": active_city.name if active_city else None,
        "target_date": str(target_date),
        "successful_logs_for_target_date": successful_today,
        "reasons": reasons,
    }
