from django.conf import settings
from django.utils import timezone

from clients.models import Client
from subscriptions.models import Subscription


def billing_is_enabled() -> bool:
    return bool(getattr(settings, "ENABLE_BILLING", False))


def _safe_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_superuser_client(request=None):
    requested_id = None
    if request is not None:
        requested_id = (
            getattr(request, "query_params", {}).get("client_id")
            or getattr(request, "data", {}).get("client_id")
            or request.headers.get("X-Client-Id")
        )

    client_id = _safe_int(requested_id)
    if client_id:
        client = Client.objects.filter(id=client_id, is_active=True).first()
        if client is not None:
            return client

    return Client.objects.filter(is_active=True).order_by("id").first()


def can_access_client_dashboard(user, request=None) -> tuple[bool, object | None]:
    if not user or not user.is_authenticated:
        return False, None

    if getattr(user, "is_superuser", False):
        client = _resolve_superuser_client(request=request)
        return (client is not None), client

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
