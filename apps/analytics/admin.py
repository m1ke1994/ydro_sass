from django.contrib import admin

from .models import PageView, TrackingEvent, Visit


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("id", "site", "session_id", "visitor_id", "started_at", "duration")
    list_filter = ("site", "started_at")
    search_fields = ("session_id", "visitor_id", "ip_address")


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ("id", "visit", "pathname", "timestamp")
    list_filter = ("timestamp", "visit__site")
    search_fields = ("url", "pathname", "visit__session_id")


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ("id", "visit", "type", "timestamp")
    list_filter = ("type", "timestamp", "visit__site")
    search_fields = ("type", "visit__session_id", "visit__visitor_id")
