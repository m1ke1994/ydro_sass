from django.urls import path

from .views import (
    AdminMyLeadDetailView,
    AdminMyLeadsListView,
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
    path("leads/", AdminMyLeadsListView.as_view(), name="admin-leads-list"),
    path("leads/<int:lead_id>/", AdminMyLeadDetailView.as_view(), name="admin-lead-detail"),
]
