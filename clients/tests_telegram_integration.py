from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from clients.models import Client
from subscriptions.models import TelegramLink


class TelegramIntegrationApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="telegram-owner@example.com",
            email="telegram-owner@example.com",
            password="test-test-123",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="Telegram Client", is_active=True)
        self.api = APIClient()
        self.api.force_authenticate(user=self.user)

    def test_status_endpoint_returns_connect_payload(self):
        response = self.api.get("/api/mini/client/telegram/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("telegram_connect_url", response.data)
        self.assertIn("connected", response.data)
        self.assertFalse(response.data["connected"])

    def test_send_test_message_requires_connected_chat(self):
        response = self.api.post("/api/mini/client/telegram/test/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["ok"])

    @patch("clients.telegram_views.send_telegram_message", return_value=True)
    def test_send_test_message_when_connected(self, mocked_sender):
        self.client_obj.telegram_chat_id = "123456"
        self.client_obj.send_to_telegram = True
        self.client_obj.save(update_fields=["telegram_chat_id", "send_to_telegram"])

        response = self.api.post("/api/mini/client/telegram/test/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["ok"])
        mocked_sender.assert_called_once()

    def test_disconnect_endpoint_clears_chat_and_links(self):
        self.client_obj.telegram_chat_id = "123456"
        self.client_obj.send_to_telegram = True
        self.client_obj.save(update_fields=["telegram_chat_id", "send_to_telegram"])
        TelegramLink.objects.create(telegram_user_id=777, telegram_chat_id=123456, client=self.client_obj)

        response = self.api.post("/api/mini/client/telegram/disconnect/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["ok"])

        self.client_obj.refresh_from_db()
        self.assertIsNone(self.client_obj.telegram_chat_id)
        self.assertFalse(self.client_obj.send_to_telegram)
        self.assertFalse(TelegramLink.objects.filter(client=self.client_obj).exists())
