import logging

from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sites.telegram_binding import resolve_site_start_payload
from clients.telegram_binding import resolve_secure_start_payload
from leads.services import send_telegram_message
from telegram_logs.services import extract_message, save_telegram_update

logger = logging.getLogger(__name__)


def _process_start_payload(update: dict) -> None:
    message = extract_message(update)
    if not isinstance(message, dict):
        return
    text = (message.get("text") or message.get("caption") or "").strip()
    if not text.lower().startswith("/start"):
        return

    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return

    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    chat_id = chat.get("id")
    if chat_id is None:
        return

    payload = parts[1].strip()
    site = resolve_site_start_payload(payload)
    if site is not None:
        site.telegram_chat_id = str(chat_id)
        site.send_to_telegram = True
        site.telegram_connected_at = timezone.now()
        site.save(update_fields=["telegram_chat_id", "send_to_telegram", "telegram_connected_at", "updated_at"])
        send_telegram_message(str(chat_id), f"Telegram подключен к сайту «{site.name}».")
        return

    client = resolve_secure_start_payload(payload)
    if client is not None:
        client.telegram_chat_id = str(chat_id)
        client.send_to_telegram = True
        client.save(update_fields=["telegram_chat_id", "send_to_telegram"])
        send_telegram_message(str(chat_id), f"Telegram подключен к Mini CRM «{client.name}».")


class TelegramWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope = "public_telegram_webhook"

    def post(self, request, *args, **kwargs):
        secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
        if secret:
            incoming_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if incoming_secret != secret:
                logger.warning("Telegram webhook rejected: invalid secret token")
                return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        update = request.data if isinstance(request.data, dict) else {}
        update_id = update.get("update_id")
        if update_id is None:
            logger.warning("Telegram webhook rejected: missing update_id")
            return Response({"detail": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            _, created = save_telegram_update(update)
            if not created:
                logger.info("Telegram webhook duplicate update ignored: update_id=%s", update_id)
            else:
                _process_start_payload(update)
        except Exception:
            logger.exception("Failed to save telegram update log")
            return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"ok": True}, status=status.HTTP_200_OK)
