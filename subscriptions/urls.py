from django.urls import path

from subscriptions.views import (
    SubscriptionCreatePaymentView,
    SubscriptionPlansView,
    SubscriptionStatusView,
    SubscriptionWebhookView,
)

urlpatterns = [
    path("status/", SubscriptionStatusView.as_view(), name="subscription_status"),
    path("plans/", SubscriptionPlansView.as_view(), name="subscription_plans"),
    path("create-payment/", SubscriptionCreatePaymentView.as_view(), name="subscription_create_payment"),
    path("webhook/", SubscriptionWebhookView.as_view(), name="subscription_webhook"),
]

