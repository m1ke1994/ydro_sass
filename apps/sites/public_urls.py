from django.urls import path

from .views import PublicSiteDetailView, PublicSiteSectionsListView

urlpatterns = [
    path("sites/<slug:slug>/", PublicSiteDetailView.as_view(), name="public-sites-detail"),
    path(
        "sites/<slug:slug>/sections/",
        PublicSiteSectionsListView.as_view(),
        name="public-sites-sections",
    ),
]
