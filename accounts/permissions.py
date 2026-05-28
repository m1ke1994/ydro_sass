from rest_framework import permissions


class IsClientUser(permissions.BasePermission):
    message = "Client dashboard access is available only for active client users."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        client = getattr(user, "client", None)
        if client is None:
            return False
        if not getattr(client, "is_active", False):
            return False

        request.client = client
        return True
