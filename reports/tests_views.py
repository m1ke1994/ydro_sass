from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from clients.models import Client
from subscriptions.models import Subscription


class ReportViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="reports-owner@example.com",
            email="reports-owner@example.com",
            password="test-pass-123",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="Reports Client", is_active=True)
        Subscription.objects.create(
            client=self.client_obj,
            status=Subscription.Status.ACTIVE,
            paid_until=timezone.now() + timedelta(days=30),
            admin_override=True,
        )
        self.api = APIClient()
        self.api.force_authenticate(user=self.user)

    @override_settings(ENABLE_BILLING=False)
    def test_send_now_returns_400_when_telegram_not_connected(self):
        response = self.api.post("/api/mini/reports/send-now/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["ok"])

    @override_settings(ENABLE_BILLING=False)
    @patch("reports.views.send_pdf_to_client_telegram", return_value=True)
    @patch("reports.views.build_pdf_for_client", return_value=(b"%PDF-1.4", "report.pdf"))
    def test_send_now_success(self, _mock_build_pdf, _mock_send):
        self.client_obj.telegram_chat_id = "123456"
        self.client_obj.send_to_telegram = True
        self.client_obj.save(update_fields=["telegram_chat_id", "send_to_telegram"])

        response = self.api.post("/api/mini/reports/send-now/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["ok"])
