from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import PageView, TrackingEvent, Visit
from apps.sites.models import Site


class AnalyticsApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="owner-analytics",
            email="owner.analytics@example.com",
            password="test-test",
        )
        self.other_user = user_model.objects.create_user(
            username="other-owner",
            email="other.owner@example.com",
            password="test-test",
        )
        self.site = Site.objects.create(
            name="Analytics Site",
            slug="analytics-site",
            domain="localhost",
            owner=self.user,
            is_active=True,
        )
        self.other_site = Site.objects.create(
            name="Foreign Site",
            slug="foreign-site",
            domain="localhost",
            owner=self.other_user,
            is_active=True,
        )

    def test_public_tracking_endpoints_create_data(self):
        visit_start_url = reverse("track-visit-start")
        pageview_url = reverse("track-pageview")
        event_url = reverse("track-event")
        visit_end_url = reverse("track-visit-end")

        payload_base = {
            "token": self.site.api_key,
            "session_id": "session-1",
            "visitor_id": "visitor-1",
        }

        start_response = self.client.post(
            visit_start_url,
            {**payload_base, "referrer": "https://google.com"},
            format="json",
        )
        self.assertEqual(start_response.status_code, status.HTTP_201_CREATED)

        pageview_response = self.client.post(
            pageview_url,
            {**payload_base, "url": "http://localhost:5173/", "title": "Home"},
            format="json",
        )
        self.assertEqual(pageview_response.status_code, status.HTTP_201_CREATED)

        event_response = self.client.post(
            event_url,
            {**payload_base, "type": "click", "payload": {"target": "button"}},
            format="json",
        )
        self.assertEqual(event_response.status_code, status.HTTP_201_CREATED)

        end_response = self.client.post(
            visit_end_url,
            {**payload_base, "duration": 42},
            format="json",
        )
        self.assertEqual(end_response.status_code, status.HTTP_200_OK)

        self.assertEqual(Visit.objects.filter(site=self.site).count(), 1)
        self.assertEqual(PageView.objects.filter(visit__site=self.site).count(), 1)
        self.assertEqual(TrackingEvent.objects.filter(visit__site=self.site).count(), 1)

    def test_owner_can_view_own_analytics_summary_only(self):
        Visit.objects.create(site=self.site, session_id="s1", visitor_id="v1")
        self.client.force_authenticate(user=self.user)

        own_url = reverse("admin-site-analytics-summary", kwargs={"site_id": self.site.id})
        own_response = self.client.get(own_url)
        self.assertEqual(own_response.status_code, status.HTTP_200_OK)
        self.assertEqual(own_response.data["visit_count"], 1)

        foreign_url = reverse("admin-site-analytics-summary", kwargs={"site_id": self.other_site.id})
        foreign_response = self.client.get(foreign_url)
        self.assertEqual(foreign_response.status_code, status.HTTP_404_NOT_FOUND)
