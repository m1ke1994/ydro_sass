from rest_framework import permissions

from subscriptions.access import can_access_client_dashboard


class IsClientUser(permissions.BasePermission):
    message = "Client dashboard access is available only for active client users."

    def has_permission(self, request, view):
        has_access, client = can_access_client_dashboard(request.user, request=request)
        if not has_access or client is None:
            return False

        request.client = client
        return True
