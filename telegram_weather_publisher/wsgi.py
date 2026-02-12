import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "telegram_weather_publisher.settings")

application = get_wsgi_application()
