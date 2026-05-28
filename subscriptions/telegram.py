import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: int, text: str, reply_markup: dict | None = None) -> bool:
    token = (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN is empty, cannot send telegram message")
        return False

    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        response = requests.post(endpoint, json=payload, timeout=15)
        response.raise_for_status()
        body = response.json()
        if not body.get("ok"):
            logger.warning("Telegram sendMessage not ok: chat_id=%s payload=%s", chat_id, body)
            return False
        return True
    except requests.RequestException:
        logger.exception("Failed to send telegram message to chat_id=%s", chat_id)
        return False

