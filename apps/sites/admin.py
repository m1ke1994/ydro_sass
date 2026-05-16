from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html, format_html_join

from .models import Site, SiteSection


class SiteSectionInline(admin.TabularInline):
    model = SiteSection
    extra = 0
    fields = (
        "name",
        "slug",
        "section_type",
        "component_key",
        "order",
        "is_active",
        "schema",
        "content",
        "settings",
    )
    ordering = ("order", "name")
    show_change_link = True


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "domain",
        "owner",
        "is_active",
        "sections_count",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "slug", "domain", "owner__username", "owner__email")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "\u041e\u0441\u043d\u043e\u0432\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f",
            {"fields": ("name", "slug", "domain", "owner", "is_active")},
        ),
        ("\u0421\u0430\u0439\u0442 SEO", {"fields": ("seo",)}),
        (
            "\u0421\u043b\u0443\u0436\u0435\u0431\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f",
            {"fields": ("created_at", "updated_at")},
        ),
    )
    inlines = (SiteSectionInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(sections_total=Count("sections"))

    @admin.display(description="\u0420\u0430\u0437\u0434\u0435\u043b\u043e\u0432", ordering="sections_total")
    def sections_count(self, obj):
        return obj.sections_total


@admin.register(SiteSection)
class SiteSectionAdmin(admin.ModelAdmin):
    list_display = ("site", "name", "slug", "section_type", "order", "is_active", "updated_at")
    list_filter = ("site", "section_type", "is_active")
    search_fields = ("name", "slug", "section_type", "site__name")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at", "schema_preview")
    fieldsets = (
        ("\u041f\u0440\u0438\u0432\u044f\u0437\u043a\u0430", {"fields": ("site",)}),
        (
            "\u041e\u0441\u043d\u043e\u0432\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f",
            {"fields": ("name", "slug", "section_type", "order", "is_active")},
        ),
        ("\u0414\u0430\u043d\u043d\u044b\u0435 \u0441\u0435\u043a\u0446\u0438\u0438", {"fields": ("schema", "content")}),
        ("\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u0441\u0435\u043a\u0446\u0438\u0438", {"fields": ("component_key", "settings")}),
        ("\u041f\u0440\u0435\u0434\u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440 \u0441\u0445\u0435\u043c\u044b", {"fields": ("schema_preview",)}),
        (
            "\u0421\u043b\u0443\u0436\u0435\u0431\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f",
            {"fields": ("created_at", "updated_at")},
        ),
    )

    @admin.display(description="\u041f\u043e\u043b\u044f \u0441\u0445\u0435\u043c\u044b")
    def schema_preview(self, obj):
        schema_fields = obj.get_schema_fields()
        rows = []
        for field in schema_fields:
            if isinstance(field, dict):
                rows.append(
                    (
                        field.get("key") or "-",
                        field.get("label") or "-",
                        field.get("type") or "-",
                    )
                )

        if not rows:
            return format_html(
                "<span style='color: #6b7280;'>{}</span>",
                "\u0421\u0445\u0435\u043c\u0430 \u043f\u0443\u0441\u0442\u0430 \u0438\u043b\u0438 \u043d\u0435 \u0441\u043e\u0434\u0435\u0440\u0436\u0438\u0442 \u043f\u043e\u043b\u0435\u0439.",
            )

        return format_html(
            "<ul style='margin: 0; padding-left: 18px;'>{}</ul>",
            format_html_join(
                "",
                "<li><code>{}</code> - {} <strong>({})</strong></li>",
                rows,
            ),
        )
