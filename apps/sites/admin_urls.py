from django.urls import path

from .views import (
    AdminMySiteDetailView,
    AdminMySiteSectionDetailView,
    AdminMySiteSectionsListCreateView,
    AdminMySitesListView,
)

urlpatterns = [
    path("my-sites/", AdminMySitesListView.as_view(), name="admin-my-sites"),
    path("my-sites/<int:site_id>/", AdminMySiteDetailView.as_view(), name="admin-my-site-detail"),
    path(
        "my-sites/<int:site_id>/sections/",
        AdminMySiteSectionsListCreateView.as_view(),
        name="admin-my-site-sections",
    ),
    path(
        "my-sites/<int:site_id>/sections/<int:section_id>/",
        AdminMySiteSectionDetailView.as_view(),
        name="admin-my-site-section-detail",
    ),
]
