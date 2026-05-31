from rest_framework import permissions

from subscriptions.access import has_active_subscription
from subscriptions.exceptions import PaymentRequired


class HasActiveSubscription(permissions.BasePermission):
    message = "Подписка не активна."

    def has_permission(self, request, view):
        client = getattr(request, "client", None)
        if client is None:
            return True

        if has_active_subscription(client):
            return True

        raise PaymentRequired()
