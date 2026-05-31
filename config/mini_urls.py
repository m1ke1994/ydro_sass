from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import ChangePasswordView, LoginView, LogoutView, RegisterView
from analytics_app.views import (
    AnalyticsAiRecommendationsView,
    AnalyticsDevicesView,
    AnalyticsEngagementView,
    AnalyticsOverviewView,
    AnalyticsSummaryView,
    AnalyticsUniqueDailyView,
    PublicAnalyticsEventCreateView,
    PublicEventCreateView,
)
from clients.views import ClientSettingsView, tracker_js_view
from clients.telegram_views import (
    TelegramIntegrationDisconnectView,
    TelegramIntegrationSendTestView,
    TelegramIntegrationStatusView,
)
from leads.views import LeadViewSet, PublicLeadCreateView
from subscriptions.views import YooKassaWebhookView
from telegram_logs.views import TelegramWebhookView

router = DefaultRouter()
router.register("leads", LeadViewSet, basename="lead")

urlpatterns = [
    path("tracker.js", tracker_js_view, name="mini_tracker_js"),
    path("track/", include("tracker.urls")),
    path("auth/register/", RegisterView.as_view(), name="mini_register"),
    path("auth/login/", LoginView.as_view(), name="mini_login"),
    path("auth/logout/", LogoutView.as_view(), name="mini_logout"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="mini_change_password"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="mini_token_refresh"),
    path("public/lead/", PublicLeadCreateView.as_view(), name="mini_public_lead"),
    path("public/event/", PublicEventCreateView.as_view(), name="mini_public_event"),
    path("analytics/event/", PublicAnalyticsEventCreateView.as_view(), name="mini_analytics_event"),
    path("public/telegram/webhook/", TelegramWebhookView.as_view(), name="mini_telegram_webhook"),
    path("subscriptions/yookassa/webhook/", YooKassaWebhookView.as_view(), name="mini_yookassa_webhook_subscriptions"),
    path("payments/yookassa/webhook/", YooKassaWebhookView.as_view(), name="mini_yookassa_webhook"),
    path("analytics/overview/", AnalyticsOverviewView.as_view(), name="mini_analytics_overview"),
    path("analytics/engagement/", AnalyticsEngagementView.as_view(), name="mini_analytics_engagement"),
    path("analytics/devices/", AnalyticsDevicesView.as_view(), name="mini_analytics_devices"),
    path("analytics/unique-daily/", AnalyticsUniqueDailyView.as_view(), name="mini_analytics_unique_daily"),
    path("analytics/summary/", AnalyticsSummaryView.as_view(), name="mini_analytics_summary"),
    path("analytics/ai-recommendations/", AnalyticsAiRecommendationsView.as_view(), name="mini_analytics_ai_recommendations"),
    path("seo/", include("seo_audit.urls")),
    path("reports/", include("reports.urls")),
    path("subscription/", include("subscriptions.urls")),
    path("settings/", ClientSettingsView.as_view(), name="mini_settings"),
    path("client/settings/", ClientSettingsView.as_view(), name="mini_client_settings"),
    path("client/telegram/", TelegramIntegrationStatusView.as_view(), name="mini_client_telegram_status"),
    path("client/telegram/test/", TelegramIntegrationSendTestView.as_view(), name="mini_client_telegram_test"),
    path("client/telegram/disconnect/", TelegramIntegrationDisconnectView.as_view(), name="mini_client_telegram_disconnect"),
    path("", include(router.urls)),
]
