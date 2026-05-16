from rest_framework import serializers

from .models import ClientProfile


class ClientProfileMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ("display_name", "phone")


class UserMeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    profile = serializers.SerializerMethodField()
    sites_count = serializers.SerializerMethodField()

    def get_profile(self, obj):
        profile = getattr(obj, "client_profile", None)
        if profile is None:
            return None
        return ClientProfileMeSerializer(profile).data

    def get_sites_count(self, obj):
        return obj.sites.count()
