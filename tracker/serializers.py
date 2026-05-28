from django.utils import timezone
from rest_framework import serializers


class BaseTrackSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128)
    visitor_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    session_id = serializers.CharField(max_length=64)


class VisitStartSerializer(BaseTrackSerializer):
    referrer = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2048)
    started_at = serializers.DateTimeField(required=False)

    def get_started_at(self):
        return self.validated_data.get("started_at") or timezone.now()


class PageViewSerializer(BaseTrackSerializer):
    url = serializers.CharField(max_length=4096)
    title = serializers.CharField(required=False, allow_blank=True, max_length=512)
    timestamp = serializers.DateTimeField(required=False)

    def get_timestamp(self):
        return self.validated_data.get("timestamp") or timezone.now()


class TrackEventSerializer(BaseTrackSerializer):
    type = serializers.CharField(max_length=64)
    payload = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField(required=False)

    def get_timestamp(self):
        return self.validated_data.get("timestamp") or timezone.now()


class VisitEndSerializer(BaseTrackSerializer):
    ended_at = serializers.DateTimeField(required=False)
    duration = serializers.IntegerField(required=False, min_value=0)

    def get_ended_at(self):
        return self.validated_data.get("ended_at") or timezone.now()
