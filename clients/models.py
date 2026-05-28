import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils.html import escape


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


class Client(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client",
        verbose_name="Owner",
    )
    name = models.CharField(max_length=255, verbose_name="Client name")
    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        editable=False,
        verbose_name="Client UUID",
    )
    api_key = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        editable=False,
        verbose_name="API key",
    )
    telegram_chat_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="Telegram chat ID",
    )
    send_to_telegram = models.BooleanField(
        default=False,
        verbose_name="Send leads to Telegram",
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = generate_api_key()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.owner.email})"

    @property
    def tracker_script_url(self) -> str:
        base_url = getattr(settings, "PUBLIC_BASE_URL", "").rstrip("/")
        if base_url:
            return f"{base_url}/api/mini/tracker.js"
        # Local/dev safe default so client installs always get an absolute URL.
        if getattr(settings, "DEBUG", False):
            return "http://localhost:9000/api/mini/tracker.js"
        return "/api/mini/tracker.js"

    @property
    def public_script_tag(self) -> str:
        api_key = escape(self.api_key)
        script_url = escape(self.tracker_script_url)
        return f'<script src="{script_url}" data-api-key="{api_key}"></script>'
