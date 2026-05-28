import logging
import secrets

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_site_token() -> str:
    return secrets.token_urlsafe(32)


class Site(models.Model):
    token = models.CharField(max_length=128, unique=True, db_index=True, default=generate_site_token)
    domain = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.domain or f"site-{self.pk}"


class Visit(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="visits")
    visitor_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    session_id = models.CharField(max_length=64, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_bot = models.BooleanField(default=False)
    device_type = models.CharField(max_length=20, db_index=True, null=True, blank=True)
    os = models.CharField(max_length=50, null=True, blank=True)
    browser = models.CharField(max_length=50, null=True, blank=True)
    browser_family = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    is_ios_browser = models.BooleanField(default=False)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=["site", "visitor_id", "started_at"]),
            models.Index(fields=["site", "session_id", "started_at"]),
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        logger.info(
            "tracker.visit saved id=%s site_id=%s visitor_id=%s session_id=%s new=%s is_bot=%s duration=%s",
            self.pk,
            self.site_id,
            self.visitor_id,
            self.session_id,
            is_new,
            self.is_bot,
            self.duration,
        )


class PageView(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="pageviews")
    url = models.TextField()
    title = models.CharField(max_length=512, blank=True, default="")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-timestamp",)


class Event(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="events")
    type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-timestamp",)
