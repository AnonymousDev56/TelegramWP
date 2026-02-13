from __future__ import annotations

import logging
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self) -> None:
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN не задан")
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.timeout = settings.DEFAULT_REQUEST_TIMEOUT

    def send_video(self, chat_id: str, caption: str, video_path: Path) -> str:
        if not video_path.exists():
            raise FileNotFoundError(f"Видео файл не найден: {video_path}")

        url = f"{self.base_url}/sendVideo"
        with video_path.open("rb") as video_file:
            response = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption},
                files={"video": video_file},
                timeout=self.timeout,
            )

        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram API error: {payload}")

        message_id = payload.get("result", {}).get("message_id")
        logger.info("Telegram message sent chat_id=%s message_id=%s", chat_id, message_id)
        return str(message_id)

    def send_message(self, chat_id: str, text: str) -> str:
        url = f"{self.base_url}/sendMessage"
        response = requests.post(
            url,
            data={"chat_id": chat_id, "text": text},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram API error: {payload}")

        message_id = payload.get("result", {}).get("message_id")
        logger.info("Telegram message sent chat_id=%s message_id=%s", chat_id, message_id)
        return str(message_id)
