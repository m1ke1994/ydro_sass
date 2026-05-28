from django.urls import path

from .views import AdminSiteAnalyticsSummaryView

urlpatterns = [
    path("my-sites/<int:site_id>/analytics/summary/", AdminSiteAnalyticsSummaryView.as_view(), name="admin-site-analytics-summary"),
]
