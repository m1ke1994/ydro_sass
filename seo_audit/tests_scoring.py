# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from clients.models import Client
from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit
from seo_audit.services.scoring import (
    build_audit_comparison,
    build_commercial_summary,
    build_fix_plan,
    build_issue_groups,
    recalculate_audit_score,
)


class SEOScoreCalculationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="seo-score-owner",
            email="seo-score-owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="SEO Score Client")

    def test_score_drops_for_unavailable_site_without_robots_and_sitemap(self):
        audit = SiteSEOAudit.objects.create(
            client=self.client_obj,
            domain="broken.example.com",
            has_robots_txt=False,
            has_sitemap_xml=False,
            sitemap_urls_count=0,
        )
        page = SEOPage.objects.create(
            audit=audit,
            url="https://broken.example.com/",
            status_code=0,
            ttfb_ms=4200,
            performance_score=0,
            speed_status=SEOPage.SpeedStatus.CRITICAL,
            indexability_status=SEOPage.IndexabilityStatus.UNKNOWN,
            title="",
            description="",
            h1="",
            h1_count=0,
            canonical_url="",
            in_sitemap=False,
            blocked_by_robots=False,
        )
        SEOIssue.objects.create(page=page, issue_type="network_error", severity=SEOIssue.Severity.HIGH, recommendation="-")
        SEOIssue.objects.create(page=page, issue_type="missing_robots_txt", severity=SEOIssue.Severity.LOW, recommendation="-")
        SEOIssue.objects.create(page=page, issue_type="missing_sitemap", severity=SEOIssue.Severity.MEDIUM, recommendation="-")
        SEOIssue.objects.create(page=page, issue_type="slow_ttfb", severity=SEOIssue.Severity.HIGH, recommendation="-")

        recalculate_audit_score(audit)
        audit.refresh_from_db()

        self.assertLessEqual(audit.seo_score, 35)
        self.assertEqual(audit.pages_count, 1)
        self.assertGreaterEqual(audit.pages_with_speed_issues, 1)
        self.assertGreaterEqual(audit.pages_with_indexing_issues, 1)

    def test_score_remains_high_for_technically_healthy_pages(self):
        audit = SiteSEOAudit.objects.create(
            client=self.client_obj,
            domain="healthy.example.com",
            has_robots_txt=True,
            has_sitemap_xml=True,
            sitemap_urls_count=2,
        )
        SEOPage.objects.create(
            audit=audit,
            url="https://healthy.example.com/",
            status_code=200,
            ttfb_ms=280,
            performance_score=92,
            speed_status=SEOPage.SpeedStatus.GOOD,
            indexability_status=SEOPage.IndexabilityStatus.INDEXABLE,
            title="Healthy Example Home",
            description="Detailed description for search snippets and result quality checks.",
            h1="Home page",
            h1_count=1,
            word_count=520,
            canonical_url="https://healthy.example.com/",
            in_sitemap=True,
            blocked_by_robots=False,
        )
        SEOPage.objects.create(
            audit=audit,
            url="https://healthy.example.com/about",
            status_code=200,
            ttfb_ms=360,
            performance_score=87,
            speed_status=SEOPage.SpeedStatus.GOOD,
            indexability_status=SEOPage.IndexabilityStatus.INDEXABLE,
            title="About Healthy Example Company",
            description="Company page with contacts, key benefits and additional useful details.",
            h1="About company",
            h1_count=1,
            word_count=610,
            canonical_url="https://healthy.example.com/about",
            in_sitemap=True,
            blocked_by_robots=False,
        )

        recalculate_audit_score(audit)
        audit.refresh_from_db()

        self.assertGreaterEqual(audit.seo_score, 80)
        self.assertEqual(audit.pages_count, 2)
        self.assertEqual(audit.pages_with_speed_issues, 0)
        self.assertEqual(audit.pages_with_indexing_issues, 0)


class SEOProductScoringHelpersTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="seo-product-owner",
            email="seo-product-owner@example.com",
            password="pass12345",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="SEO Product Client")

    def test_issue_groups_and_fix_plan_are_built_from_payload(self):
        audit = SiteSEOAudit.objects.create(
            client=self.client_obj,
            domain="grouped.example.com",
            has_robots_txt=False,
            has_sitemap_xml=False,
            pages_count=10,
        )
        issues_payload = [
            {
                "issue_type": "missing_title",
                "issue_title": "Отсутствует title",
                "severity": "high",
                "page_url": "https://grouped.example.com/a",
            },
            {
                "issue_type": "missing_title",
                "issue_title": "Отсутствует title",
                "severity": "high",
                "page_url": "https://grouped.example.com/b",
            },
            {
                "issue_type": "missing_sitemap",
                "issue_title": "Отсутствует sitemap.xml",
                "severity": "medium",
                "page_url": "https://grouped.example.com/",
            },
        ]
        pages_payload = [
            {
                "id": 1,
                "url": "https://grouped.example.com/a",
                "commercial_status": SEOPage.CommercialStatus.CRITICAL,
                "commercial_readiness_score": 20,
                "has_form": False,
                "has_cta": False,
                "has_phone_or_contact": False,
                "has_messenger": False,
                "has_offer_like_heading": False,
                "has_benefits_block": False,
                "has_faq": False,
            },
            {
                "id": 2,
                "url": "https://grouped.example.com/b",
                "commercial_status": SEOPage.CommercialStatus.WARNING,
                "commercial_readiness_score": 52,
                "has_form": True,
                "has_cta": False,
                "has_phone_or_contact": True,
                "has_messenger": False,
                "has_offer_like_heading": False,
                "has_benefits_block": False,
                "has_faq": False,
            },
        ]

        issue_groups = build_issue_groups(issues_payload)
        self.assertGreaterEqual(len(issue_groups), 2)
        missing_title_group = next((item for item in issue_groups if item["issue_type"] == "missing_title"), None)
        self.assertIsNotNone(missing_title_group)
        self.assertEqual(missing_title_group["pages_affected"], 2)
        self.assertEqual(missing_title_group["priority_key"], "urgent")

        commercial_summary = build_commercial_summary(pages_payload)
        self.assertTrue(commercial_summary["has_data"])
        self.assertEqual(commercial_summary["critical_pages"], 1)
        self.assertEqual(commercial_summary["warning_pages"], 1)

        fix_plan = build_fix_plan(
            audit=audit,
            issue_groups=issue_groups,
            commercial_summary=commercial_summary,
        )
        self.assertGreaterEqual(len(fix_plan), 2)
        self.assertEqual(fix_plan[0]["priority_key"], "urgent")
        self.assertTrue(any(item["title"] == "Не найден robots.txt" for item in fix_plan))
        self.assertTrue(any(item["title"] == "Не найден sitemap.xml" for item in fix_plan))

    def test_audit_comparison_reports_new_and_fixed_issues(self):
        domain = "compare.example.com"
        previous = SiteSEOAudit.objects.create(
            client=self.client_obj,
            domain=domain,
            status=SiteSEOAudit.Status.DONE,
            has_robots_txt=False,
            has_sitemap_xml=False,
            pages_with_speed_issues=2,
            pages_with_indexing_issues=3,
        )
        current = SiteSEOAudit.objects.create(
            client=self.client_obj,
            domain=domain,
            status=SiteSEOAudit.Status.DONE,
            has_robots_txt=True,
            has_sitemap_xml=True,
            pages_with_speed_issues=1,
            pages_with_indexing_issues=1,
        )
        previous_page = SEOPage.objects.create(
            audit=previous,
            url="https://compare.example.com/",
            status_code=200,
            ttfb_ms=1200,
            performance_score=48,
            speed_status=SEOPage.SpeedStatus.WARNING,
            indexability_status=SEOPage.IndexabilityStatus.UNKNOWN,
        )
        current_page = SEOPage.objects.create(
            audit=current,
            url="https://compare.example.com/",
            status_code=200,
            ttfb_ms=420,
            performance_score=88,
            speed_status=SEOPage.SpeedStatus.GOOD,
            indexability_status=SEOPage.IndexabilityStatus.INDEXABLE,
        )
        SEOIssue.objects.create(
            page=previous_page,
            issue_type="missing_title",
            severity=SEOIssue.Severity.HIGH,
            recommendation="-",
        )
        SEOIssue.objects.create(
            page=current_page,
            issue_type="missing_description",
            severity=SEOIssue.Severity.LOW,
            recommendation="-",
        )

        comparison = build_audit_comparison(current_audit=current, previous_audit=previous)
        self.assertTrue(comparison["has_data"])
        self.assertIn(comparison["trend"], {"better", "stable", "worse"})
        self.assertEqual(comparison["robots_txt"]["status"], "appeared")
        self.assertEqual(comparison["sitemap_xml"]["status"], "appeared")
        self.assertEqual(comparison["new_issues_count"], 1)
        self.assertEqual(comparison["fixed_issues_count"], 1)

    def test_commercial_summary_detects_alternative_channel_without_hard_negative(self):
        pages_payload = [
            {
                "id": 11,
                "url": "https://channels.example.com/",
                "commercial_status": SEOPage.CommercialStatus.WARNING,
                "commercial_readiness_score": 58,
                "has_form": False,
                "has_cta": False,
                "has_phone_or_contact": True,
                "has_messenger": True,
                "has_offer_like_heading": True,
                "has_benefits_block": False,
                "has_faq": False,
                "has_conversion_path": True,
                "conversion_path_type": SEOPage.ConversionPathType.MESSENGER,
                "commercial_signals_payload": {
                    "conversion_signals": {
                        "has_form": False,
                        "has_cta": False,
                        "has_direct_contact": False,
                        "has_contact_block": True,
                        "has_messenger_contact": True,
                        "has_widget": False,
                        "has_multi_channel_contact": True,
                        "has_offer_like_heading": True,
                        "has_benefits_block": False,
                        "has_faq": False,
                    }
                },
            }
        ]
        summary = build_commercial_summary(pages_payload)
        self.assertTrue(summary["has_data"])
        self.assertEqual(summary["has_channel_pages"], 1)
        self.assertEqual(summary["no_conversion_path_pages"], 0)
        page = summary["pages"][0]
        self.assertTrue(page["has_conversion_path"])
        self.assertIn(page["conversion_path_type"], {"messenger", "mixed"})
        self.assertEqual(page["commercial_business_status"], "has_channel")
        self.assertTrue(
            all("Добавьте хотя бы один явный сценарий обращения" not in item for item in page["commercial_recommendations"])
        )
        self.assertTrue(all("Добавьте контакты для быстрого обращения" not in item for item in page["commercial_recommendations"]))

    def test_commercial_summary_marks_missing_path_as_none(self):
        pages_payload = [
            {
                "id": 12,
                "url": "https://empty-conversion.example.com/",
                "commercial_status": SEOPage.CommercialStatus.CRITICAL,
                "commercial_readiness_score": 10,
                "has_form": False,
                "has_cta": False,
                "has_phone_or_contact": False,
                "has_messenger": False,
                "has_offer_like_heading": False,
                "has_benefits_block": False,
                "has_faq": False,
                "has_conversion_path": False,
                "conversion_path_type": SEOPage.ConversionPathType.NONE,
                "commercial_signals_payload": {},
            }
        ]
        summary = build_commercial_summary(pages_payload)
        self.assertTrue(summary["has_data"])
        self.assertEqual(summary["no_conversion_path_pages"], 1)
        self.assertEqual(summary["weak_pages"], 0)
        page = summary["pages"][0]
        self.assertEqual(page["commercial_business_status"], "none")
        self.assertTrue(any("Добавьте хотя бы один явный сценарий обращения" in item for item in page["commercial_recommendations"]))
