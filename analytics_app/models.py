from django.db import models

from clients.models import Client


class Event(models.Model):
    class EventType(models.TextChoices):
        VISIT = "visit", "Visit"
        CLICK = "click", "Click"
        FORM_SUBMIT = "form_submit", "Form submit"
        TIME_ON_PAGE = "time_on_page", "Time on page"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="events", verbose_name="Client")
    visitor_id = models.CharField(max_length=64, blank=True, default="", db_index=True, verbose_name="Visitor ID")
    event_type = models.CharField(max_length=20, choices=EventType.choices, verbose_name="Event type")
    element_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="Element ID")
    page_url = models.URLField(max_length=1000, verbose_name="Page URL")
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name="Duration (sec)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Event"
        verbose_name_plural = "Events"
        indexes = [
            models.Index(fields=["client", "event_type", "created_at"]),
            models.Index(fields=["client", "visitor_id", "created_at"]),
        ]


class PageView(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="page_views", verbose_name="Client")
    visitor_id = models.CharField(max_length=64, blank=True, default="", db_index=True, verbose_name="Visitor ID")
    session_id = models.CharField(max_length=64, db_index=True, verbose_name="Session ID")
    url = models.URLField(max_length=1000, verbose_name="Page URL")
    pathname = models.CharField(max_length=512, db_index=True, verbose_name="Pathname")
    query_string = models.TextField(blank=True, null=True, verbose_name="Query string")
    referrer = models.URLField(max_length=1000, blank=True, null=True, verbose_name="Referrer")
    utm_source = models.CharField(max_length=255, blank=True, null=True, verbose_name="UTM Source")
    utm_medium = models.CharField(max_length=255, blank=True, null=True, verbose_name="UTM Medium")
    utm_campaign = models.CharField(max_length=255, blank=True, null=True, verbose_name="UTM Campaign")
    utm_term = models.CharField(max_length=255, blank=True, null=True, verbose_name="UTM Term")
    utm_content = models.CharField(max_length=255, blank=True, null=True, verbose_name="UTM Content")
    max_scroll_depth = models.PositiveSmallIntegerField(default=0, verbose_name="Max scroll depth")
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name="Time on page (sec)")
    attributed_leads = models.PositiveIntegerField(default=0, verbose_name="Attributed leads")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Page view"
        verbose_name_plural = "Page views"
        indexes = [
            models.Index(fields=["client", "session_id", "created_at"]),
            models.Index(fields=["client", "visitor_id", "created_at"]),
            models.Index(fields=["client", "pathname", "created_at"]),
        ]


class ClickEvent(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="click_events", verbose_name="Client")
    visitor_id = models.CharField(max_length=64, blank=True, default="", db_index=True, verbose_name="Visitor ID")
    session_id = models.CharField(max_length=64, db_index=True, verbose_name="Session ID")
    page_pathname = models.CharField(max_length=512, db_index=True, verbose_name="Page")
    element_text = models.CharField(max_length=100, blank=True, default="", verbose_name="Element text")
    element_id = models.CharField(max_length=255, blank=True, default="", verbose_name="Element ID")
    element_class = models.CharField(max_length=255, blank=True, default="", verbose_name="Element class")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Click"
        verbose_name_plural = "Clicks"
        indexes = [
            models.Index(fields=["client", "created_at"]),
            models.Index(fields=["client", "visitor_id", "created_at"]),
            models.Index(fields=["client", "page_pathname", "created_at"]),
        ]
