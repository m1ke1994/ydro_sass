from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.sites.models import Site as CoreSite
from clients.models import Client
from tracker.models import Site as TrackerSite, Visit


class TrackerSiteTokenResolutionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="tracker-owner@example.com",
            email="tracker-owner@example.com",
            password="test-test-123",
        )
        self.client_obj = Client.objects.create(owner=self.owner, name="Tracker Client", is_active=True)
        self.site = CoreSite.objects.create(
            name="A Meditation / Амедиа",
            slug="a-meditation",
            domain="localhost",
            owner=self.owner,
            is_active=True,
        )
        self.api = APIClient()

    def test_visit_start_accepts_core_site_api_key_and_creates_tracker_site(self):
        payload = {
            "token": self.site.api_key,
            "visitor_id": "visitor-1",
            "session_id": "session-1",
        }
        response = self.api.post("/api/mini/track/visit-start/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["ok"])

        tracker_site = TrackerSite.objects.filter(token=self.site.api_key).first()
        self.assertIsNotNone(tracker_site)
        self.assertTrue(Visit.objects.filter(site=tracker_site, session_id="session-1").exists())
