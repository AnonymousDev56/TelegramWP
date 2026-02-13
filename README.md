# Telegram Weather Publisher

Серверный сервис на Python/Django, который публикует прогноз погоды в Telegram-каналы/группы по расписанию и управляется через Django Admin.

Django + Telegram Bot + Scheduler, автопостинг погоды (today/tomorrow/3 days), управление через admin, Docker-ready deploy.

## Что умеет

- Получает прогноз погоды (сегодня, завтра, 3 дня) через Open-Meteo API
- Публикует посты в несколько Telegram-каналов
- Отправляет `mp4` как фон + текст в `caption`
- Работает по расписанию (cron-style через APScheduler)
- Управляется через web-админку (`/admin`)
- Логирует запуск задач, успехи и ошибки

## Архитектура

- `weatherbot/weather_api.py` - интеграция с Open-Meteo
- `weatherbot/telegram_api.py` - отправка видео в Telegram Bot API
- `weatherbot/publisher.py` - бизнес-логика публикации и идемпотентность
- `weatherbot/management/commands/run_scheduler.py` - планировщик
- `weatherbot/models.py` - `Channel`, `City`, `Schedule`, `BotConfig`, `PublicationLog`

## Модели

- `City`: город + координаты
- `Channel`: Telegram-канал/группа (`chat_id`)
- `Schedule`: время публикации для типов (`today`, `tomorrow`, `three_days`)
- `BotConfig`: глобальный флаг включения сервиса + дефолтный город
- `PublicationLog`: аудит публикаций + защита от дублей

## Быстрый старт (одной командой)

1. Создайте `.env`:

```bash
cp .env.example .env
```

2. Запустите:

```bash
docker compose up --build
```

После запуска:

- Админка: `http://localhost:8000/admin/`
- Healthcheck: `http://localhost:8000/health/`
- Суперпользователь создается автоматически из `.env`

## Настройка через админку

1. Добавьте `City` (можно без координат, подтянутся автоматически).
2. Добавьте `Channel` с `chat_id` (например `@my_channel` или `-100...`).
3. Проверьте `BotConfig` (`service_enabled=True`, `default_city` выбран).
4. Настройте `Schedule` для 3 типов прогнозов.

## Ручной запуск публикации

```bash
python manage.py publish_forecast today
python manage.py publish_forecast tomorrow
python manage.py publish_forecast three_days
```

## Видео-контент

Положите mp4-файлы в `media/videos/`:

- `sunny.mp4`
- `cloudy.mp4`
- `rain.mp4`
- `snow.mp4`
- `thunderstorm.mp4`

## Пример поста

```text
🌤 Погода в Москва

Сегодня:
Температура: -2..3°C
Описание: ясно

Хорошего дня ☀️
```

## Переменные окружения

- `DJANGO_SECRET_KEY` - секрет Django
- `DEBUG` - режим отладки
- `ALLOWED_HOSTS` - разрешенные хосты
- `TIME_ZONE` - таймзона
- `TELEGRAM_BOT_TOKEN` - токен Telegram-бота
- `WEATHER_API_BASE_URL` - URL weather API
- `DEFAULT_REQUEST_TIMEOUT` - timeout HTTP-запросов
- `DJANGO_SUPERUSER_USERNAME` - логин админа
- `DJANGO_SUPERUSER_EMAIL` - email админа
- `DJANGO_SUPERUSER_PASSWORD` - пароль админа

## Идемпотентность и логи

- Дубли блокируются по ключу: `channel + forecast_type + target_date`
- Логи публикаций сохраняются в `PublicationLog`
- Системные логи идут через стандартный `python logging`

## Локальный запуск без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py bootstrap_defaults
python manage.py createsuperuser
python manage.py runserver
```

В отдельном терминале:

```bash
python manage.py run_scheduler
```

## Deploy на Render (free)

В проект добавлен `render.yaml` для бесплатного деплоя одним web-сервисом.

1. Запушь проект в GitHub (см. шаги ниже).
2. На Render: `New` -> `Blueprint` -> выбери репозиторий.
3. В env переменных Render обязательно задай:
   - `TELEGRAM_BOT_TOKEN`
   - `DJANGO_SUPERUSER_PASSWORD`
   - `DATABASE_URL` (PostgreSQL URL)
4. После деплоя открой:
   - `/` (главная)
   - `/admin/` (админка)
   - `/health/` (healthcheck)

Важно для free Render:
- free web-сервис засыпает после 15 минут без входящего трафика;
- локальная файловая система и SQLite непостоянные (теряются при sleep/restart/redeploy);
- есть лимит 750 instance hours/месяц на workspace.

Источники:
- https://render.com/docs/free

## Публикация на GitHub

```bash
cd /home/user/projects/TelegramWP
git init
git add .
git commit -m "Initial release: Telegram Weather Publisher"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
git push -u origin main
```

## Auto CI/CD (GitHub Actions -> Render)

CI уже запускается на каждый push/PR: `check`, `test`, `docker build`.

Для автодеплоя на Render:
1. Render -> `Settings` -> `Deploy Hook` -> скопируй URL.
2. GitHub repo -> `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`.
3. Создай секрет `RENDER_DEPLOY_HOOK_URL` и вставь туда URL хука.
4. После этого каждый push в `main` будет автоматически деплоить сервис на Render (после успешного CI).

CI/CD smoke test: enabled and verified on February 13, 2026.

Live demo: https://telegram-weather-publisher.onrender.com
