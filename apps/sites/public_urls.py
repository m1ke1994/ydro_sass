from django.urls import path

from .views import (
    PublicSiteByDomainView,
    PublicSiteDetailView,
    PublicSiteLeadCreateBySlugView,
    PublicSiteSectionDetailView,
    PublicSiteSectionsListView,
)

urlpatterns = [
    path("sites/<slug:site_slug>/", PublicSiteDetailView.as_view(), name="public-site-detail"),
    path(
        "sites/<slug:site_slug>/sections/",
        PublicSiteSectionsListView.as_view(),
        name="public-site-sections",
    ),
    path(
        "sites/<slug:site_slug>/sections/<slug:section_key>/",
        PublicSiteSectionDetailView.as_view(),
        name="public-site-section-detail",
    ),
    path("sites/<slug:site_slug>/leads/", PublicSiteLeadCreateBySlugView.as_view(), name="public-site-lead-create"),
    path("by-domain/", PublicSiteByDomainView.as_view(), name="public-site-by-domain"),
]
