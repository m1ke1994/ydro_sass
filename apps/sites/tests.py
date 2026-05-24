from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.sites.models import Site, SiteSection


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
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.content["title"], "Updated")

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
