from rest_framework import serializers

from analytics_app.models import ClickEvent, Event, PageView


class PublicEventCreateSerializer(serializers.ModelSerializer):
    source_url = serializers.URLField(required=False, allow_null=True, allow_blank=True, write_only=True)
    utm_source = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    utm_medium = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    utm_campaign = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    visitor_id = serializers.CharField(required=False, allow_blank=True, max_length=64)

    class Meta:
        model = Event
        fields = (
            "event_type",
            "element_id",
            "page_url",
            "source_url",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "visitor_id",
        )

    def create(self, validated_data):
        client = self.context["client"]
        validated_data.pop("source_url", None)
        validated_data.pop("utm_source", None)
        validated_data.pop("utm_medium", None)
        validated_data.pop("utm_campaign", None)
        return Event.objects.create(client=client, **validated_data)


class PublicAnalyticsEventSerializer(serializers.Serializer):
    EVENT_PAGE_VIEW = "page_view"
    EVENT_SESSION_END = "session_end"
    EVENT_CLICK = "click_event"
    EVENT_LEAD_SUBMIT = "lead_submit"

    event_type = serializers.ChoiceField(
        choices=(EVENT_PAGE_VIEW, EVENT_SESSION_END, EVENT_CLICK, EVENT_LEAD_SUBMIT)
    )
    visitor_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    session_id = serializers.CharField(max_length=64)
    timestamp = serializers.DateTimeField(required=False)

    url = serializers.URLField(required=False, allow_blank=True)
    pathname = serializers.CharField(required=False, allow_blank=True, max_length=512)
    query_string = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    referrer = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    utm_source = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    utm_medium = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    utm_campaign = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    utm_term = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    utm_content = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    duration_seconds = serializers.IntegerField(required=False, min_value=0)
    max_scroll_depth = serializers.IntegerField(required=False, min_value=0, max_value=100)

    element_text = serializers.CharField(required=False, allow_blank=True, max_length=100)
    element_id = serializers.CharField(required=False, allow_blank=True, max_length=255)
    element_class = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def _get_latest_page_view(self, client, session_id):
        return (
            PageView.objects.filter(client=client, session_id=session_id)
            .order_by("-created_at")
            .first()
        )

    def _normalize_referrer(self, value):
        value = (value or "").strip()
        if not value:
            return None
        if value == "null":
            return None
        return value

    def create(self, validated_data):
        client = self.context["client"]
        event_type = validated_data["event_type"]
        session_id = validated_data["session_id"]
        visitor_id = (validated_data.get("visitor_id") or "").strip()

        if event_type == self.EVENT_PAGE_VIEW:
            pathname = (validated_data.get("pathname") or "").strip() or "/"
            page_view = PageView.objects.create(
                client=client,
                visitor_id=visitor_id,
                session_id=session_id,
                url=validated_data.get("url") or "",
                pathname=pathname,
                query_string=validated_data.get("query_string"),
                referrer=self._normalize_referrer(validated_data.get("referrer")),
                utm_source=validated_data.get("utm_source"),
                utm_medium=validated_data.get("utm_medium"),
                utm_campaign=validated_data.get("utm_campaign"),
                utm_term=validated_data.get("utm_term"),
                utm_content=validated_data.get("utm_content"),
                max_scroll_depth=validated_data.get("max_scroll_depth") or 0,
            )
            return {"kind": "page_view", "id": page_view.id}

        if event_type == self.EVENT_SESSION_END:
            latest = self._get_latest_page_view(client=client, session_id=session_id)
            if not latest:
                return {"kind": "session_end", "id": None}
            max_scroll_depth = validated_data.get("max_scroll_depth")
            duration_seconds = validated_data.get("duration_seconds")
            update_fields = []
            if max_scroll_depth is not None and max_scroll_depth > latest.max_scroll_depth:
                latest.max_scroll_depth = max_scroll_depth
                update_fields.append("max_scroll_depth")
            if duration_seconds is not None and duration_seconds > latest.duration_seconds:
                latest.duration_seconds = duration_seconds
                update_fields.append("duration_seconds")
            if visitor_id and latest.visitor_id != visitor_id:
                latest.visitor_id = visitor_id
                update_fields.append("visitor_id")
            if update_fields:
                latest.save(update_fields=update_fields + ["updated_at"])
            return {"kind": "session_end", "id": latest.id}

        if event_type == self.EVENT_CLICK:
            pathname = (validated_data.get("pathname") or "").strip()
            if not pathname:
                latest = self._get_latest_page_view(client=client, session_id=session_id)
                pathname = latest.pathname if latest else "/"
            click = ClickEvent.objects.create(
                client=client,
                visitor_id=visitor_id,
                session_id=session_id,
                page_pathname=pathname,
                element_text=(validated_data.get("element_text") or "")[:100],
                element_id=(validated_data.get("element_id") or "")[:255],
                element_class=(validated_data.get("element_class") or "")[:255],
            )
            return {"kind": "click_event", "id": click.id}

        if event_type == self.EVENT_LEAD_SUBMIT:
            latest = self._get_latest_page_view(client=client, session_id=session_id)
            return {"kind": "lead_submit", "id": latest.id if latest else None}

        raise serializers.ValidationError({"event_type": ["Unsupported event type."]})
