from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        return token

    def validate(self, attrs):
        username_field = self.username_field
        candidate = attrs.get(username_field)

        if candidate and "@" in candidate:
            user_model = get_user_model()
            user = user_model.objects.filter(email__iexact=candidate).order_by("id").first()
            if user is not None:
                attrs[username_field] = getattr(user, username_field)

        return super().validate(attrs)
