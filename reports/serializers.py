from rest_framework import serializers


class DailyToggleSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
