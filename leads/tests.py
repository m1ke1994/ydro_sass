from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from clients.models import Client
from leads.models import Lead
from leads.services import build_lead_telegram_message
from leads.tasks import send_lead_notification_task

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

    def test_get_request_does_not_create_legacy_lead(self):
        response = self.client.get(self.url, {"api_key": self.client_obj.api_key})

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Lead.objects.count(), 0)

    @patch("leads.services.send_telegram_message", return_value=True)
    def test_one_legacy_lead_sends_one_telegram_message(self, mocked_telegram):
        self.client_obj.telegram_chat_id = "legacy-chat"
        self.client_obj.send_to_telegram = True
        self.client_obj.save(update_fields=["telegram_chat_id", "send_to_telegram"])
        lead = Lead.objects.create(
            client=self.client_obj,
            name="Ivan",
            phone="+79999999999",
            notification_context={"domain": "site.ru", "page": "/contact", "form": "Callback"},
        )

        send_lead_notification_task(lead.id)

        mocked_telegram.assert_called_once()
        chat_id, message = mocked_telegram.call_args.args
        self.assertEqual(chat_id, "legacy-chat")
        self.assertIn("Домен: site.ru", message)
        self.assertIn("Форма: Callback", message)

    def test_empty_fields_are_replaced_with_not_specified(self):
        lead = Lead.objects.create(client=self.client_obj, name="", phone="", email=None, message="")

        message = build_lead_telegram_message(lead, client=self.client_obj)

        self.assertIn("Домен: не указано", message)
        self.assertIn("Страница: не указано", message)
        self.assertIn("Форма: не указано", message)
        self.assertIn("Имя: не указано", message)
        self.assertIn("Телефон: не указано", message)
        self.assertIn("Email: не указано", message)
        self.assertIn("Комментарий: не указано", message)
        self.assertIn("IP: не указано", message)
        self.assertNotIn("Источник:", message)
        self.assertNotIn("UTM source:", message)
        self.assertNotIn("UTM medium:", message)
        self.assertNotIn("UTM campaign:", message)
        self.assertNotIn("UTM term:", message)
        self.assertNotIn("UTM content:", message)

    def test_telegram_message_keeps_utm_data_out_of_client_text(self):
        lead = Lead.objects.create(
            client=self.client_obj,
            name="Иван",
            phone="+79999999999",
            source_url="https://site.ru/?utm_source=google&utm_medium=cpc&utm_campaign=spring&utm_term=lila&utm_content=hero",
            utm_source="google",
            utm_medium="cpc",
            utm_campaign="spring",
            notification_context={
                "source": "google ads",
                "utm_term": "lila",
                "utm_content": "hero",
            },
        )

        message = build_lead_telegram_message(lead, client=self.client_obj)

        self.assertEqual(lead.utm_source, "google")
        self.assertEqual(lead.utm_medium, "cpc")
        self.assertEqual(lead.utm_campaign, "spring")
        self.assertNotIn("Источник:", message)
        self.assertNotIn("UTM ", message)
