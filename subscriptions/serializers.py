from rest_framework import serializers

from subscriptions.models import Subscription, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ("id", "name", "duration_days", "price")


class SubscriptionStatusSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    client_id = serializers.IntegerField(source="client_id", read_only=True)

    class Meta:
        model = Subscription
        fields = ("status", "paid_until", "is_trial", "plan", "client_id")


class CreatePaymentSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
