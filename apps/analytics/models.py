from django.db import models
from django.utils import timezone

from apps.sites.models import Site


class Visit(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="visits", verbose_name="Сайт")
    visitor_id = models.CharField(max_length=64, blank=True, default="", db_index=True, verbose_name="Visitor ID")
    session_id = models.CharField(max_length=64, db_index=True, verbose_name="Session ID")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.TextField(blank=True, default="", verbose_name="User-Agent")
    referrer = models.TextField(blank=True, default="", verbose_name="Referrer")
    started_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Начало визита")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Окончание визита")
    duration = models.PositiveIntegerField(default=0, verbose_name="Длительность (сек)")

    class Meta:
        ordering = ("-started_at",)
        verbose_name = "Визит"
        verbose_name_plural = "Визиты"
        indexes = [
            models.Index(fields=["site", "session_id", "started_at"]),
            models.Index(fields=["site", "visitor_id", "started_at"]),
        ]

    def __str__(self):
        return f"{self.site.slug} / {self.session_id}"


class PageView(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="pageviews", verbose_name="Визит")
    url = models.TextField(verbose_name="URL")
    pathname = models.CharField(max_length=512, db_index=True, blank=True, default="", verbose_name="Pathname")
    title = models.CharField(max_length=512, blank=True, default="", verbose_name="Заголовок страницы")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Время просмотра")

    class Meta:
        ordering = ("-timestamp",)
        verbose_name = "Просмотр страницы"
        verbose_name_plural = "Просмотры страниц"
        indexes = [models.Index(fields=["visit", "timestamp"])]


class TrackingEvent(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="events", verbose_name="Визит")
    type = models.CharField(max_length=64, verbose_name="Тип события")
    payload = models.JSONField(default=dict, blank=True, verbose_name="Payload")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Время события")

    class Meta:
        ordering = ("-timestamp",)
        verbose_name = "Событие"
        verbose_name_plural = "События"
        indexes = [models.Index(fields=["visit", "type", "timestamp"])]

