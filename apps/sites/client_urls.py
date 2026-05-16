from django.urls import path

from .views import (
    ClientSiteSectionDetailUpdateView,
    ClientSiteSectionFormView,
    ClientSiteSectionsListView,
    ClientSiteView,
)

urlpatterns = [
    path("site/", ClientSiteView.as_view(), name="client-site"),
    path("sections/", ClientSiteSectionsListView.as_view(), name="client-sections"),
    path(
        "sections/<slug:slug>/form/",
        ClientSiteSectionFormView.as_view(),
        name="client-section-form",
    ),
    path(
        "sections/<slug:slug>/",
        ClientSiteSectionDetailUpdateView.as_view(),
        name="client-section-detail-update",
    ),
]
