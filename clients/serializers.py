from django.conf import settings
from rest_framework import serializers

from clients.models import Client
from clients.telegram_binding import build_secure_start_payload


class ClientSettingsSerializer(serializers.ModelSerializer):
    public_script_tag = serializers.SerializerMethodField()
    tracker_script_url = serializers.SerializerMethodField()
    telegram_status = serializers.SerializerMethodField()
    telegram_connect_url = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = (
            "id",
            "name",
            "uuid",
            "api_key",
            "tracker_script_url",
            "public_script_tag",
            "telegram_chat_id",
            "telegram_status",
            "telegram_connect_url",
            "send_to_telegram",
            "is_active",
            "created_at",
        )
        read_only_fields = (
            "id",
            "uuid",
            "api_key",
            "tracker_script_url",
            "public_script_tag",
            "telegram_chat_id",
            "telegram_status",
            "telegram_connect_url",
            "is_active",
            "created_at",
        )

    def get_tracker_script_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri("/api/mini/tracker.js")
        return obj.tracker_script_url

    def get_public_script_tag(self, obj):
        script_url = self.get_tracker_script_url(obj)
        return f'<script src="{script_url}" data-api-key="{obj.api_key}"></script>'

    def get_telegram_status(self, obj):
        return "connected" if obj.telegram_chat_id else "not_connected"

    def get_telegram_connect_url(self, obj):
        bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "")
        if not bot_username:
            return ""
        return f"https://t.me/{bot_username}?start={build_secure_start_payload(obj)}"
