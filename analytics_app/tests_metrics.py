from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from analytics_app.models import Event
from analytics_app.services.metrics import get_metrics
from clients.models import Client
from leads.models import Lead
from tracker.models import Event as TrackerEvent
from tracker.models import Site, Visit


class MetricsServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="owner", email="owner@example.com", password="pass12345")
        self.client_obj = Client.objects.create(owner=self.user, name="Test Client")
        self.site = Site.objects.create(token=self.client_obj.api_key, domain="test.local", is_active=True)
        self.date_to = timezone.localdate()
        self.date_from = self.date_to - timedelta(days=1)

    def _visit(self, session_id, visitor_id, is_bot=False):
        return Visit.objects.create(
            site=self.site,
            session_id=session_id,
            visitor_id=visitor_id,
            is_bot=is_bot,
            started_at=timezone.now(),
        )

    def test_single_visitor_multiple_visits(self):
        for idx in range(8):
            self._visit(session_id=f"session-{idx}", visitor_id="visitor-1")

        metrics = get_metrics(self.client_obj, self.date_from, self.date_to)
        self.assertEqual(metrics["visits"], 8)
        self.assertEqual(metrics["unique_users"], 1)

    def test_two_visitors_total_eight_visits(self):
        for idx in range(5):
            self._visit(session_id=f"session-a-{idx}", visitor_id="visitor-a")
        for idx in range(3):
            self._visit(session_id=f"session-b-{idx}", visitor_id="visitor-b")

        metrics = get_metrics(self.client_obj, self.date_from, self.date_to)
        self.assertEqual(metrics["visits"], 8)
        self.assertEqual(metrics["unique_users"], 2)

    def test_conversion_and_legacy_missing_visitor_id(self):
        for idx in range(2):
            self._visit(session_id=f"legacy-{idx}", visitor_id="")
        Event.objects.create(
            client=self.client_obj,
            visitor_id="",
            event_type=Event.EventType.FORM_SUBMIT,
            element_id="contact-form",
            page_url="https://test.local/",
        )
        Lead.objects.create(client=self.client_obj, name="Lead One")

        metrics = get_metrics(self.client_obj, self.date_from, self.date_to)
        self.assertEqual(metrics["visits"], 2)
        self.assertEqual(metrics["unique_users"], 2)
        self.assertEqual(metrics["forms"], 1)
        self.assertEqual(metrics["leads"], 1)
        self.assertEqual(metrics["conversion"], 50.0)

    def test_conversion_uses_form_submit_when_leads_absent(self):
        for idx in range(5):
            self._visit(session_id=f"session-{idx}", visitor_id=f"visitor-{idx}")
        for idx in range(2):
            Event.objects.create(
                client=self.client_obj,
                visitor_id=f"visitor-{idx}",
                event_type=Event.EventType.FORM_SUBMIT,
                element_id=f"form-{idx}",
                page_url="https://test.local/contact",
            )

        metrics = get_metrics(self.client_obj, self.date_from, self.date_to)
        self.assertEqual(metrics["visits"], 5)
        self.assertEqual(metrics["forms"], 2)
        self.assertEqual(metrics["leads"], 0)
        self.assertEqual(metrics["conversion"], 40.0)

    def test_conversion_falls_back_to_leads_when_forms_absent(self):
        for idx in range(4):
            self._visit(session_id=f"session-{idx}", visitor_id=f"visitor-{idx}")
        for idx in range(2):
            Lead.objects.create(client=self.client_obj, name=f"Lead {idx + 1}")

        metrics = get_metrics(self.client_obj, self.date_from, self.date_to)
        self.assertEqual(metrics["visits"], 4)
        self.assertEqual(metrics["forms"], 0)
        self.assertEqual(metrics["leads"], 2)
        self.assertEqual(metrics["conversion"], 50.0)

    def test_notifications_sent_count_tracks_successful_telegram_dispatch(self):
        visit_ok = self._visit(session_id="notify-1", visitor_id="visitor-1")
        visit_fail = self._visit(session_id="notify-2", visitor_id="visitor-2")
        visit_other = self._visit(session_id="notify-3", visitor_id="visitor-3")

        TrackerEvent.objects.create(
            visit=visit_ok,
            type="form_submit",
            payload={"telegram_notified": True},
            timestamp=timezone.now(),
        )
        TrackerEvent.objects.create(
            visit=visit_fail,
            type="form_submit",
            payload={"telegram_notified": False},
            timestamp=timezone.now(),
        )
        TrackerEvent.objects.create(
            visit=visit_other,
            type="click",
            payload={"telegram_notified": True},
            timestamp=timezone.now(),
        )

        metrics = get_metrics(self.client_obj, self.date_from, self.date_to)
        self.assertEqual(metrics["notifications_sent"], 1)

    def test_time_on_page_metrics_are_aggregated(self):
        for idx in range(3):
            self._visit(session_id=f"time-{idx}", visitor_id=f"visitor-{idx}")

        Event.objects.create(
            client=self.client_obj,
            visitor_id="visitor-1",
            event_type=Event.EventType.TIME_ON_PAGE,
            page_url="https://test.local/",
            duration_seconds=20,
        )
        Event.objects.create(
            client=self.client_obj,
            visitor_id="visitor-2",
            event_type=Event.EventType.TIME_ON_PAGE,
            page_url="https://test.local/catalog",
            duration_seconds=40,
        )
        Event.objects.create(
            client=self.client_obj,
            visitor_id="visitor-3",
            event_type=Event.EventType.TIME_ON_PAGE,
            page_url="https://test.local/catalog",
            duration_seconds=60,
        )

        metrics = get_metrics(self.client_obj, self.date_from, self.date_to)
        self.assertEqual(metrics["time_on_page_events"], 3)
        self.assertEqual(metrics["total_time_on_site_seconds"], 120)
        self.assertEqual(metrics["avg_visit_duration_seconds"], 40)

    def test_bot_visits_are_excluded_from_visits_and_unique_counts(self):
        self._visit(session_id="human-1", visitor_id="visitor-1", is_bot=False)
        self._visit(session_id="human-2", visitor_id="", is_bot=False)
        self._visit(session_id="bot-1", visitor_id="visitor-bot", is_bot=True)
        self._visit(session_id="bot-2", visitor_id="", is_bot=True)

        metrics = get_metrics(self.client_obj, self.date_from, self.date_to)
        self.assertEqual(metrics["visits"], 2)
        self.assertEqual(metrics["unique_users"], 2)
