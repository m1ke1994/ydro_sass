from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Site, SiteSection


class SiteSerializer(serializers.ModelSerializer):
    sections_count = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = ("id", "name", "slug", "domain", "seo", "is_active", "sections_count")

    def get_sections_count(self, obj):
        annotated_count = getattr(obj, "sections_count", None)
        if annotated_count is not None:
            return annotated_count
        return obj.sections.filter(is_active=True).count()


class SiteSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = (
            "id",
            "name",
            "slug",
            "section_type",
            "component_key",
            "order",
            "schema",
            "content",
            "settings",
            "is_active",
        )


class ClientSiteSerializer(serializers.ModelSerializer):
    sections_count = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = ("id", "name", "slug", "domain", "seo", "is_active", "sections_count")

    def get_sections_count(self, obj):
        annotated_count = getattr(obj, "sections_count", None)
        if annotated_count is not None:
            return annotated_count
        return obj.sections.count()


class ClientSiteSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = (
            "id",
            "site",
            "name",
            "slug",
            "section_type",
            "component_key",
            "order",
            "is_active",
            "schema",
            "content",
            "settings",
            "created_at",
            "updated_at",
        )


class SiteSectionFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = (
            "id",
            "name",
            "slug",
            "section_type",
            "component_key",
            "schema",
            "content",
            "settings",
        )


class ClientSiteSectionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSection
        fields = ("content", "settings")

    def validate(self, attrs):
        forbidden_fields = set(self.initial_data.keys()) - {"content", "settings"}
        if forbidden_fields:
            details = {
                field: "Это поле недоступно для изменения в client API."
                for field in sorted(forbidden_fields)
            }
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

    def validate_settings(self, value):
        if self.instance is None:
            return value

        try:
            SiteSection.validate_settings(settings=value)
        except DjangoValidationError as exc:
            details = exc.message_dict.get("settings", exc.messages)
            raise serializers.ValidationError(details)

        return value
