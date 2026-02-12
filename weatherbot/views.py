from django.shortcuts import render

from .models import BotConfig, Channel, City, Schedule


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
