from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate by email first, then username."""

    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        login = (email or username or "").strip()
        if not login or not password:
            return None

        user = self._get_user_by_email(login) or self._get_user_by_username(login)
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def _get_user_by_email(self, email_value):
        if not email_value:
            return None
        try:
            return User.objects.get(email__iexact=email_value)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            return User.objects.filter(email__iexact=email_value).order_by("id").first()

    def _get_user_by_username(self, username_value):
        if User.USERNAME_FIELD != "username":
            return None
        try:
            return User.objects.get(username__iexact=username_value)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            return User.objects.filter(username__iexact=username_value).order_by("id").first()
