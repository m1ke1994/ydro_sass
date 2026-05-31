import logging

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClientUser
from clients.serializers import ClientSettingsSerializer
from leads.services import send_telegram_message
from subscriptions.access import billing_is_enabled
from subscriptions.models import TelegramLink

logger = logging.getLogger(__name__)


class TelegramIntegrationStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def get(self, request):
        serializer = ClientSettingsSerializer(instance=request.client, context={"request": request})
        data = serializer.data
        return Response(
            {
                "connected": bool(request.client.telegram_chat_id),
                "telegram_status": data.get("telegram_status"),
                "telegram_connect_url": data.get("telegram_connect_url"),
                "send_to_telegram": bool(request.client.send_to_telegram),
                "billing_enabled": billing_is_enabled(),
            },
            status=status.HTTP_200_OK,
        )


class TelegramIntegrationDisconnectView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def post(self, request):
        client = request.client
        if not client.telegram_chat_id and not client.send_to_telegram:
            return Response({"ok": True, "detail": "Telegram уже отключен."}, status=status.HTTP_200_OK)

        client.telegram_chat_id = None
        client.send_to_telegram = False
        client.save(update_fields=["telegram_chat_id", "send_to_telegram"])
        TelegramLink.objects.filter(client=client).delete()
        return Response({"ok": True, "detail": "Telegram отключен."}, status=status.HTTP_200_OK)


class TelegramIntegrationSendTestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def post(self, request):
        client = request.client
        if not client.telegram_chat_id:
            return Response(
                {
                    "ok": False,
                    "detail": "Telegram пока не подключен. Сначала нажмите «Подключить Telegram».",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        test_text = (
            "Тестовое сообщение из Yadro Mini CRM\n\n"
            f"Сайт: {client.name}\n"
            f"Дата: {timezone.localtime(timezone.now()):%d.%m.%Y %H:%M}"
        )
        delivered = send_telegram_message(client.telegram_chat_id, test_text)
        if delivered:
            return Response({"ok": True, "detail": "Тестовое сообщение отправлено."}, status=status.HTTP_200_OK)

        logger.warning("Telegram test message failed client_id=%s chat_id=%s", client.id, client.telegram_chat_id)
        return Response(
            {
                "ok": False,
                "detail": "Не удалось отправить сообщение в Telegram. Проверьте подключение бота.",
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )
