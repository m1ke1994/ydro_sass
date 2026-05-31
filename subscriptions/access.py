from django.conf import settings
from django.utils import timezone

from subscriptions.models import Subscription


def billing_is_enabled() -> bool:
    return bool(getattr(settings, "ENABLE_BILLING", False))


def can_access_client_dashboard(user) -> tuple[bool, object | None]:
    if not user or not user.is_authenticated:
        return False, None

    client = getattr(user, "client", None)
    if client is None:
        return False, None
    if not getattr(client, "is_active", False):
        return False, client
    return True, client


def has_active_subscription(client) -> bool:
    if client is None:
        return False
    if not billing_is_enabled():
        return True

    if Subscription.objects.filter(client=client, admin_override=True).exists():
        return True

    subscription = Subscription.objects.filter(
        client=client,
        status=Subscription.Status.ACTIVE,
        paid_until__gt=timezone.now(),
    ).first()
    return bool(subscription)
