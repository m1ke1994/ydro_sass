import logging

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from telegram_logs.services import save_telegram_update

logger = logging.getLogger(__name__)


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
        except Exception:
            logger.exception("Failed to save telegram update log")
            return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"ok": True}, status=status.HTTP_200_OK)
