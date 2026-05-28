from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from analytics_app.views import _build_ai_event_signals_payload
from clients.models import Client
from tracker.models import Event as TrackerEvent
from tracker.models import Site, Visit


class AiSignalsPayloadTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="AI Signal Client")
        self.site = Site.objects.create(token=self.client_obj.api_key, domain="test.local", is_active=True)
        self.visit = Visit.objects.create(
            site=self.site,
            session_id="session-ai-payload",
            visitor_id="visitor-ai-payload",
            started_at=timezone.now(),
        )

    def _build_payload(self, now):
        return _build_ai_event_signals_payload(
            client=self.client_obj,
            from_dt=now - timedelta(days=1),
            to_dt=now + timedelta(days=1),
        )

    def test_ai_signal_payload_aggregates_stage_one_events(self):
        now = timezone.now()
        TrackerEvent.objects.bulk_create(
            [
                TrackerEvent(
                    visit=self.visit,
                    type="scroll_depth",
                    payload={"depth": 25},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="scroll_depth",
                    payload={"depth": 80},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="form_view",
                    payload={},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="form_start",
                    payload={},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="form_first_field_filled",
                    payload={},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="form_submit_attempt",
                    payload={},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="form_submit_success",
                    payload={},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="form_submit_error",
                    payload={},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="section_view",
                    payload={"section_key": "hero"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="cta_click",
                    payload={"cta_key": "hero_cta"},
                    timestamp=now,
                ),
            ]
        )

        payload = self._build_payload(now)

        self.assertEqual(payload["scroll_depth"]["events_total"], 2)
        self.assertEqual(payload["scroll_depth"]["unique_users_total"], 1)
        self.assertEqual(payload["scroll_depth"]["avg_scroll_depth"], 80.0)
        self.assertEqual(payload["scroll_depth"]["thresholds"]["25"], 1)
        self.assertEqual(payload["scroll_depth"]["thresholds"]["50"], 1)
        self.assertEqual(payload["scroll_depth"]["thresholds"]["75"], 1)
        self.assertEqual(payload["scroll_depth"]["thresholds"]["100"], 0)
        self.assertEqual(payload["scroll_depth"]["threshold_rates_pct"]["25"], 100.0)
        self.assertEqual(payload["scroll_depth"]["threshold_rates_pct"]["75"], 100.0)
        self.assertEqual(payload["scroll_depth"]["threshold_rates_pct"]["100"], 0.0)
        self.assertEqual(payload["scroll_depth"]["threshold_event_counts"]["25"], 1)
        self.assertEqual(payload["scroll_depth"]["threshold_event_counts"]["75"], 1)
        self.assertEqual(payload["forms"]["form_view"], 1)
        self.assertEqual(payload["forms"]["form_start"], 1)
        self.assertEqual(payload["forms"]["form_first_field_filled"], 1)
        self.assertEqual(payload["forms"]["form_submit_attempt"], 1)
        self.assertEqual(payload["forms"]["form_submit_success"], 1)
        self.assertEqual(payload["forms"]["form_submit_error"], 1)
        self.assertEqual(payload["forms"]["form_visible"], 1)
        self.assertEqual(payload["forms"]["form_started"], 1)
        self.assertEqual(payload["forms"]["form_first_field_completed"], 1)
        self.assertEqual(payload["section_views"]["events_total"], 1)
        self.assertEqual(payload["cta_clicks"]["events_total"], 1)

    def test_ai_signal_payload_includes_extended_ai_blocks(self):
        now = timezone.now()
        self.visit.device_type = "mobile"
        self.visit.referrer = "https://google.com"
        self.visit.save(update_fields=["device_type", "referrer"])

        TrackerEvent.objects.bulk_create(
            [
                TrackerEvent(
                    visit=self.visit,
                    type="scroll_depth",
                    payload={"depth": 60},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="form_visible",
                    payload={"form_id": "lead_form"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="form_started",
                    payload={"form_id": "lead_form"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="form_first_field_completed",
                    payload={"form_id": "lead_form"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="field_input_started",
                    payload={"form_id": "lead_form", "field_name": "name", "field_type": "text"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="field_completed",
                    payload={"form_id": "lead_form", "field_name": "name", "field_type": "text"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="field_error",
                    payload={"form_id": "lead_form", "field_name": "phone", "field_type": "tel"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="field_revisit",
                    payload={"form_id": "lead_form", "field_name": "phone", "field_type": "tel"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="cta_visible",
                    payload={"cta_id": "hero_cta", "cta_text": "Оставить заявку", "cta_type": "hero"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="cta_click",
                    payload={"cta_id": "hero_cta", "cta_text": "Оставить заявку", "cta_type": "hero"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="cta_target_reached",
                    payload={"cta_id": "hero_cta"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="cta_converted",
                    payload={"cta_id": "hero_cta"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="section_visible",
                    payload={"section_id": "hero"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="section_time_spent",
                    payload={"section_id": "hero", "visible_duration_seconds": 9},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="section_interaction_after_view",
                    payload={"section_id": "hero", "interaction_type": "cta_click"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="section_conversion_after_view",
                    payload={"section_id": "hero"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="phone_click",
                    payload={"section_id": "contacts", "page_url": "https://test.local/"},
                    timestamp=now,
                ),
            ]
        )

        payload = self._build_payload(now)

        self.assertIn("overview", payload)
        self.assertIn("form_funnel", payload)
        self.assertIn("field_analytics", payload)
        self.assertIn("cta_funnel", payload)
        self.assertIn("section_analytics", payload)
        self.assertIn("device_segmentation", payload)
        self.assertIn("source_segmentation", payload)
        self.assertIn("micro_conversions", payload)
        self.assertIn("anomalies", payload)

        self.assertGreaterEqual(len(payload["form_funnel"]["rows"]), 6)
        self.assertEqual(len(payload["field_analytics"]["rows"]), 2)
        self.assertEqual(payload["field_analytics"]["summary"]["form_started_users"], 1)
        self.assertEqual(payload["field_analytics"]["summary"]["first_field_completed_users"], 1)
        self.assertEqual(payload["field_analytics"]["summary"]["field_error_users"], 1)
        self.assertEqual(len(payload["cta_funnel"]["rows"]), 1)
        self.assertEqual(len(payload["section_analytics"]["rows"]), 1)
        self.assertEqual(len(payload["device_segmentation"]["rows"]), 4)
        self.assertEqual(len(payload["source_segmentation"]["rows"]), 7)
        self.assertEqual(payload["micro_conversions"]["rows"][0]["event"], "phone_click")
        self.assertEqual(payload["micro_conversions"]["rows"][0]["label"], "Клик по телефону")
        self.assertEqual(len(payload["anomalies"]["rows"]), 6)

    def test_scroll_thresholds_count_unique_user_once(self):
        now = timezone.now()
        TrackerEvent.objects.bulk_create(
            [
                TrackerEvent(visit=self.visit, type="scroll_depth", payload={"depth": 10}, timestamp=now),
                TrackerEvent(visit=self.visit, type="scroll_depth", payload={"depth": 30}, timestamp=now),
                TrackerEvent(visit=self.visit, type="scroll_depth", payload={"depth": 55}, timestamp=now),
                TrackerEvent(visit=self.visit, type="scroll_depth", payload={"depth": 90}, timestamp=now),
                TrackerEvent(visit=self.visit, type="scroll_depth", payload={"depth": 100}, timestamp=now),
                TrackerEvent(visit=self.visit, type="scroll_depth", payload={"depth": 100}, timestamp=now),
            ]
        )

        payload = self._build_payload(now)

        self.assertEqual(payload["scroll_depth"]["events_total"], 6)
        self.assertEqual(payload["scroll_depth"]["unique_users_total"], 1)
        self.assertEqual(payload["scroll_depth"]["threshold_users"]["25"], 1)
        self.assertEqual(payload["scroll_depth"]["threshold_users"]["50"], 1)
        self.assertEqual(payload["scroll_depth"]["threshold_users"]["75"], 1)
        self.assertEqual(payload["scroll_depth"]["threshold_users"]["100"], 1)
        self.assertEqual(payload["scroll_depth"]["threshold_rates_pct"]["100"], 100.0)

    def test_scroll_depth_uses_unique_users_not_sessions_for_rates(self):
        now = timezone.now()
        visitor_depths = {
            "u1": 100,
            "u2": 80,
            "u3": 60,
            "u4": 30,
            "u5": 10,
        }

        visits = []
        for idx in range(100):
            visitor_id = f"visitor-{(idx % 5) + 1}"
            visits.append(
                Visit(
                    site=self.site,
                    session_id=f"mass-session-{idx}",
                    visitor_id=visitor_id,
                    started_at=now,
                )
            )
        Visit.objects.bulk_create(visits)
        mass_visits = list(Visit.objects.filter(site=self.site, session_id__startswith="mass-session-"))

        events = []
        for visit in mass_visits:
            depth = visitor_depths[f"u{visit.visitor_id.split('-')[-1]}"]
            events.append(TrackerEvent(visit=visit, type="scroll_depth", payload={"depth": depth}, timestamp=now))
        TrackerEvent.objects.bulk_create(events)

        payload = self._build_payload(now)

        self.assertEqual(payload["scroll_depth"]["events_total"], 100)
        self.assertEqual(payload["scroll_depth"]["unique_users_total"], 5)
        self.assertEqual(payload["scroll_depth"]["threshold_users"]["25"], 4)
        self.assertEqual(payload["scroll_depth"]["threshold_users"]["50"], 3)
        self.assertEqual(payload["scroll_depth"]["threshold_users"]["75"], 2)
        self.assertEqual(payload["scroll_depth"]["threshold_users"]["100"], 1)
        self.assertEqual(payload["scroll_depth"]["threshold_rates_pct"]["25"], 80.0)
        self.assertEqual(payload["scroll_depth"]["threshold_rates_pct"]["50"], 60.0)
        self.assertEqual(payload["scroll_depth"]["threshold_rates_pct"]["75"], 40.0)
        self.assertEqual(payload["scroll_depth"]["threshold_rates_pct"]["100"], 20.0)

    def test_micro_conversions_include_label_and_unique_users(self):
        now = timezone.now()
        extra_visit = Visit.objects.create(
            site=self.site,
            session_id="session-extra",
            visitor_id="visitor-extra",
            started_at=now,
        )
        TrackerEvent.objects.bulk_create(
            [
                TrackerEvent(
                    visit=self.visit,
                    type="phone_click",
                    payload={"section_id": "contacts", "page_url": "https://test.local/"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="phone_click",
                    payload={"section_id": "contacts", "page_url": "https://test.local/"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=extra_visit,
                    type="phone_click",
                    payload={"section_id": "contacts", "page_url": "https://test.local/"},
                    timestamp=now,
                ),
                TrackerEvent(
                    visit=self.visit,
                    type="map_open",
                    payload={"section_id": "contacts", "page_url": "https://test.local/contacts"},
                    timestamp=now,
                ),
            ]
        )

        payload = self._build_payload(now)
        phone_row = next((item for item in payload["micro_conversions"]["rows"] if item["event"] == "phone_click"), None)

        self.assertIsNotNone(phone_row)
        self.assertEqual(phone_row["label"], "Клик по телефону")
        self.assertEqual(phone_row["count"], 3)
        self.assertEqual(phone_row["unique_users"], 2)
        self.assertEqual(payload["overview"]["micro_conversion_users"], 2)

    def test_anomalies_mark_insufficient_base_data(self):
        now = timezone.now()
        TrackerEvent.objects.create(
            visit=self.visit,
            type="cta_click",
            payload={"cta_id": "hero_cta"},
            timestamp=now,
        )

        payload = self._build_payload(now)

        self.assertIn("anomalies", payload)
        self.assertFalse(payload["anomalies"]["has_data"])
        self.assertFalse(payload["anomalies"]["has_comparable_data"])
        self.assertTrue(payload["anomalies"]["insufficient_data"])
        self.assertEqual(payload["anomalies"]["display_mode"], "compact")
        self.assertTrue(bool(payload["anomalies"]["insufficient_data_reason"]))
