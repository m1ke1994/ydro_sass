from django.utils import timezone
from rest_framework import serializers


class VisitStartSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128)
    session_id = serializers.CharField(max_length=64)
    visitor_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    referrer = serializers.CharField(required=False, allow_blank=True)
    started_at = serializers.DateTimeField(required=False)

    def get_started_at(self):
        return self.validated_data.get("started_at") or timezone.now()


class PageViewSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128)
    session_id = serializers.CharField(max_length=64)
    visitor_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    url = serializers.URLField(max_length=1000)
    title = serializers.CharField(required=False, allow_blank=True, max_length=512)
    timestamp = serializers.DateTimeField(required=False)

    def get_timestamp(self):
        return self.validated_data.get("timestamp") or timezone.now()


class TrackEventSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128)
    session_id = serializers.CharField(max_length=64)
    visitor_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    type = serializers.CharField(max_length=64)
    payload = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField(required=False)

    def get_timestamp(self):
        return self.validated_data.get("timestamp") or timezone.now()


class VisitEndSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128)
    session_id = serializers.CharField(max_length=64)
    visitor_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    ended_at = serializers.DateTimeField(required=False)
    duration = serializers.IntegerField(required=False, min_value=0)

    def get_ended_at(self):
        return self.validated_data.get("ended_at") or timezone.now()
