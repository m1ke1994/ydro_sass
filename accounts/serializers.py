from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from clients.models import Client
from subscriptions.models import Subscription, SubscriptionSettings

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)

    def validate_company_name(self, value):
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("Company name is required.")
        return normalized

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return email

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        company_name = validated_data["company_name"]

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            is_staff=False,
            is_superuser=False,
        )
        client = Client.objects.create(
            owner=user,
            name=company_name,
            send_to_telegram=False,
            telegram_chat_id=None,
        )

        subscription_settings = SubscriptionSettings.get_solo()
        trial_enabled = subscription_settings.demo_enabled
        Subscription.objects.get_or_create(
            client=client,
            defaults={
                "status": Subscription.Status.ACTIVE if trial_enabled else Subscription.Status.EXPIRED,
                "paid_until": timezone.now() + timedelta(days=subscription_settings.demo_days) if trial_enabled else None,
                "is_trial": trial_enabled,
                "auto_renew": False,
            },
        )
        return user, client


class RegisterResponseSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    client_id = serializers.IntegerField()
    company_name = serializers.CharField()
    api_key = serializers.CharField()
