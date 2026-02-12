import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "telegram_weather_publisher.settings")

application = get_asgi_application()
