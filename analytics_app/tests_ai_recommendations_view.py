from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from clients.models import Client
from subscriptions.models import Subscription


class AnalyticsAiRecommendationsViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="analytics-ai-owner",
            email="analytics-ai-owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="Analytics AI Client")
        Subscription.objects.create(
            client=self.client_obj,
            status=Subscription.Status.ACTIVE,
            paid_until=timezone.now() + timedelta(days=30),
            admin_override=True,
        )
        self.http = APIClient()
        self.http.force_authenticate(user=self.user)

    @patch("analytics_app.views.get_conversion_ai_recommendations")
    def test_ai_recommendations_endpoint_returns_ai_payload(self, mocked_ai_service):
        mocked_ai_service.return_value = {
            "success": True,
            "source": "ai",
            "title": "AI-рекомендации по повышению конверсии",
            "summary": "Найдены точки роста по кнопкам и форме.",
            "items": ["Сократите количество полей формы до 3."],
            "priority": "high",
        }

        response = self.http.get("/api/analytics/ai-recommendations/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["source"], "ai")
        self.assertIn("period", payload)
        mocked_ai_service.assert_called_once()
        call_kwargs = mocked_ai_service.call_args.kwargs
        self.assertEqual(call_kwargs["client_id"], self.client_obj.id)
        self.assertFalse(call_kwargs["force_refresh"])

    @patch("analytics_app.views.get_conversion_ai_recommendations")
    def test_ai_recommendations_endpoint_supports_force_refresh(self, mocked_ai_service):
        mocked_ai_service.return_value = {
            "success": False,
            "source": "fallback",
            "title": "Рекомендации временно недоступны",
            "summary": "Попробуйте позже.",
            "items": [],
            "priority": "medium",
        }

        response = self.http.get("/api/analytics/ai-recommendations/?refresh=true")
        self.assertEqual(response.status_code, 200)
        call_kwargs = mocked_ai_service.call_args.kwargs
        self.assertTrue(call_kwargs["force_refresh"])
