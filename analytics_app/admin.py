from django.contrib import admin

from analytics_app.models import ClickEvent, Event, PageView


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "visitor_id", "event_type", "page_url", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("page_url", "element_id", "client__name")
    ordering = ("-created_at",)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client",
        "visitor_id",
        "session_id",
        "pathname",
        "duration_seconds",
        "max_scroll_depth",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("session_id", "pathname", "url", "client__name")
    ordering = ("-created_at",)


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "visitor_id", "session_id", "page_pathname", "element_text", "created_at")
    list_filter = ("created_at",)
    search_fields = ("session_id", "page_pathname", "element_text", "element_id", "client__name")
    ordering = ("-created_at",)
