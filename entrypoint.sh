#!/usr/bin/env bash
set -euo pipefail

python manage.py migrate --noinput
python manage.py bootstrap_defaults
python manage.py collectstatic --noinput

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.getenv("DJANGO_SUPERUSER_USERNAME")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")

if username and password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
PY
fi

case "${1:-web}" in
  web)
    exec gunicorn telegram_weather_publisher.wsgi:application --bind 0.0.0.0:8000 --workers "${WEB_CONCURRENCY:-2}"
    ;;
  scheduler)
    exec python manage.py run_scheduler
    ;;
  all)
    if [ "${ENABLE_INTERNAL_SCHEDULER:-true}" = "true" ]; then
      (
        while true; do
          echo "Starting scheduler process..."
          python manage.py run_scheduler
          echo "Scheduler process exited; restarting in 5s..."
          sleep 5
        done
      ) &
    else
      echo "Internal scheduler is disabled (ENABLE_INTERNAL_SCHEDULER=false)"
    fi
    exec gunicorn telegram_weather_publisher.wsgi:application --bind 0.0.0.0:8000 --workers 1
    ;;
  *)
    exec "$@"
    ;;
esac
