from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from analytics_app.models import PageView as AnalyticsPageView
from clients.models import Client
from tracker.models import Site


class TrackAiEventsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="AI Analytics Client")
        self.site = Site.objects.create(token=self.client_obj.api_key, domain="test.local", is_active=True)
        self.http = APIClient()
        self.session_id = "session-ai-1"
        self.visitor_id = "visitor-ai-1"

        self.http.post(
            "/api/track/pageview/",
            {
                "token": self.client_obj.api_key,
                "session_id": self.session_id,
                "visitor_id": self.visitor_id,
                "url": "https://test.local/landing",
                "title": "Landing",
            },
            format="json",
        )

    def test_scroll_depth_updates_latest_analytics_page_view(self):
        self.http.post(
            "/api/track/event/",
            {
                "token": self.client_obj.api_key,
                "session_id": self.session_id,
                "visitor_id": self.visitor_id,
                "type": "scroll_depth",
                "payload": {"depth": 50, "path": "/landing"},
            },
            format="json",
        )
        self.http.post(
            "/api/track/event/",
            {
                "token": self.client_obj.api_key,
                "session_id": self.session_id,
                "visitor_id": self.visitor_id,
                "type": "scroll_depth",
                "payload": {"depth": 75, "path": "/landing"},
            },
            format="json",
        )
        self.http.post(
            "/api/track/event/",
            {
                "token": self.client_obj.api_key,
                "session_id": self.session_id,
                "visitor_id": self.visitor_id,
                "type": "scroll_depth",
                "payload": {"depth": 25, "path": "/landing"},
            },
            format="json",
        )

        latest_page_view = (
            AnalyticsPageView.objects.filter(client=self.client_obj, session_id=self.session_id)
            .order_by("-created_at")
            .first()
        )
        self.assertIsNotNone(latest_page_view)
        self.assertEqual(latest_page_view.max_scroll_depth, 75)
