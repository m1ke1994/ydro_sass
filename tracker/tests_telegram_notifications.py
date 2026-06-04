from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.sites.models import SiteLead
from clients.models import Client
from leads.models import Lead
from tracker.models import Event, Site


class TrackerTelegramNotificationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tracker-owner",
            email="tracker-owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(
            owner=self.user,
            name="Tracker Site",
            telegram_chat_id="tracker-chat",
            send_to_telegram=True,
        )
        Site.objects.create(token=self.client_obj.api_key, domain="tracker.test", is_active=True)
        self.http = APIClient()

    @patch("leads.services.send_telegram_message")
    def test_get_form_event_does_not_create_lead_or_send_telegram(self, mocked_telegram):
        response = self.http.post(
            "/api/track/event/",
            {
                "token": self.client_obj.api_key,
                "visitor_id": "visitor-1",
                "session_id": "session-1",
                "type": "form_submit",
                "payload": {
                    "method": "GET",
                    "url": "https://tracker.test/contact",
                    "form_key": "contact",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Event.objects.filter(type="form_submit").count(), 1)
        self.assertEqual(Lead.objects.count(), 0)
        self.assertEqual(SiteLead.objects.count(), 0)
        mocked_telegram.assert_not_called()
