from django.contrib import admin

from telegram_logs.models import TelegramUpdateLog


@admin.register(TelegramUpdateLog)
class TelegramUpdateLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "update_id",
        "chat_id",
        "chat_type",
        "username",
        "command",
        "short_text",
    )
    list_filter = ("chat_type", "command", "created_at")
    search_fields = ("update_id", "chat_id", "username", "first_name", "last_name", "text")
    ordering = ("-created_at",)
    readonly_fields = (
        "update_id",
        "message_id",
        "chat_id",
        "chat_type",
        "chat_title",
        "user_id",
        "username",
        "first_name",
        "last_name",
        "text",
        "command",
        "payload",
        "created_at",
    )

    def short_text(self, obj):
        if not obj.text:
            return "-"
        return obj.text[:60]

    short_text.short_description = "Text"
