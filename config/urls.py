from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.sites.views import PublicSiteBundleBySlugView

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
                "media": "/api/client/media/",
                "health": "/api/health/",
            },
        }
    )


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_root),
    path("api/health/", healthcheck),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/public/", include("apps.sites.public_urls")),
    path("api/sites/<slug:site_slug>/", PublicSiteBundleBySlugView.as_view(), name="public-site-bundle"),
    path("api/admin/", include("apps.sites.admin_urls")),
    path("api/client/media/", include("apps.mediafiles.client_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
