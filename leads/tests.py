from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clients.models import Client
from leads.models import Lead

User = get_user_model()


class PublicLeadApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner@example.com", email="owner@example.com", password="secret12345")
        self.client_obj = Client.objects.create(owner=self.user, name="Site A")
        self.url = reverse("public_lead")
        self.payload = {
            "name": "Ivan",
            "phone": "+79999999999",
            "email": "test@mail.com",
            "message": "Need consultation",
            "source_url": "https://site.ru",
            "utm_source": "instagram",
            "utm_medium": "cpc",
            "utm_campaign": "spring",
        }

    def test_rejects_invalid_api_key(self):
        response = self.client.post(self.url, data=self.payload, format="json", HTTP_X_API_KEY="bad-key")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Lead.objects.count(), 0)

    @patch("leads.serializers.send_lead_notification_task.delay")
    def test_creates_lead_for_valid_api_key(self, mocked_task):
        response = self.client.post(
            self.url,
            data=self.payload,
            format="json",
            HTTP_X_API_KEY=self.client_obj.api_key,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.first()
        self.assertEqual(lead.client, self.client_obj)
        self.assertEqual(lead.status, Lead.Status.NEW)
        mocked_task.assert_called_once()

