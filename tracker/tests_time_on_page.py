from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from analytics_app.models import Event as AnalyticsEvent
from clients.models import Client
from tracker.models import Event as TrackerEvent
from tracker.models import Site, Visit


class TrackTimeOnPageEventTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="Test Client")
        self.site = Site.objects.create(token=self.client_obj.api_key, domain="test.local", is_active=True)
        self.http = APIClient()

    def test_time_on_page_event_is_stored_for_tracker_and_analytics(self):
        response = self.http.post(
            "/api/track/event/",
            {
                "token": self.client_obj.api_key,
                "session_id": "session-1",
                "visitor_id": "visitor-1",
                "type": "time_on_page",
                "payload": {
                    "page": "/pricing",
                    "duration_seconds": 7,
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(TrackerEvent.objects.filter(type="time_on_page").count(), 1)
        analytics_event = AnalyticsEvent.objects.filter(event_type=AnalyticsEvent.EventType.TIME_ON_PAGE).first()
        self.assertIsNotNone(analytics_event)
        self.assertEqual(analytics_event.duration_seconds, 7)
        self.assertEqual(analytics_event.element_id, "/pricing")
        self.assertEqual(analytics_event.page_url, "https://tracker.local/pricing")

    def test_time_on_page_event_is_ignored_when_duration_is_invalid(self):
        response = self.http.post(
            "/api/track/event/",
            {
                "token": self.client_obj.api_key,
                "session_id": "session-2",
                "visitor_id": "visitor-2",
                "type": "time_on_page",
                "payload": {
                    "page": "/catalog",
                    "duration_seconds": 0,
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("ignored"), True)
        self.assertEqual(TrackerEvent.objects.filter(type="time_on_page").count(), 0)
        self.assertEqual(AnalyticsEvent.objects.filter(event_type=AnalyticsEvent.EventType.TIME_ON_PAGE).count(), 0)

    def test_visit_is_marked_as_bot_for_headless_user_agent(self):
        response = self.http.post(
            "/api/track/visit-start/",
            {
                "token": self.client_obj.api_key,
                "session_id": "bot-session-1",
                "visitor_id": "visitor-bot",
            },
            format="json",
            HTTP_USER_AGENT="Mozilla/5.0 HeadlessChrome/145.0.0.0 Safari/537.36",
        )

        self.assertEqual(response.status_code, 201)
        visit = Visit.objects.get(session_id="bot-session-1")
        self.assertTrue(visit.is_bot)

    def test_visit_is_marked_as_bot_for_empty_user_agent(self):
        response = self.http.post(
            "/api/track/visit-start/",
            {
                "token": self.client_obj.api_key,
                "session_id": "bot-session-empty-ua",
                "visitor_id": "visitor-bot-empty-ua",
            },
            format="json",
            HTTP_USER_AGENT="",
        )

        self.assertEqual(response.status_code, 201)
        visit = Visit.objects.get(session_id="bot-session-empty-ua")
        self.assertTrue(visit.is_bot)

    def test_common_browser_user_agents_are_not_marked_as_bot(self):
        browser_uas = [
            (
                "chrome-session",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            ),
            (
                "safari-session",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            ),
            (
                "edge-session",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            ),
        ]

        for session_id, ua in browser_uas:
            response = self.http.post(
                "/api/track/visit-start/",
                {
                    "token": self.client_obj.api_key,
                    "session_id": session_id,
                    "visitor_id": f"visitor-{session_id}",
                },
                format="json",
                HTTP_USER_AGENT=ua,
            )
            self.assertEqual(response.status_code, 201)

        for session_id, _ in browser_uas:
            visit = Visit.objects.get(session_id=session_id)
            self.assertFalse(visit.is_bot, msg=f"{session_id} was incorrectly marked as bot")
