import logging

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import RegisterResponseSerializer, RegisterSerializer
from subscriptions.access import can_access_client_dashboard

logger = logging.getLogger(__name__)


def _format_errors(errors):
    return {"errors": errors}


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [JSONRenderer]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Register validation failed: %s", serializer.errors)
            return Response(_format_errors(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

        user, client = serializer.save()
        response_serializer = RegisterResponseSerializer(
            {
                "user_id": user.id,
                "email": user.email,
                "client_id": client.id,
                "company_name": client.name,
                "api_key": client.api_key,
            }
        )
        tokens = RefreshToken.for_user(user)
        return Response(
            {
                "user": response_serializer.data,
                "tokens": {
                    "access": str(tokens.access_token),
                    "refresh": str(tokens),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [JSONRenderer]

    def post(self, request, *args, **kwargs):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""

        validation_errors = {}
        if not email:
            validation_errors["email"] = ["Email is required."]
        if not password:
            validation_errors["password"] = ["Password is required."]
        if validation_errors:
            logger.warning("Login validation failed: %s", validation_errors)
            return Response(_format_errors(validation_errors), status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request=request, username=email, password=password)
        if user is None:
            logger.warning("Login failed: invalid credentials for email=%s", email)
            return Response(
                _format_errors({"non_field_errors": ["Invalid email or password."]}),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        has_dashboard_access, client = can_access_client_dashboard(user)
        if not has_dashboard_access or client is None:
            logger.warning("Login failed: inactive client for email=%s", email)
            return Response(
                _format_errors({"non_field_errors": ["Client cabinet access is disabled."]}),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(tokens.access_token),
                "refresh": str(tokens),
                "email": user.email,
                "client_id": client.id,
            },
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def post(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get("current_password") or ""
        new_password = request.data.get("new_password") or ""

        validation_errors = {}
        if not current_password:
            validation_errors["current_password"] = ["Current password is required."]
        if not new_password:
            validation_errors["new_password"] = ["New password is required."]
        if validation_errors:
            return Response(_format_errors(validation_errors), status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({"error": "Current password is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            return Response(_format_errors({"new_password": list(exc.messages)}), status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"success": True}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def post(self, request, *args, **kwargs):
        return Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
