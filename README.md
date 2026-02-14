# Telegram Weather Publisher

Серверный Django-сервис, который публикует прогноз погоды в Telegram по расписанию.
Управление настройками выполняется через Django Admin, деплой — через Docker/Render, CI/CD — через GitHub Actions.

## Коротко о проекте

- Источник погоды: Open-Meteo
- Канал доставки: Telegram Bot API
- Режимы публикации: `today`, `tomorrow`, `three_days`
- Контент: видео (`mp4`) + `caption`
- Fallback: если видео отсутствует, отправляется текст
- Идемпотентность: защита от дублей по `(channel, forecast_type, target_date)`

## Скриншоты

<img width="1919" height="984" alt="main" src="https://github.com/user-attachments/assets/64057398-9d66-48a4-95d8-cbd18501e80e" />
<img width="1919" height="997" alt="admin" src="https://github.com/user-attachments/assets/6877939e-dacf-47d7-892f-ecc8b671d83b" />
<img width="1919" height="1001" alt="schedules" src="https://github.com/user-attachments/assets/a13d2231-2910-400a-9f52-344102158067" />
<img width="1261" height="929" alt="telegram" src="https://github.com/user-attachments/assets/3138d0e0-92af-439e-b570-74ea593de736" />
<img width="1910" height="1000" alt="actions" src="https://github.com/user-attachments/assets/17f2fe63-2c06-4135-ac3b-65ede6babb98" />

## Архитектура

- `weatherbot/weather_api.py` — клиент Open-Meteo (геокодинг + daily forecast)
- `weatherbot/content.py` — сборка текста и выбор видео
- `weatherbot/telegram_api.py` — отправка в Telegram (`sendVideo` / `sendMessage`)
- `weatherbot/publisher.py` — orchestration публикации и идемпотентность
- `weatherbot/management/commands/run_scheduler.py` — APScheduler для внутреннего расписания
- `weatherbot/views.py` — web-страницы и internal endpoint для cron-триггера
- `weatherbot/models.py` — модели и логи публикаций

## Модели

- `City` — город (имя, координаты, active)
- `Channel` — Telegram chat/channel (`chat_id`, active)
- `Schedule` — расписание по типам (`today/tomorrow/three_days`)
- `BotConfig` — singleton-конфиг (`service_enabled`, `default_city`)
- `PublicationLog` — результат публикации, `message_id`, `error`

## Как работает публикация

1. Выбирается тип публикации (`today`, `tomorrow`, `three_days`).
2. Проверяется `BotConfig.service_enabled`.
3. Определяется город (`default_city` или первый активный).
4. Если координат нет — геокодинг через Open-Meteo.
5. Запрашивается daily-прогноз.
6. Формируется caption:
   - температура
   - описание
   - влажность
   - ветер
   - вероятность осадков
7. Выбирается видео по типу погоды.
8. В Telegram отправляется видео+caption (или текст fallback).
9. Пишется `PublicationLog`.
10. При повторе за тот же день/тип/канал — дубль блокируется.

## Режимы расписания

### 1) Внутренний scheduler (APScheduler)

Запускается внутри приложения (`run_scheduler`) и берет расписания из модели `Schedule`.

Плюсы:
- просто локально
- расписание редактируется в админке

Минусы на Render Free:
- при sleep процесс может не работать в нужную минуту

### 2) Внешний scheduler (рекомендуется для Render Free)

GitHub Actions cron вызывает защищенный endpoint:

- `POST /internal/publish/today/`
- `POST /internal/publish/tomorrow/`
- `POST /internal/publish/three_days/`

Защита: заголовок `X-Cron-Token` == `CRON_SECRET_TOKEN`.

Плюсы:
- не зависит от засыпания внутреннего scheduler процесса
- удобно диагностировать через Actions logs

## Быстрый локальный запуск

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

В отдельном терминале (если нужен внутренний scheduler):

```bash
python manage.py run_scheduler
```

## Docker запуск

```bash
cp .env.example .env
docker compose up --build
```

После запуска:

- `http://localhost:8000/`
- `http://localhost:8000/admin/`
- `http://localhost:8000/health/`

## Настройка админки

1. `Cities` — добавь город (например `Astana`)
2. `Channels` — добавь `chat_id` (например `@weathertest12345`)
3. `Bot configs` — включи `service_enabled`, выбери `default_city`
4. `Schedules` — укажи 3 времени для `today`, `tomorrow`, `three_days`

Пример расписания:
- `today` -> `08:00`
- `tomorrow` -> `14:00`
- `three_days` -> `20:00`

## Видео-контент

Папка: `media/videos/`

Нужные файлы:
- `sunny.mp4`
- `cloudy.mp4`
- `rain.mp4`
- `snow.mp4`
- `thunderstorm.mp4`

Если файла нет, сработает fallback: отправка текстом.

## Переменные окружения

### Базовые
- `DJANGO_SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `TIME_ZONE` (для Астаны: `Asia/Almaty`)
- `LOG_LEVEL`
- `DATABASE_URL` (Postgres)
- `TELEGRAM_BOT_TOKEN`

### Scheduler/Weather
- `SCHEDULER_MISFIRE_GRACE_SECONDS`
- `SCHEDULER_STARTUP_CATCHUP`
- `ENABLE_INTERNAL_SCHEDULER`
- `CRON_SECRET_TOKEN`
- `WEATHER_INCLUDE_CODE_IN_CAPTION`
- `DEFAULT_REQUEST_TIMEOUT`
- `WEATHER_API_BASE_URL`

### Admin bootstrap
- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

## Deploy на Render

Проект содержит `render.yaml`.

Минимум для env в Render:
- `DATABASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `DJANGO_SECRET_KEY`
- `DJANGO_SUPERUSER_PASSWORD`
- `TIME_ZONE=Asia/Almaty`
- `CRON_SECRET_TOKEN`
- `ENABLE_INTERNAL_SCHEDULER=False` (если используешь GitHub cron)

## CI/CD

### CI + автодеплой Render

Workflow: `.github/workflows/ci.yml`

- `check`
- `test`
- `docker build`
- trigger deploy hook на Render

Нужный secret в GitHub:
- `RENDER_DEPLOY_HOOK_URL`

### Scheduled Publish (GitHub cron)

Workflow: `.github/workflows/scheduled_publish.yml`

Нужные GitHub secrets:
- `PUBLISH_BASE_URL` (например `https://telegram-weather-publisher.onrender.com`)
- `CRON_SECRET_TOKEN` (тот же токен, что в Render)

Расписание workflow (UTC):
- `0 3 * * *` -> 08:00 Asia/Almaty -> `today`
- `0 9 * * *` -> 14:00 Asia/Almaty -> `tomorrow`
- `0 15 * * *` -> 20:00 Asia/Almaty -> `three_days`

Также поддержан ручной запуск (`workflow_dispatch`) для тестов.

## Диагностика проблем

### `published: 0` в Actions

Смотри `diagnostics` в ответе endpoint. Частые причины:
- `already_published_for_target_date` — уже был пост за эту дату/тип
- `service_disabled`
- `no_active_channels`
- `no_active_city`

### Нет поста в Telegram

Проверить:
- `TELEGRAM_BOT_TOKEN` корректный
- бот админ в канале
- `chat_id` правильный
- канал/город активны
- `service_enabled = true`

### На free Render пропуски по времени

Использовать GitHub cron режим (рекомендуется), а внутренний scheduler отключить:
- `ENABLE_INTERNAL_SCHEDULER=False`

## Почему могут быть 2 публикации после рестарта

Если включен `SCHEDULER_STARTUP_CATCHUP=True`, при старте может сработать догон пропущенного слота.
Это нормальное поведение для восстановления после downtime.

## Лицензии и источники

- Weather API: Open-Meteo
- Telegram API: Bot API
- Видео: free stock assets (смотри лицензию конкретного источника)

## Live demo

https://telegram-weather-publisher.onrender.com
