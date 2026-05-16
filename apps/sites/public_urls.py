from django.urls import path

from .views import PublicSiteDetailView, PublicSiteListView, PublicSiteSectionsListView

urlpatterns = [
    path("sites/", PublicSiteListView.as_view(), name="public-sites-list"),
    path("sites/<slug:slug>/", PublicSiteDetailView.as_view(), name="public-sites-detail"),
    path(
        "sites/<slug:slug>/sections/",
        PublicSiteSectionsListView.as_view(),
        name="public-sites-sections",
    ),
]
