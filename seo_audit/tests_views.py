# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from clients.models import Client
from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit
from subscriptions.models import Subscription


class SEOAuditViewsExtendedTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="seo-view-owner",
            email="seo-view-owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="SEO Views Client")
        Subscription.objects.create(
            client=self.client_obj,
            status=Subscription.Status.ACTIVE,
            paid_until=timezone.now() + timedelta(days=30),
            admin_override=True,
        )
        self.http = APIClient()
        self.http.force_authenticate(user=self.user)

    def _create_done_audit(self, *, domain: str, has_robots: bool, has_sitemap: bool, issue_type: str, severity: str):
        audit = SiteSEOAudit.objects.create(
            client=self.client_obj,
            domain=domain,
            status=SiteSEOAudit.Status.DONE,
            has_robots_txt=has_robots,
            has_sitemap_xml=has_sitemap,
            pages_count=1,
            pages_with_speed_issues=1,
            pages_with_indexing_issues=1,
            seo_score=60,
            finished_at=timezone.now(),
        )
        page = SEOPage.objects.create(
            audit=audit,
            url=f"https://{domain}/",
            status_code=200,
            ttfb_ms=900,
            performance_score=55,
            speed_status=SEOPage.SpeedStatus.WARNING,
            indexability_status=SEOPage.IndexabilityStatus.UNKNOWN,
            title="Example title",
            description="Example description",
            h1="Example",
            h1_count=1,
            word_count=400,
            has_form=True,
            has_cta=True,
            has_phone_or_contact=False,
            has_messenger=False,
            has_offer_like_heading=True,
            has_benefits_block=False,
            has_faq=False,
            commercial_readiness_score=52,
            commercial_status=SEOPage.CommercialStatus.WARNING,
        )
        SEOIssue.objects.create(
            page=page,
            issue_type=issue_type,
            severity=severity,
            recommendation="-",
        )
        return audit

    def test_detail_payload_contains_product_sections(self):
        audit = self._create_done_audit(
            domain="details.example.com",
            has_robots=False,
            has_sitemap=False,
            issue_type="missing_title",
            severity=SEOIssue.Severity.HIGH,
        )

        response = self.http.get(f"/api/seo/{audit.id}/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("fix_plan", payload)
        self.assertIn("issue_groups", payload)
        self.assertIn("commercial_summary", payload)
        self.assertIn("audit_history", payload)
        self.assertIn("comparison_preview", payload)
        self.assertIn("recommendations", payload)
        self.assertEqual(payload["recommendations"]["source"], "local")
        pages = payload.get("commercial_summary", {}).get("pages") or []
        self.assertTrue(len(pages) >= 1)
        page = pages[0]
        self.assertIn("has_conversion_path", page)
        self.assertIn("conversion_path_type", page)
        self.assertIn("conversion_signals", page)
        self.assertIn("commercial_explanation", page)
        self.assertIn("commercial_business_status", page)

    def test_history_endpoint_returns_done_rows_and_default_compare_id(self):
        domain = "history.example.com"
        old_audit = self._create_done_audit(
            domain=domain,
            has_robots=False,
            has_sitemap=False,
            issue_type="missing_title",
            severity=SEOIssue.Severity.HIGH,
        )
        current_audit = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.MEDIUM,
        )

        response = self.http.get(f"/api/seo/{current_audit.id}/history/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["audit_id"], current_audit.id)
        self.assertEqual(payload["domain"], domain)
        self.assertEqual(len(payload["rows"]), 1)
        self.assertEqual(payload["rows"][0]["audit_id"], old_audit.id)
        self.assertEqual(payload["default_compare_audit_id"], old_audit.id)

    def test_audits_list_pages_and_issues_endpoints(self):
        audit = self._create_done_audit(
            domain="list.example.com",
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.MEDIUM,
        )

        list_response = self.http.get("/api/seo/audits/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["rows"][0]["audit_id"], audit.id)

        pages_response = self.http.get(f"/api/seo/{audit.id}/pages/")
        self.assertEqual(pages_response.status_code, 200)
        self.assertGreaterEqual(pages_response.json()["count"], 1)

        issues_response = self.http.get(f"/api/seo/{audit.id}/issues/?severity=medium")
        self.assertEqual(issues_response.status_code, 200)
        self.assertEqual(issues_response.json()["severity"], "medium")
        self.assertGreaterEqual(issues_response.json()["count"], 1)

    def test_compare_endpoint_returns_stub_when_previous_is_missing(self):
        audit = self._create_done_audit(
            domain="single-compare.example.com",
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(f"/api/seo/{audit.id}/compare/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["has_data"])
        self.assertIn("reason", payload)

    def test_compare_endpoint_returns_data_for_selected_audits(self):
        domain = "compare.example.com"
        previous = self._create_done_audit(
            domain=domain,
            has_robots=False,
            has_sitemap=False,
            issue_type="missing_title",
            severity=SEOIssue.Severity.HIGH,
        )
        current = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(f"/api/seo/{current.id}/compare/", {"with_audit_id": previous.id})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["has_data"])
        self.assertEqual(payload["with_audit_id"], previous.id)
        self.assertIn("score", payload)
        self.assertIn("new_issues_count", payload)
        self.assertIn("fixed_issues_count", payload)

    def test_ai_recommendations_endpoint_returns_local_payload(self):
        audit = self._create_done_audit(
            domain="ai-seo.example.com",
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.MEDIUM,
        )

        response = self.http.get(f"/api/seo/{audit.id}/ai-recommendations/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["source"], "local")
        self.assertIn("items", payload)
        self.assertIn("summary", payload)

    def test_ai_recommendations_endpoint_ignores_force_refresh_and_returns_local_payload(self):
        audit = self._create_done_audit(
            domain="ai-refresh.example.com",
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(f"/api/seo/{audit.id}/ai-recommendations/?refresh=1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source"], "local")
        self.assertIn("items", payload)

    def test_export_endpoint_returns_pdf_report(self):
        domain = "export.example.com"
        previous = self._create_done_audit(
            domain=domain,
            has_robots=False,
            has_sitemap=False,
            issue_type="missing_title",
            severity=SEOIssue.Severity.HIGH,
        )
        current = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(
            f"/api/seo/{current.id}/export/",
            {"with_audit_id": previous.id},
            HTTP_ACCEPT="application/pdf",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response["Content-Type"])
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertIn(".pdf", response["Content-Disposition"].lower())
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_export_endpoint_works_with_json_accept_too(self):
        domain = "export-json.example.com"
        audit = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(f"/api/seo/{audit.id}/export/", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response["Content-Type"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_export_endpoint_works_with_browser_like_accept_header(self):
        domain = "export-browser.example.com"
        audit = self._create_done_audit(
            domain=domain,
            has_robots=True,
            has_sitemap=True,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
        )

        response = self.http.get(
            f"/api/seo/{audit.id}/export/",
            HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response["Content-Type"])
        self.assertTrue(response.content.startswith(b"%PDF"))
