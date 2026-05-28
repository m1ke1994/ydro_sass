import logging

from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed

from clients.models import Client

logger = logging.getLogger(__name__)


class HasValidApiKey(permissions.BasePermission):
    header_name = "HTTP_X_API_KEY"

    def has_permission(self, request, view):
        if request.method == "OPTIONS":
            return True
        api_key = request.META.get(self.header_name)
        if not api_key:
            api_key = request.query_params.get("api_key")
        if not api_key and request.method in ("POST", "PUT", "PATCH"):
            api_key = request.data.get("api_key")
        if not api_key:
            logger.warning(
                "Public API auth failed: missing api_key path=%s origin=%s",
                request.path,
                request.headers.get("Origin"),
            )
            raise AuthenticationFailed("Отсутствует API-ключ.")
        try:
            client = Client.objects.get(api_key=api_key, is_active=True)
        except Client.DoesNotExist as exc:
            api_key_masked = (api_key[:6] + "***") if isinstance(api_key, str) and len(api_key) >= 6 else "***"
            logger.warning(
                "Public API auth failed: invalid api_key=%s path=%s origin=%s clients_count=%s",
                api_key_masked,
                request.path,
                request.headers.get("Origin"),
                Client.objects.count(),
            )
            raise AuthenticationFailed("Недействительный API-ключ или клиент отключен.") from exc

        api_key_masked = (api_key[:6] + "***") if isinstance(api_key, str) and len(api_key) >= 6 else "***"
        logger.info(
            "Public API auth success: client_id=%s owner_id=%s api_key=%s path=%s",
            client.id,
            client.owner_id,
            api_key_masked,
            request.path,
        )
        request.client = client
        return True
