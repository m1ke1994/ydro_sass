import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: str, message: str, parse_mode: str | None = None) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.info("Telegram token is not configured, skipping message.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    if parse_mode:
        payload["parse_mode"] = parse_mode
        payload["disable_web_page_preview"] = True
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        body = response.json()
        if not body.get("ok"):
            logger.warning("Telegram sendMessage not ok: chat_id=%s payload=%s", chat_id, body)
            return False
        return True
    except requests.RequestException:
        logger.exception("Failed to send telegram message for chat_id=%s", chat_id)
        return False

