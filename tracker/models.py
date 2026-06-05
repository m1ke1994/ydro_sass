import logging
import secrets

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_site_token() -> str:
    return secrets.token_urlsafe(32)


class Site(models.Model):
    token = models.CharField(max_length=128, unique=True, db_index=True, default=generate_site_token, verbose_name="Токен")
    domain = models.CharField(max_length=255, blank=True, default="", verbose_name="Домен")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Сайт трекера"
        verbose_name_plural = "Сайты трекера"

    def __str__(self) -> str:
        return self.domain or f"site-{self.pk}"


class Visit(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="visits", verbose_name="Сайт")
    visitor_id = models.CharField(max_length=64, blank=True, default="", db_index=True, verbose_name="ID посетителя")
    session_id = models.CharField(max_length=64, db_index=True, verbose_name="ID сессии")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP-адрес")
    is_bot = models.BooleanField(default=False, verbose_name="Бот")
    device_type = models.CharField(max_length=20, db_index=True, null=True, blank=True, verbose_name="Устройство")
    os = models.CharField(max_length=50, null=True, blank=True, verbose_name="ОС")
    browser = models.CharField(max_length=50, null=True, blank=True, verbose_name="Браузер")
    browser_family = models.CharField(max_length=50, db_index=True, null=True, blank=True, verbose_name="Семейство браузера")
    is_ios_browser = models.BooleanField(default=False, verbose_name="iOS-браузер")
    user_agent = models.TextField(null=True, blank=True, verbose_name="User-Agent")
    referrer = models.TextField(blank=True, default="", verbose_name="Источник перехода")
    started_at = models.DateTimeField(default=timezone.now, verbose_name="Начало визита")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Окончание визита")
    duration = models.PositiveIntegerField(default=0, verbose_name="Длительность (сек)")

    class Meta:
        ordering = ("-started_at",)
        verbose_name = "Визит трекера"
        verbose_name_plural = "Визиты трекера"
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
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="pageviews", verbose_name="Визит")
    url = models.TextField(verbose_name="URL")
    title = models.CharField(max_length=512, blank=True, default="", verbose_name="Заголовок страницы")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Время просмотра")

    class Meta:
        ordering = ("-timestamp",)
        verbose_name = "Просмотр страницы трекера"
        verbose_name_plural = "Просмотры страниц трекера"


class Event(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="events", verbose_name="Визит")
    type = models.CharField(max_length=64, verbose_name="Тип события")
    payload = models.JSONField(default=dict, blank=True, verbose_name="Данные события")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Время события")

    class Meta:
        ordering = ("-timestamp",)
        verbose_name = "Событие трекера"
        verbose_name_plural = "События трекера"
