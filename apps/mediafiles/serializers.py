from rest_framework import serializers

from .models import MediaFile


class MediaFileSerializer(serializers.ModelSerializer):
    site = serializers.IntegerField(source="site_id", read_only=True)
    url = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()

    class Meta:
        model = MediaFile
        fields = (
            "id",
            "site",
            "section_key",
            "field_key",
            "original_name",
            "title",
            "alt",
            "description",
            "file",
            "url",
            "path",
            "filename",
            "file_type",
            "mime_type",
            "size",
            "created_at",
        )
        read_only_fields = ("id", "file_type", "mime_type", "size", "created_at", "url", "path", "filename")

    def get_url(self, obj):
        return obj.get_absolute_url()

    def get_path(self, obj):
        return obj.get_relative_media_path()

    def get_filename(self, obj):
        return obj.get_filename()
