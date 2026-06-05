from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve

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
from leads.views import PublicLeadCreateView as MiniPublicLeadCreateView
from subscriptions.views import YooKassaWebhookView
from telegram_logs.views import TelegramWebhookView

from apps.mediafiles.views import UploadFileView
from apps.sites.views import PublicLeadCreateView, PublicSiteBundleBySlugView

admin.site.site_header = "Панель управления"
admin.site.site_title = "Админка"
admin.site.index_title = "Управление"


def api_root(_request):
    return JsonResponse(
        {
            "status": "ok",
            "endpoints": {
                "auth": "/api/auth/",
                "public": "/api/public/",
                "public_lead_legacy": "/api/public/lead/",
                "admin": "/api/admin/",
                "tracking": "/api/track/",
                "tracking_legacy": "/api/mini/track/",
                "media": "/api/client/media/",
                "uploads": "/api/uploads/",
                "leads": "/api/leads/",
                "analytics": "/api/analytics/",
                "seo": "/api/seo/",
                "reports": "/api/reports/",
                "subscription": "/api/subscription/",
                "mini": "/api/mini/",
                "health": "/api/health/",
            },
        }
    )


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("tracker.js", tracker_js_view, name="tracker-js"),
    path("admin/", admin.site.urls),
    path("api/", api_root),
    path("api/health/", healthcheck),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/mini/", include("config.mini_urls")),
    # Mini SaaS compatibility aliases
    path("api/track/", include("tracker.urls")),
    path("api/public/lead/", MiniPublicLeadCreateView.as_view(), name="public_lead"),
    path("api/public/event/", PublicEventCreateView.as_view(), name="public_event"),
    path("api/analytics/event/", PublicAnalyticsEventCreateView.as_view(), name="analytics_event"),
    path("api/public/telegram/webhook/", TelegramWebhookView.as_view(), name="telegram_webhook"),
    path("api/subscriptions/yookassa/webhook/", YooKassaWebhookView.as_view(), name="yookassa_webhook_subscriptions"),
    path("api/payments/yookassa/webhook/", YooKassaWebhookView.as_view(), name="yookassa_webhook"),
    path("api/analytics/overview/", AnalyticsOverviewView.as_view(), name="analytics_overview"),
    path("api/analytics/engagement/", AnalyticsEngagementView.as_view(), name="analytics_engagement"),
    path("api/analytics/devices/", AnalyticsDevicesView.as_view(), name="analytics_devices"),
    path("api/analytics/unique-daily/", AnalyticsUniqueDailyView.as_view(), name="analytics_unique_daily"),
    path("api/analytics/summary/", AnalyticsSummaryView.as_view(), name="analytics_summary"),
    path(
        "api/analytics/ai-recommendations/",
        AnalyticsAiRecommendationsView.as_view(),
        name="analytics_ai_recommendations",
    ),
    path("api/seo/", include("seo_audit.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/subscription/", include("subscriptions.urls")),
    path("api/settings/", ClientSettingsView.as_view(), name="settings"),
    path("api/client/settings/", ClientSettingsView.as_view(), name="client_settings"),
    # Yadro core endpoints
    path("api/yadro-track/", include("apps.analytics.public_urls")),
    path("api/public/", include("apps.sites.public_urls")),
    path("api/sites/<slug:site_slug>/", PublicSiteBundleBySlugView.as_view(), name="public-site-bundle"),
    path("api/leads/", PublicLeadCreateView.as_view(), name="public-leads-create"),
    path("leads/", PublicLeadCreateView.as_view(), name="public-leads-create-legacy"),
    path("leads", PublicLeadCreateView.as_view(), name="public-leads-create-legacy-no-slash"),
    path("api/admin/", include("apps.sites.admin_urls")),
    path("api/admin/", include("apps.analytics.admin_urls")),
    path("api/uploads/", UploadFileView.as_view(), name="upload-file"),
    path("api/client/media/", include("apps.mediafiles.client_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.SERVE_MEDIA_FILES:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
