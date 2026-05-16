from rest_framework import serializers

from .models import MediaFile


class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = (
            "id",
            "title",
            "alt",
            "description",
            "file",
            "file_type",
            "mime_type",
            "size",
            "created_at",
        )
        read_only_fields = ("id", "file_type", "mime_type", "size", "created_at")
