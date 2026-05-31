from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from clients.models import Client
from subscriptions.access import has_active_subscription
from subscriptions.models import Subscription


class BillingAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="billing-user@example.com",
            email="billing-user@example.com",
            password="test-pass-123",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="Billing Client", is_active=True)
        self.subscription = Subscription.objects.create(
            client=self.client_obj,
            status=Subscription.Status.EXPIRED,
            paid_until=timezone.now() - timedelta(days=1),
            is_trial=False,
            admin_override=False,
        )

    @override_settings(ENABLE_BILLING=False)
    def test_has_active_subscription_is_bypassed_when_billing_disabled(self):
        self.assertTrue(has_active_subscription(self.client_obj))

    @override_settings(ENABLE_BILLING=True)
    def test_has_active_subscription_requires_valid_subscription_when_billing_enabled(self):
        self.assertFalse(has_active_subscription(self.client_obj))

        self.subscription.status = Subscription.Status.ACTIVE
        self.subscription.paid_until = timezone.now() + timedelta(days=3)
        self.subscription.save(update_fields=["status", "paid_until", "updated_at"])
        self.assertTrue(has_active_subscription(self.client_obj))

    @override_settings(ENABLE_BILLING=False)
    def test_subscription_status_view_exposes_billing_flag(self):
        api = APIClient()
        api.force_authenticate(user=self.user)
        response = api.get("/api/mini/subscription/status/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("billing_enabled", response.data)
        self.assertFalse(response.data["billing_enabled"])

    @override_settings(ENABLE_BILLING=True)
    def test_subscription_gated_endpoint_is_blocked_when_billing_enabled(self):
        api = APIClient()
        api.force_authenticate(user=self.user)
        response = api.get("/api/mini/leads/")
        self.assertEqual(response.status_code, 402)

    @override_settings(ENABLE_BILLING=False)
    def test_superuser_can_access_client_endpoints_with_client_switch(self):
        user_model = get_user_model()
        superuser = user_model.objects.create_superuser(
            username="billing-admin",
            email="billing-admin@example.com",
            password="test-pass-123",
        )
        api = APIClient()
        api.force_authenticate(user=superuser)
        response = api.get(f"/api/mini/client/settings/?client_id={self.client_obj.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.client_obj.id)
