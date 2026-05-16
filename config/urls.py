from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

admin.site.site_header = "\u041f\u0430\u043d\u0435\u043b\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f"
admin.site.site_title = "\u0410\u0434\u043c\u0438\u043d\u043a\u0430"
admin.site.index_title = "\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/public/", include("apps.sites.public_urls")),
    path("api/client/media/", include("apps.mediafiles.client_urls")),
    path("api/client/", include("apps.sites.client_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
