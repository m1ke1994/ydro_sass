from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from clients.models import Client
from reports.models import ReportSettings


class DailyReportsCommandTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="daily-report-owner@example.com",
            email="daily-report-owner@example.com",
            password="test-pass-123",
        )
        self.client_obj = Client.objects.create(
            owner=self.user,
            name="Daily Report Client",
            is_active=True,
            send_to_telegram=True,
            telegram_chat_id="123456",
        )

    @patch("reports.management.commands.send_daily_reports.send_pdf_to_client_telegram", return_value=True)
    @patch("reports.management.commands.send_daily_reports.build_pdf_for_client", return_value=(b"%PDF-1.4 test", "daily.pdf"))
    def test_send_daily_reports_builds_and_sends_pdf(self, _mock_build_pdf, mock_send):
        out = StringIO()
        call_command("send_daily_reports", stdout=out)
        self.assertIn("sent client_id=", out.getvalue())
        mock_send.assert_called_once()

        settings_obj = ReportSettings.objects.get(client=self.client_obj)
        self.assertIsNotNone(settings_obj.last_sent_at)
        self.assertEqual(settings_obj.last_error, "")

    @patch("reports.management.commands.send_daily_reports.send_pdf_to_client_telegram", return_value=True)
    @patch("reports.management.commands.send_daily_reports.build_pdf_for_client", return_value=(b"%PDF-1.4 test", "daily.pdf"))
    def test_send_daily_reports_skips_when_telegram_not_connected(self, _mock_build_pdf, mock_send):
        self.client_obj.telegram_chat_id = None
        self.client_obj.save(update_fields=["telegram_chat_id"])

        out = StringIO()
        call_command("send_daily_reports", stdout=out)
        self.assertIn("skip client_id=", out.getvalue())
        mock_send.assert_not_called()
