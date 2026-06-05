from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html, format_html_join

from .models import SectionSchema, Site, SiteLead, SiteSection


class SiteSectionInline(admin.TabularInline):
    model = SiteSection
    extra = 0
    fields = (
        "title",
        "key",
        "section_type",
        "component_key",
        "order",
        "is_active",
        "schema",
        "content",
        "settings",
        "seo",
    )
    ordering = ("order", "title")
    show_change_link = True


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "domain",
        "api_key",
        "telegram_status",
        "owner",
        "is_active",
        "sections_count",
        "created_at",
    )
    list_filter = ("is_active", "send_to_telegram", "created_at")
    search_fields = ("name", "slug", "domain", "telegram_chat_id", "owner__username", "owner__email")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("api_key", "telegram_connected_at", "created_at", "updated_at")
    fieldsets = (
        ("Основное", {"fields": ("name", "slug", "domain", "api_key", "owner", "is_active")}),
        ("Telegram", {"fields": ("telegram_chat_id", "send_to_telegram", "telegram_connected_at")}),
        ("SEO", {"fields": ("seo",)}),
        ("Служебное", {"fields": ("created_at", "updated_at")}),
    )
    inlines = (SiteSectionInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(sections_total=Count("sections"))

    @admin.display(description="Sections", ordering="sections_total")
    def sections_count(self, obj):
        return obj.sections_total

    @admin.display(description="Telegram")
    def telegram_status(self, obj):
        return "подключен" if obj.telegram_chat_id and obj.send_to_telegram else "не подключен"


@admin.register(SectionSchema)
class SectionSchemaAdmin(admin.ModelAdmin):
    list_display = ("section_key", "title", "updated_at")
    search_fields = ("section_key", "title", "description")
    readonly_fields = ("created_at", "updated_at", "schema_preview")
    fieldsets = (
        ("Main", {"fields": ("section_key", "title", "description")}),
        ("Schema", {"fields": ("schema", "schema_preview")}),
        ("Meta", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Fields preview")
    def schema_preview(self, obj):
        rows = []
        for field in obj.schema.get("fields", []):
            if not isinstance(field, dict):
                continue
            rows.append((field.get("key") or "-", field.get("label") or "-", field.get("type") or "-"))

        if not rows:
            return format_html("<span style='color:#6b7280;'>Schema is empty.</span>")

        return format_html(
            "<ul style='margin:0; padding-left:18px;'>{}</ul>",
            format_html_join("", "<li><code>{}</code> - {} <strong>({})</strong></li>", rows),
        )


@admin.register(SiteSection)
class SiteSectionAdmin(admin.ModelAdmin):
    list_display = ("site", "title", "key", "section_type", "order", "is_active", "updated_at")
    list_filter = ("site", "section_type", "is_active")
    search_fields = ("title", "key", "section_type", "site__name")
    prepopulated_fields = {"key": ("title",)}
    readonly_fields = ("created_at", "updated_at", "schema_preview")
    fieldsets = (
        ("Bindings", {"fields": ("site",)}),
        ("Main", {"fields": ("title", "key", "section_type", "order", "is_active")}),
        ("Section data", {"fields": ("schema", "content")}),
        ("Section settings", {"fields": ("component_key", "settings")}),
        ("SEO", {"fields": ("seo",)}),
        ("Schema preview", {"fields": ("schema_preview",)}),
        ("Meta", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Schema fields")
    def schema_preview(self, obj):
        schema_fields = obj.get_schema_fields()
        rows = []
        for field in schema_fields:
            if isinstance(field, dict):
                rows.append((field.get("key") or "-", field.get("label") or "-", field.get("type") or "-"))

        if not rows:
            return format_html("<span style='color:#6b7280;'>Schema is empty.</span>")

        return format_html(
            "<ul style='margin:0; padding-left:18px;'>{}</ul>",
            format_html_join("", "<li><code>{}</code> - {} <strong>({})</strong></li>", rows),
        )


@admin.register(SiteLead)
class SiteLeadAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "site",
        "name",
        "phone",
        "email",
        "service_title",
        "service_type",
        "status",
    )
    list_filter = ("site", "status", "created_at", "service_type")
    search_fields = ("name", "phone", "email", "message", "service_title")
    readonly_fields = ("created_at", "updated_at", "user_agent", "ip_address", "payload")
    fieldsets = (
        ("Основное", {"fields": ("site", "status", "created_at", "updated_at")}),
        ("Клиент", {"fields": ("name", "phone", "email", "message")}),
        ("Источник", {"fields": ("section_key", "form_name", "service_type", "service_title", "source_url")}),
        ("Техническое", {"fields": ("ip_address", "user_agent", "payload")}),
    )
