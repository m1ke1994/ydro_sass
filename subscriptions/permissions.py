from django.utils import timezone
from rest_framework import permissions

from subscriptions.exceptions import PaymentRequired
from subscriptions.models import Subscription


def has_active_subscription(client) -> bool:
    if Subscription.objects.filter(client=client, admin_override=True).exists():
        return True

    subscription = Subscription.objects.filter(
        client=client,
        status=Subscription.Status.ACTIVE,
        paid_until__gt=timezone.now(),
    ).first()
    return bool(subscription)


class HasActiveSubscription(permissions.BasePermission):
    message = "Подписка не активна."

    def has_permission(self, request, view):
        client = getattr(request, "client", None)
        if client is None:
            return True

        if has_active_subscription(client):
            return True

        raise PaymentRequired()
