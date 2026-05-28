# -*- coding: utf-8 -*-
from django.contrib import admin

from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit


@admin.register(SiteSEOAudit)
class SiteSEOAuditAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "domain", "status", "seo_score", "pages_count", "created_at", "finished_at")
    list_filter = ("status", "client")
    search_fields = ("domain", "client__name", "client__owner__email")


@admin.register(SEOPage)
class SEOPageAdmin(admin.ModelAdmin):
    list_display = ("id", "audit", "status_code", "title_length", "description_length", "h1_count", "word_count")
    list_filter = ("audit__client", "status_code")
    search_fields = ("url", "title", "h1")


@admin.register(SEOIssue)
class SEOIssueAdmin(admin.ModelAdmin):
    list_display = ("id", "page", "issue_type", "severity")
    list_filter = ("issue_type", "severity", "page__audit__client")
    search_fields = ("page__url", "recommendation")

