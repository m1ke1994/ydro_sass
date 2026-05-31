# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from clients.models import Client
from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit
from seo_audit.services.crawler import _collect_commercial_signals, _score_commercial_signals, crawl_site_audit
from seo_audit.services.messages import get_commercial_recommendations

from bs4 import BeautifulSoup


class _FakeResponse:
    def __init__(self, url, status_code=200, text="", headers=None, apparent_encoding="utf-8", history=None):
        self.url = url
        self.status_code = status_code
        self.text = text
        self.headers = headers or {"Content-Type": "text/html; charset=utf-8"}
        self.apparent_encoding = apparent_encoding
        self.encoding = None
        self.history = history or []
        self.content = str(text or "").encode("utf-8")


class SEOCrawlerServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="seo-owner", email="seo-owner@example.com", password="pass12345")
        self.client_obj = Client.objects.create(owner=self.user, name="SEO Client")

    def test_crawler_creates_pages_and_issues(self):
        audit = SiteSEOAudit.objects.create(client=self.client_obj, domain="example.com")

        pages = {
            "https://example.com/": _FakeResponse(
                url="https://example.com/",
                text="""
                <html>
                  <head>
                    <title>Home page title for SEO checks</title>
                    <meta name="description" content="Main page description text">
                  </head>
                  <body>
                    <h1>Home</h1>
                    <p>Welcome to the home page.</p>
                    <section class="benefits">
                      <ul>
                        <li>Fast onboarding</li>
                        <li>Transparent pricing</li>
                        <li>Dedicated support</li>
                        <li>Growth tracking</li>
                      </ul>
                    </section>
                    <form action="/lead" method="post">
                      <input type="text" name="name">
                      <button type="submit">Оставить заявку</button>
                    </form>
                    <a href="tel:+79990001122">+7 (999) 000-11-22</a>
                    <a href="/about">About</a>
                    <a href="https://external.example.org/">External</a>
                  </body>
                </html>
                """,
            ),
            "https://example.com/about": _FakeResponse(
                url="https://example.com/about",
                text="""
                <html>
                  <head>
                    <title>Short</title>
                  </head>
                  <body>
                    <h1>About</h1>
                    <h1>Second heading</h1>
                    <p>About page text content.</p>
                    <section id="faq">
                      <h2>FAQ</h2>
                      <details><summary>Question?</summary><p>Answer.</p></details>
                    </section>
                    <a href="/missing">Broken page</a>
                  </body>
                </html>
                """,
            ),
            "https://example.com/missing": _FakeResponse(
                url="https://example.com/missing",
                status_code=404,
                text="<html><head></head><body><p>Not found</p></body></html>",
            ),
            "https://example.com/robots.txt": _FakeResponse(
                url="https://example.com/robots.txt",
                headers={"Content-Type": "text/plain; charset=utf-8"},
                text="User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n",
            ),
            "https://example.com/sitemap.xml": _FakeResponse(
                url="https://example.com/sitemap.xml",
                headers={"Content-Type": "application/xml; charset=utf-8"},
                text="""
                <?xml version="1.0" encoding="UTF-8"?>
                <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                  <url><loc>https://example.com/</loc></url>
                  <url><loc>https://example.com/about</loc></url>
                  <url><loc>https://example.com/missing?utm=ad#top</loc></url>
                </urlset>
                """,
            ),
        }

        def fake_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url")
            if url is None and len(args) >= 2:
                url = args[1]
            normalized = str(url).rstrip("/") or str(url)
            if str(url) == "https://example.com/":
                normalized = "https://example.com/"
            if normalized not in pages:
                raise AssertionError(f"Unexpected URL requested: {url}")
            return pages[normalized]

        with patch("seo_audit.services.crawler.requests.Session.get", side_effect=fake_get):
            crawl_site_audit(audit)

        audit.refresh_from_db()
        self.assertEqual(audit.status, SiteSEOAudit.Status.PENDING)
        self.assertTrue(audit.used_sitemap)
        self.assertTrue(audit.has_robots_txt)
        self.assertTrue(audit.has_sitemap_xml)
        self.assertEqual(audit.sitemap_urls_count, 3)
        self.assertGreaterEqual(audit.pages_count, 2)
        self.assertGreaterEqual(audit.avg_ttfb_ms, 0)
        self.assertGreaterEqual(audit.avg_performance_score, 0)
        self.assertTrue(SEOPage.objects.filter(audit=audit, url="https://example.com/about").exists())
        self.assertTrue(SEOPage.objects.filter(audit=audit, url="https://example.com/about", in_sitemap=True).exists())
        self.assertGreater(SEOIssue.objects.filter(page__audit=audit).count(), 0)
        self.assertTrue(SEOIssue.objects.filter(page__audit=audit, issue_type="missing_description").exists())
        self.assertTrue(SEOIssue.objects.filter(page__audit=audit, issue_type="multiple_h1").exists())
        self.assertTrue(SEOIssue.objects.filter(page__audit=audit, issue_type="bad_status").exists())
        self.assertTrue(SEOIssue.objects.filter(page__audit=audit, issue_type="missing_canonical").exists())

        home_page = SEOPage.objects.get(audit=audit, url="https://example.com/")
        self.assertTrue(home_page.has_form)
        self.assertTrue(home_page.has_cta)
        self.assertTrue(home_page.has_phone_or_contact)
        self.assertTrue(home_page.has_benefits_block)
        self.assertGreater(home_page.commercial_readiness_score, 0)
        self.assertIn(
            home_page.commercial_status,
            {
                SEOPage.CommercialStatus.GOOD,
                SEOPage.CommercialStatus.WARNING,
                SEOPage.CommercialStatus.CRITICAL,
            },
        )
        self.assertTrue(home_page.has_conversion_path)
        self.assertIn(
            home_page.conversion_path_type,
            {
                SEOPage.ConversionPathType.FORM,
                SEOPage.ConversionPathType.MIXED,
            },
        )
        self.assertIsInstance(home_page.commercial_signals_payload, dict)
        self.assertIn("conversion_signals", home_page.commercial_signals_payload)

    def test_crawler_falls_back_to_internal_links_without_sitemap(self):
        audit = SiteSEOAudit.objects.create(client=self.client_obj, domain="example.com")
        pages = {
            "https://example.com/": _FakeResponse(
                url="https://example.com/",
                text="""
                <html>
                  <head><title>Main page for fallback crawl</title></head>
                  <body>
                    <h1>Main</h1>
                    <a href="/about">About</a>
                  </body>
                </html>
                """,
            ),
            "https://example.com/about": _FakeResponse(
                url="https://example.com/about",
                text="""
                <html>
                  <head><title>About fallback page title</title></head>
                  <body><h1>About</h1></body>
                </html>
                """,
            ),
            "https://example.com/robots.txt": _FakeResponse(
                url="https://example.com/robots.txt",
                status_code=404,
                headers={"Content-Type": "text/plain; charset=utf-8"},
                text="",
            ),
            "https://example.com/sitemap.xml": _FakeResponse(
                url="https://example.com/sitemap.xml",
                status_code=404,
                headers={"Content-Type": "text/plain; charset=utf-8"},
                text="",
            ),
        }

        def fake_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url")
            if url is None and len(args) >= 2:
                url = args[1]
            normalized = str(url).rstrip("/") or str(url)
            if str(url) == "https://example.com/":
                normalized = "https://example.com/"
            if normalized not in pages:
                raise AssertionError(f"Unexpected URL requested: {url}")
            return pages[normalized]

        with patch("seo_audit.services.crawler.requests.Session.get", side_effect=fake_get):
            crawl_site_audit(audit)

        audit.refresh_from_db()
        self.assertFalse(audit.used_sitemap)
        self.assertFalse(audit.has_sitemap_xml)
        self.assertTrue(SEOPage.objects.filter(audit=audit, url="https://example.com/about").exists())
        self.assertTrue(
            SEOIssue.objects.filter(page__audit=audit, issue_type__in=["missing_sitemap", "bad_sitemap_status"]).exists()
        )

    def test_commercial_signals_detect_messenger_conversion_without_form(self):
        soup = BeautifulSoup(
            """
            <html>
              <body>
                <section class="contact-card">
                  <h2>Выберите удобный канал связи</h2>
                  <a href="https://t.me/mycompany">Telegram</a>
                  <a href="https://vk.com/mycompany">VK</a>
                </section>
              </body>
            </html>
            """,
            "html.parser",
        )
        signals = _collect_commercial_signals(soup)
        score, status = _score_commercial_signals(signals)

        self.assertTrue(signals["has_conversion_path"])
        self.assertIn(
            signals["conversion_path_type"],
            {SEOPage.ConversionPathType.MESSENGER, SEOPage.ConversionPathType.MIXED},
        )
        self.assertTrue(signals["has_messenger_contact"])
        self.assertGreaterEqual(score, 35)
        self.assertIn(status, {SEOPage.CommercialStatus.WARNING, SEOPage.CommercialStatus.GOOD})

        recommendations = get_commercial_recommendations(
            signals,
            has_conversion_path=signals["has_conversion_path"],
            conversion_path_type=signals["conversion_path_type"],
            score=score,
        )
        self.assertTrue(all("Добавьте контакты для быстрого обращения" not in item for item in recommendations))
        self.assertTrue(all("Добавьте хотя бы один явный сценарий обращения" not in item for item in recommendations))

    def test_commercial_signals_form_only_is_valid_conversion_path(self):
        soup = BeautifulSoup(
            """
            <html>
              <body>
                <form action="/lead">
                  <input type="text" name="name">
                  <input type="tel" name="phone">
                  <button type="submit">Отправить заявку</button>
                </form>
              </body>
            </html>
            """,
            "html.parser",
        )
        signals = _collect_commercial_signals(soup)
        score, status = _score_commercial_signals(signals)
        self.assertTrue(signals["has_conversion_path"])
        self.assertIn(signals["conversion_path_type"], {SEOPage.ConversionPathType.FORM, SEOPage.ConversionPathType.MIXED})
        self.assertGreater(score, 0)
        self.assertIn(status, {SEOPage.CommercialStatus.WARNING, SEOPage.CommercialStatus.GOOD})

    def test_commercial_signals_contacts_only_is_valid_conversion_path(self):
        soup = BeautifulSoup(
            """
            <html>
              <body>
                <section class="contacts">
                  <h2>Свяжитесь с нами</h2>
                  <a href="tel:+79990001122">+7 (999) 000-11-22</a>
                  <a href="mailto:hello@example.com">hello@example.com</a>
                </section>
              </body>
            </html>
            """,
            "html.parser",
        )
        signals = _collect_commercial_signals(soup)
        score, _status = _score_commercial_signals(signals)
        self.assertTrue(signals["has_conversion_path"])
        self.assertIn(
            signals["conversion_path_type"],
            {SEOPage.ConversionPathType.CONTACTS, SEOPage.ConversionPathType.MIXED},
        )
        self.assertGreaterEqual(score, 30)

    def test_commercial_signals_no_conversion_path_returns_none(self):
        soup = BeautifulSoup(
            """
            <html>
              <body>
                <h1>О компании</h1>
                <p>Информационная страница без кнопок и контактов.</p>
              </body>
            </html>
            """,
            "html.parser",
        )
        signals = _collect_commercial_signals(soup)
        score, status = _score_commercial_signals(signals)
        self.assertFalse(signals["has_conversion_path"])
        self.assertEqual(signals["conversion_path_type"], SEOPage.ConversionPathType.NONE)
        self.assertLessEqual(score, 40)
        self.assertEqual(status, SEOPage.CommercialStatus.CRITICAL)

    def test_commercial_signals_widget_counts_as_conversion_path(self):
        soup = BeautifulSoup(
            """
            <html>
              <body>
                <div id="floating-chat-widget" class="chat-widget floating">
                  <a href="https://t.me/helpdesk">Написать</a>
                </div>
              </body>
            </html>
            """,
            "html.parser",
        )
        signals = _collect_commercial_signals(soup)
        self.assertTrue(signals["has_widget"])
        self.assertTrue(signals["has_conversion_path"])
