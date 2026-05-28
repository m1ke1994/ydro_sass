from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.analytics.views import tracker_js_view
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
                "admin": "/api/admin/",
                "tracking": "/api/track/",
                "media": "/api/client/media/",
                "uploads": "/api/uploads/",
                "leads": "/api/leads/",
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
    path("api/track/", include("apps.analytics.public_urls")),
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
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
