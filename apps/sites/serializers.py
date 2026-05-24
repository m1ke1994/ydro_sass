from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import SectionSchema, Site, SiteSection


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

    class Meta:
        model = Site
        fields = (
            "id",
            "name",
            "slug",
            "domain",
            "seo",
            "is_active",
            "sections_count",
            "created_at",
            "updated_at",
        )

    def get_sections_count(self, obj):
        annotated_count = getattr(obj, "sections_count", None)
        if annotated_count is not None:
            return annotated_count
        return obj.sections.filter(is_active=True).count()


class AdminMySiteSectionSerializer(serializers.ModelSerializer):
    schema_template = serializers.SerializerMethodField()

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
