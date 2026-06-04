import logging

from rest_framework import serializers

from analytics_app.models import PageView
from leads.models import Lead
from leads.tasks import send_lead_notification_task
from leads.utils import normalize_phone
from tracker.models import Visit

logger = logging.getLogger(__name__)


def _set_context_value(context, key, value):
    if not context.get(key) and value not in (None, ""):
        context[key] = value


class PublicLeadCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True, label="Name")
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, label="Phone")
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True, label="Email")
    session_id = serializers.CharField(required=False, allow_blank=True, write_only=True)
    domain = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    page = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    form = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    form_name = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    source = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    utm_term = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    utm_content = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    device = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    browser = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    os = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)

    class Meta:
        model = Lead
        fields = (
            "name",
            "phone",
            "email",
            "message",
            "source_url",
            "domain",
            "page",
            "form",
            "form_name",
            "source",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "device",
            "browser",
            "os",
            "session_id",
        )

    def validate(self, attrs):
        name = (attrs.get("name") or "").strip()
        attrs["name"] = name

        raw_email = attrs.get("email")
        if raw_email is not None:
            email = str(raw_email).strip().lower()
            attrs["email"] = email or None

        attrs["phone"] = normalize_phone(attrs.get("phone"))
        return attrs

    def create(self, validated_data):
        client = self.context["client"]
        request = self.context.get("request")
        session_id = (validated_data.pop("session_id", "") or "").strip()
        notification_context = {}
        for field_name in (
            "domain",
            "page",
            "form",
            "form_name",
            "source",
            "utm_term",
            "utm_content",
            "device",
            "browser",
            "os",
        ):
            value = validated_data.pop(field_name, None)
            if value not in (None, ""):
                notification_context[field_name] = value

        if request is not None:
            forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
            _set_context_value(notification_context, "ip", forwarded or request.META.get("REMOTE_ADDR"))
            _set_context_value(notification_context, "user_agent", request.META.get("HTTP_USER_AGENT", ""))
            _set_context_value(notification_context, "referrer", request.META.get("HTTP_REFERER", ""))

        validated_data.setdefault("name", "")
        if session_id:
            latest_page_view = (
                PageView.objects.filter(client=client, session_id=session_id)
                .order_by("-created_at")
                .first()
            )
            if latest_page_view:
                validated_data["source_url"] = validated_data.get("source_url") or latest_page_view.url
                validated_data["utm_source"] = validated_data.get("utm_source") or latest_page_view.utm_source
                validated_data["utm_medium"] = validated_data.get("utm_medium") or latest_page_view.utm_medium
                validated_data["utm_campaign"] = validated_data.get("utm_campaign") or latest_page_view.utm_campaign
                _set_context_value(notification_context, "page", latest_page_view.pathname)
                _set_context_value(notification_context, "utm_term", latest_page_view.utm_term)
                _set_context_value(notification_context, "utm_content", latest_page_view.utm_content)
                _set_context_value(notification_context, "referrer", latest_page_view.referrer)
                latest_page_view.attributed_leads += 1
                latest_page_view.save(update_fields=["attributed_leads", "updated_at"])

            latest_visit = (
                Visit.objects.filter(site__token=client.api_key, session_id=session_id)
                .order_by("-started_at")
                .first()
            )
            if latest_visit:
                _set_context_value(notification_context, "ip", str(latest_visit.ip_address or ""))
                _set_context_value(notification_context, "user_agent", latest_visit.user_agent or "")
                _set_context_value(notification_context, "device", latest_visit.device_type or "")
                _set_context_value(notification_context, "browser", latest_visit.browser or "")
                _set_context_value(notification_context, "os", latest_visit.os or "")

        lead = Lead.objects.create(
            client=client,
            status=Lead.Status.NEW,
            notification_context=notification_context,
            **validated_data,
        )
        try:
            send_lead_notification_task.delay(lead.id)
        except Exception:
            logger.exception(
                "Failed to enqueue lead notification task. lead_id=%s client_id=%s",
                lead.id,
                client.id,
            )
        return lead


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = (
            "id",
            "name",
            "phone",
            "email",
            "message",
            "source_url",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class LeadStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Lead.Status.choices, label="Status")

    class Meta:
        model = Lead
        fields = ("status",)
