from django.core.exceptions import ValidationError as DjangoValidationError
import logging

from rest_framework import serializers

from leads.services import send_lead_telegram_notification

from .models import SectionSchema, Site, SiteLead, SiteSection
from .a_meditation import SECTION_TITLES
from .tracker_utils import build_tracker_script_tag

logger = logging.getLogger(__name__)


class PublicSiteSerializer(serializers.ModelSerializer):
    sections_count = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = ("id", "name", "slug", "domain", "seo", "is_active", "sections_count")

    def get_sections_count(self, obj):
        annotated_count = getattr(obj, "sections_count", None)
        if annotated_count is not None:
            return annotated_count
        return obj.sections.filter(is_active=True).count()


class PublicSiteSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = (
            "id",
            "site",
            "key",
            "title",
            "section_type",
            "component_key",
            "order",
            "schema",
            "content",
            "settings",
            "seo",
            "is_active",
        )


class SectionSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectionSchema
        fields = ("id", "section_key", "title", "schema", "description", "created_at", "updated_at")


class AdminMySiteSerializer(serializers.ModelSerializer):
    sections_count = serializers.SerializerMethodField()
    tracker_script_tag = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = (
            "id",
            "name",
            "slug",
            "domain",
            "api_key",
            "telegram_chat_id",
            "send_to_telegram",
            "telegram_connected_at",
            "seo",
            "is_active",
            "sections_count",
            "tracker_script_tag",
            "created_at",
            "updated_at",
        )

    def get_sections_count(self, obj):
        annotated_count = getattr(obj, "sections_count", None)
        if annotated_count is not None:
            return annotated_count
        return obj.sections.filter(is_active=True).count()

    def get_tracker_script_tag(self, obj):
        return build_tracker_script_tag(obj.api_key)


class AdminMySiteSectionSerializer(serializers.ModelSerializer):
    schema_template = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()

    class Meta:
        model = SiteSection
        fields = (
            "id",
            "site",
            "key",
            "title",
            "display_title",
            "section_type",
            "component_key",
            "order",
            "is_active",
            "schema",
            "schema_template",
            "content",
            "settings",
            "seo",
            "created_at",
            "updated_at",
        )

    def get_schema_template(self, obj):
        schema_obj = SectionSchema.objects.filter(section_key=obj.key).first()
        if not schema_obj:
            return None
        return SectionSchemaSerializer(schema_obj).data

    def get_display_title(self, obj):
        if obj.site.slug == "a-meditation":
            return SECTION_TITLES.get(obj.key, obj.title)
        return obj.title


class AdminMySiteSectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = (
            "id",
            "site",
            "key",
            "title",
            "section_type",
            "component_key",
            "order",
            "is_active",
            "schema",
            "content",
            "settings",
            "seo",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "site", "created_at", "updated_at")

    def validate_schema(self, value):
        try:
            SiteSection.validate_schema(value)
        except DjangoValidationError as exc:
            details = exc.message_dict.get("schema", exc.messages)
            raise serializers.ValidationError(details)
        return value

    def validate(self, attrs):
        schema = attrs.get("schema")
        content = attrs.get("content")
        if schema is not None and content is not None:
            try:
                SiteSection.validate_content(content=content, schema=schema)
            except DjangoValidationError as exc:
                details = exc.message_dict.get("content", exc.messages)
                raise serializers.ValidationError({"content": details})
        return attrs


class AdminMySiteSectionPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = ("content",)

    def validate(self, attrs):
        forbidden_fields = set(self.initial_data.keys()) - {"content"}
        if forbidden_fields:
            details = {field: "This field is read-only in this endpoint." for field in sorted(forbidden_fields)}
            raise serializers.ValidationError(details)
        return attrs

    def validate_content(self, value):
        if self.instance is None:
            return value

        try:
            SiteSection.validate_schema(self.instance.schema)
            SiteSection.validate_content(content=value, schema=self.instance.schema)
        except DjangoValidationError as exc:
            details = exc.message_dict.get("content", exc.messages)
            raise serializers.ValidationError(details)

        return value

    def to_representation(self, instance):
        return AdminMySiteSectionSerializer(instance, context=self.context).data


class PublicLeadCreateSerializer(serializers.Serializer):
    site_slug = serializers.SlugField()
    section_key = serializers.CharField(max_length=100, required=False, allow_blank=True)
    form_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    service_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    service_title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    source_url = serializers.URLField(required=False, allow_blank=True)
    payload = serializers.JSONField(required=False)

    default_error_messages = {
        "required_fields": "Заполните обязательные поля",
        "site_not_found": "Сайт не найден",
    }

    def validate(self, attrs):
        required_fields = ("site_slug", "name", "phone")
        if any(not str(attrs.get(field, "")).strip() for field in required_fields):
            self.fail("required_fields")
        return attrs

    def create(self, validated_data):
        site_slug = validated_data.pop("site_slug")
        site = Site.objects.filter(slug=site_slug, is_active=True).first()
        if site is None:
            self.fail("site_not_found")

        request = self.context.get("request")
        meta = getattr(request, "META", {})
        payload = validated_data.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        payload = dict(payload)
        if meta.get("HTTP_REFERER") and not payload.get("referrer"):
            payload["referrer"] = meta["HTTP_REFERER"]

        lead = SiteLead.objects.create(
            site=site,
            section_key=validated_data.get("section_key", ""),
            form_name=validated_data.get("form_name", ""),
            name=validated_data["name"],
            phone=validated_data["phone"],
            email=validated_data.get("email", ""),
            message=validated_data.get("message", ""),
            service_type=validated_data.get("service_type", ""),
            service_title=validated_data.get("service_title", ""),
            source_url=validated_data.get("source_url", ""),
            user_agent=meta.get("HTTP_USER_AGENT", "")[:1000],
            ip_address=self._extract_ip(meta),
            payload=payload,
        )
        self._send_site_lead_telegram_notification(site=site, lead=lead)
        return lead

    @staticmethod
    def _extract_ip(meta):
        x_forwarded_for = meta.get("HTTP_X_FORWARDED_FOR", "")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return meta.get("REMOTE_ADDR")

    def _send_site_lead_telegram_notification(self, *, site: Site, lead: SiteLead) -> None:
        delivered = send_lead_telegram_notification(lead, site=site)
        if not delivered:
            logger.warning(
                "Site lead telegram notification skipped or failed site_id=%s lead_id=%s",
                site.id,
                lead.id,
            )


class AdminLeadSerializer(serializers.ModelSerializer):
    site_slug = serializers.CharField(source="site.slug", read_only=True)
    site_name = serializers.CharField(source="site.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SiteLead
        fields = (
            "id",
            "site",
            "site_slug",
            "site_name",
            "section_key",
            "form_name",
            "name",
            "phone",
            "email",
            "message",
            "service_type",
            "service_title",
            "source_url",
            "status",
            "status_label",
            "created_at",
            "updated_at",
        )


class AdminLeadStatusPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteLead
        fields = ("status",)
