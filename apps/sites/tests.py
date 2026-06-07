from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from apps.sites.models import Site, SiteLead, SiteSection
from apps.sites.a_meditation import (
    A_MEDITATION_SECTION_SEEDS,
    merge_content_defaults,
)
from clients.models import Client


class SitesApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="owner1",
            email="owner1@example.com",
            password="test-test",
        )
        self.other_user = user_model.objects.create_user(
            username="owner2",
            email="owner2@example.com",
            password="test-test",
        )
        self.superuser = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-test",
        )

        self.site = Site.objects.create(
            name="Site One",
            slug="site-one",
            domain="localhost:5173",
            owner=self.user,
            is_active=True,
        )
        self.other_site = Site.objects.create(
            name="Site Two",
            slug="site-two",
            domain="localhost:3000",
            owner=self.other_user,
            is_active=True,
        )
        self.owner_client = Client.objects.create(
            owner=self.user,
            name=self.site.name,
            is_active=True,
            send_to_telegram=True,
            telegram_chat_id="123456",
        )

        self.hero = SiteSection.objects.create(
            site=self.site,
            key="hero",
            title="Hero",
            section_type="hero",
            order=1,
            is_active=True,
            schema={"fields": [{"key": "title", "type": "text"}]},
            content={"title": "Hello"},
        )
        self.hidden = SiteSection.objects.create(
            site=self.site,
            key="hidden",
            title="Hidden",
            section_type="custom",
            order=2,
            is_active=False,
            schema={"fields": [{"key": "title", "type": "text"}]},
            content={"title": "Hidden"},
        )

    def test_public_site_detail_and_sections_only_active(self):
        detail_url = reverse("public-site-detail", kwargs={"site_slug": self.site.slug})
        sections_url = reverse("public-site-sections", kwargs={"site_slug": self.site.slug})

        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["slug"], "site-one")

        sections_response = self.client.get(sections_url)
        self.assertEqual(sections_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(sections_response.data), 1)
        self.assertEqual(sections_response.data[0]["key"], "hero")

    def test_public_section_detail(self):
        url = reverse(
            "public-site-section-detail",
            kwargs={"site_slug": self.site.slug, "section_key": "hero"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"]["title"], "Hello")

    def test_public_by_domain(self):
        url = reverse("public-site-by-domain")
        response = self.client.get(url, {"domain": "localhost:5173"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["site"]["slug"], "site-one")
        self.assertEqual(len(response.data["sections"]), 1)

    def test_admin_my_sites_for_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("admin-my-sites")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], "site-one")

    def test_admin_my_sites_for_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse("admin-my-sites")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_user_cannot_access_foreign_site(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("admin-my-site-detail", kwargs={"site_id": self.other_site.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_patch_own_section_content(self):
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "admin-my-site-section-detail",
            kwargs={"site_id": self.site.id, "section_id": self.hero.id},
        )
        payload = {"content": {"title": "Updated"}}
        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.hero.id)
        self.assertEqual(response.data["display_title"], "Hero")
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.content["title"], "Updated")

    def test_a_meditation_sections_have_russian_display_titles(self):
        meditation_site = Site.objects.create(
            name="A Meditation",
            slug="a-meditation",
            domain="localhost:5173",
            owner=self.user,
            is_active=True,
        )
        section = SiteSection.objects.create(
            site=meditation_site,
            key="hero",
            title="Hero",
            section_type="hero",
            order=1,
            schema={"fields": [{"key": "title", "type": "text"}]},
            content={"title": "Текущий текст"},
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("admin-my-site-sections", kwargs={"site_id": meditation_site.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], section.id)
        self.assertEqual(response.data[0]["display_title"], "Hero-блок")
        self.assertEqual(response.data[0]["content"]["title"], "Текущий текст")

    def test_a_meditation_contract_is_valid_and_merge_keeps_user_values(self):
        for seed in A_MEDITATION_SECTION_SEEDS:
            SiteSection.validate_schema(seed["schema"])
            SiteSection.validate_content(seed["content"], seed["schema"])

        merged = merge_content_defaults(
            {"title": "Новый default", "description": "Описание"},
            {"title": "Текст клиента", "legacy": "Удалить"},
        )
        self.assertEqual(
            merged,
            {"title": "Текст клиента", "description": "Описание"},
        )

    def test_user_cannot_patch_foreign_section(self):
        foreign_section = SiteSection.objects.create(
            site=self.other_site,
            key="hero",
            title="Hero",
            section_type="hero",
            order=1,
            is_active=True,
            schema={"fields": [{"key": "title", "type": "text"}]},
            content={"title": "X"},
        )

        self.client.force_authenticate(user=self.user)
        url = reverse(
            "admin-my-site-section-detail",
            kwargs={"site_id": self.other_site.id, "section_id": foreign_section.id},
        )
        response = self.client.patch(url, {"content": {"title": "Hack"}}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_section_is_soft_delete(self):
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "admin-my-site-section-detail",
            kwargs={"site_id": self.site.id, "section_id": self.hero.id},
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.hero.refresh_from_db()
        self.assertFalse(self.hero.is_active)

    @patch("apps.sites.serializers.send_lead_telegram_notification", return_value=True)
    def test_public_can_create_lead(self, mocked_telegram):
        url = reverse("public-leads-create")
        payload = {
            "site_slug": self.site.slug,
            "section_key": "contacts",
            "form_name": "Форма записи",
            "name": "Александр",
            "phone": "+79990000000",
            "message": "Хочу записаться",
            "service_type": "lila",
            "service_title": "Индивидуальная игра Лила",
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(SiteLead.objects.count(), 1)
        lead = SiteLead.objects.first()
        self.assertEqual(lead.site_id, self.site.id)
        self.assertEqual(lead.status, SiteLead.Status.NEW)
        mocked_telegram.assert_called_once()

    def test_get_request_does_not_create_lead(self):
        response = self.client.get(reverse("public-leads-create"))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(SiteLead.objects.count(), 0)

    @patch("leads.services.send_telegram_message", return_value=True)
    def test_one_site_lead_sends_one_detailed_message_to_its_site_chat(self, mocked_telegram):
        Client.objects.create(
            owner=self.other_user,
            name=self.other_site.name,
            is_active=True,
            send_to_telegram=True,
            telegram_chat_id="other-chat",
        )
        response = self.client.post(
            reverse("public-leads-create"),
            {
                "site_slug": self.site.slug,
                "section_key": "contacts",
                "form_name": "Форма записи",
                "name": "Александр",
                "phone": "+79990000000",
                "email": "alex@example.com",
                "message": "Хочу записаться",
                "source_url": "https://example.com/contact?utm_source=google&utm_medium=cpc&utm_campaign=spring&utm_term=lila&utm_content=hero",
                "payload": {"source": "google ads"},
            },
            format="json",
            HTTP_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            REMOTE_ADDR="203.0.113.10",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_telegram.assert_called_once()
        chat_id, message = mocked_telegram.call_args.args
        self.assertEqual(chat_id, "123456")
        self.assertIn("Новая заявка с сайта", message)
        self.assertIn("Сайт: Site One", message)
        self.assertIn("Домен: localhost:5173", message)
        self.assertIn("Страница: /contact", message)
        self.assertIn("Форма: Форма записи", message)
        self.assertNotIn("Источник:", message)
        self.assertNotIn("UTM source:", message)
        self.assertNotIn("UTM medium:", message)
        self.assertNotIn("UTM campaign:", message)
        self.assertNotIn("UTM term:", message)
        self.assertNotIn("UTM content:", message)
        self.assertIn("Устройство: desktop", message)
        self.assertIn("Браузер: Chrome", message)
        self.assertIn("ОС: Windows", message)
        self.assertIn("IP: 203.0.113.10", message)

    @patch("apps.sites.serializers.send_lead_telegram_notification", return_value=False)
    def test_public_lead_is_saved_even_if_telegram_send_fails(self, mocked_telegram):
        url = reverse("public-leads-create")
        payload = {
            "site_slug": self.site.slug,
            "name": "Иван",
            "phone": "+79990000000",
            "message": "Тестовая заявка",
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SiteLead.objects.count(), 1)
        mocked_telegram.assert_called_once()

    def test_admin_user_sees_only_own_site_leads_and_can_patch_status(self):
        own_lead = SiteLead.objects.create(site=self.site, name="Own", phone="+70000000001")
        foreign_lead = SiteLead.objects.create(site=self.other_site, name="Foreign", phone="+70000000002")

        self.client.force_authenticate(user=self.user)

        list_url = reverse("admin-leads-list")
        list_response = self.client.get(list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], own_lead.id)

        patch_url = reverse("admin-lead-detail", kwargs={"lead_id": own_lead.id})
        patch_response = self.client.patch(patch_url, {"status": SiteLead.Status.DONE}, format="json")
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        own_lead.refresh_from_db()
        self.assertEqual(own_lead.status, SiteLead.Status.DONE)

        foreign_patch_url = reverse("admin-lead-detail", kwargs={"lead_id": foreign_lead.id})
        foreign_patch_response = self.client.patch(
            foreign_patch_url,
            {"status": SiteLead.Status.DONE},
            format="json",
        )
        self.assertEqual(foreign_patch_response.status_code, status.HTTP_404_NOT_FOUND)
