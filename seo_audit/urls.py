# -*- coding: utf-8 -*-
from django.urls import path

from seo_audit.views import (
    SEOAuditAiRecommendationsView,
    SEOAuditCompareView,
    SEOAuditDetailView,
    SEOAuditExportView,
    SEOAuditHistoryView,
    SEOAuditLatestView,
    SEOAuditStartView,
    SEOAuditStopView,
)

urlpatterns = [
    path("start/", SEOAuditStartView.as_view(), name="seo_audit_start"),
    path("latest/", SEOAuditLatestView.as_view(), name="seo_audit_latest"),
    path("<int:audit_id>/stop/", SEOAuditStopView.as_view(), name="seo_audit_stop"),
    path("<int:audit_id>/history/", SEOAuditHistoryView.as_view(), name="seo_audit_history"),
    path("<int:audit_id>/compare/", SEOAuditCompareView.as_view(), name="seo_audit_compare"),
    path("<int:audit_id>/ai-recommendations/", SEOAuditAiRecommendationsView.as_view(), name="seo_audit_ai_recommendations"),
    path("<int:audit_id>/export/", SEOAuditExportView.as_view(), name="seo_audit_export"),
    path("<int:audit_id>/", SEOAuditDetailView.as_view(), name="seo_audit_detail"),
]
