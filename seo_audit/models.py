# -*- coding: utf-8 -*-
from django.db import models

from clients.models import Client


class SiteSEOAudit(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        ERROR = "error", "Error"
        STOPPED = "stopped", "Stopped"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="seo_audits")
    domain = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    seo_score = models.IntegerField(default=0)
    pages_count = models.PositiveIntegerField(default=0)
    used_sitemap = models.BooleanField(default=False)
    sitemap_urls_count = models.PositiveIntegerField(default=0)
    pages_with_speed_issues = models.PositiveIntegerField(default=0)
    pages_with_indexing_issues = models.PositiveIntegerField(default=0)
    has_robots_txt = models.BooleanField(default=False)
    has_sitemap_xml = models.BooleanField(default=False)
    avg_ttfb_ms = models.PositiveIntegerField(default=0)
    avg_performance_score = models.PositiveIntegerField(default=0)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"SEO audit #{self.pk} {self.domain} ({self.status})"


class SEOPage(models.Model):
    class SpeedStatus(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        GOOD = "good", "Good"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    class IndexabilityStatus(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        INDEXABLE = "indexable", "Indexable"
        NOINDEX = "noindex", "Noindex"
        BLOCKED = "blocked", "Blocked by robots.txt"
        CONFLICT = "conflict", "Indexability conflict"

    class CommercialStatus(models.TextChoices):
        GOOD = "good", "Ready for leads"
        WARNING = "warning", "Needs improvement"
        CRITICAL = "critical", "Weak conversion readiness"

    class ConversionPathType(models.TextChoices):
        NONE = "none", "No conversion path"
        FORM = "form", "Form"
        CONTACTS = "contacts", "Direct contacts"
        MESSENGER = "messenger", "Messenger or social contact"
        WIDGET = "widget", "Widget"
        MIXED = "mixed", "Mixed conversion mechanics"

    audit = models.ForeignKey(SiteSEOAudit, on_delete=models.CASCADE, related_name="pages")
    url = models.TextField()
    status_code = models.PositiveIntegerField(default=0)
    ttfb_ms = models.PositiveIntegerField(default=0)
    html_size_bytes = models.PositiveIntegerField(default=0)
    js_files_count = models.PositiveIntegerField(default=0)
    css_files_count = models.PositiveIntegerField(default=0)
    images_count = models.PositiveIntegerField(default=0)
    total_js_bytes = models.PositiveIntegerField(default=0)
    total_css_bytes = models.PositiveIntegerField(default=0)
    total_image_bytes = models.PositiveIntegerField(default=0)
    performance_score = models.PositiveIntegerField(default=0)
    speed_status = models.CharField(
        max_length=16,
        choices=SpeedStatus.choices,
        default=SpeedStatus.UNKNOWN,
    )
    title = models.CharField(max_length=512, blank=True, default="")
    title_length = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, default="")
    description_length = models.PositiveIntegerField(default=0)
    h1 = models.TextField(blank=True, default="")
    h1_count = models.PositiveIntegerField(default=0)
    word_count = models.PositiveIntegerField(default=0)
    meta_robots = models.CharField(max_length=512, blank=True, default="")
    canonical_url = models.TextField(blank=True, default="")
    indexability_status = models.CharField(
        max_length=24,
        choices=IndexabilityStatus.choices,
        default=IndexabilityStatus.UNKNOWN,
    )
    in_sitemap = models.BooleanField(default=False)
    blocked_by_robots = models.BooleanField(default=False)

    has_form = models.BooleanField(default=False)
    has_cta = models.BooleanField(default=False)
    has_phone_or_contact = models.BooleanField(default=False)
    has_messenger = models.BooleanField(default=False)
    has_offer_like_heading = models.BooleanField(default=False)
    has_benefits_block = models.BooleanField(default=False)
    has_faq = models.BooleanField(default=False)
    has_conversion_path = models.BooleanField(default=False)
    conversion_path_type = models.CharField(
        max_length=16,
        choices=ConversionPathType.choices,
        default=ConversionPathType.NONE,
    )
    commercial_signals_payload = models.JSONField(default=dict, blank=True)
    commercial_readiness_score = models.PositiveSmallIntegerField(default=0)
    commercial_status = models.CharField(
        max_length=16,
        choices=CommercialStatus.choices,
        default=CommercialStatus.WARNING,
    )

    class Meta:
        ordering = ("url", "id")
        indexes = [
            models.Index(fields=["audit", "url"]),
        ]

    def __str__(self) -> str:
        return f"SEO page #{self.pk} ({self.status_code}) {self.url}"


class SEOIssue(models.Model):
    class IssueType(models.TextChoices):
        MISSING_TITLE = "missing_title", "missing_title"
        BAD_TITLE_LENGTH = "bad_title_length", "bad_title_length"
        TITLE_TOO_SHORT = "title_too_short", "title_too_short"
        TITLE_TOO_LONG = "title_too_long", "title_too_long"
        MISSING_DESCRIPTION = "missing_description", "missing_description"
        DESCRIPTION_TOO_SHORT = "description_too_short", "description_too_short"
        DESCRIPTION_TOO_LONG = "description_too_long", "description_too_long"
        DUPLICATE_TITLE = "duplicate_title", "duplicate_title"
        MISSING_H1 = "missing_h1", "missing_h1"
        MULTIPLE_H1 = "multiple_h1", "multiple_h1"
        LONG_H1 = "long_h1", "long_h1"
        HEADING_HIERARCHY_GAP = "heading_hierarchy_gap", "heading_hierarchy_gap"
        LOW_WORD_COUNT = "low_word_count", "low_word_count"
        IMAGE_MISSING_ALT = "image_missing_alt", "image_missing_alt"
        IMAGE_EMPTY_ALT = "image_empty_alt", "image_empty_alt"
        BAD_STATUS = "bad_status", "bad_status"
        NETWORK_ERROR = "network_error", "network_error"
        REDIRECT = "redirect", "redirect"
        SLOW_RESPONSE = "slow_response", "slow_response"
        LARGE_PAGE_SIZE = "large_page_size", "large_page_size"
        SLOW_TTFB = "slow_ttfb", "slow_ttfb"
        LARGE_HTML_SIZE = "large_html_size", "large_html_size"
        TOO_MANY_JS = "too_many_js", "too_many_js"
        TOO_MANY_CSS = "too_many_css", "too_many_css"
        TOO_MANY_IMAGES = "too_many_images", "too_many_images"
        HEAVY_JS_PAYLOAD = "heavy_js_payload", "heavy_js_payload"
        HEAVY_CSS_PAYLOAD = "heavy_css_payload", "heavy_css_payload"
        HEAVY_IMAGES_PAYLOAD = "heavy_images_payload", "heavy_images_payload"
        HEAVY_PAGE_PAYLOAD = "heavy_page_payload", "heavy_page_payload"
        MISSING_CANONICAL = "missing_canonical", "missing_canonical"
        INVALID_CANONICAL = "invalid_canonical", "invalid_canonical"
        CANONICAL_CONFLICT = "canonical_conflict", "canonical_conflict"
        PAGE_NOINDEX = "page_noindex", "page_noindex"
        PAGE_NOFOLLOW = "page_nofollow", "page_nofollow"
        BLOCKED_BY_ROBOTS = "blocked_by_robots", "blocked_by_robots"
        SITEMAP_PAGE_MISSING = "sitemap_page_missing", "sitemap_page_missing"
        MISSING_META_ROBOTS = "missing_meta_robots", "missing_meta_robots"
        MISSING_VIEWPORT = "missing_viewport", "missing_viewport"
        MISSING_CHARSET = "missing_charset", "missing_charset"
        MISSING_ROBOTS_TXT = "missing_robots_txt", "missing_robots_txt"
        ROBOTS_DISALLOW_ALL = "robots_disallow_all", "robots_disallow_all"
        ROBOTS_MISSING_SITEMAP = "robots_missing_sitemap", "robots_missing_sitemap"
        MISSING_SITEMAP = "missing_sitemap", "missing_sitemap"
        BAD_SITEMAP_STATUS = "bad_sitemap_status", "bad_sitemap_status"
        SITEMAP_MISMATCH = "sitemap_mismatch", "sitemap_mismatch"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    page = models.ForeignKey(SEOPage, on_delete=models.CASCADE, related_name="issues")
    issue_type = models.CharField(max_length=64, choices=IssueType.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices)
    recommendation = models.TextField()

    class Meta:
        ordering = ("page__url", "id")

    def __str__(self) -> str:
        return f"SEO issue #{self.pk} {self.issue_type} ({self.severity})"
