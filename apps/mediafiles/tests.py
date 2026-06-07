import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.sites.models import Site

from .models import MediaFile


class MediaUploadTests(APITestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()

        self.user = get_user_model().objects.create_user(
            username="media-owner",
            email="media@example.com",
            password="test-test",
        )
        self.site = Site.objects.create(
            name="A Meditation",
            slug="a-meditation",
            domain="localhost:5173",
            owner=self.user,
        )
        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.settings_override.disable()
        self.media_dir.cleanup()

    def test_reupload_same_file_replaces_media_record(self):
        url = reverse("upload-file")
        payload = {
            "site": str(self.site.id),
            "section": "hero",
            "field": "image",
            "file": SimpleUploadedFile("cover.png", b"first", content_type="image/png"),
        }
        first = self.client.post(url, payload, format="multipart")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        payload["file"] = SimpleUploadedFile("cover.png", b"second", content_type="image/png")
        second = self.client.post(url, payload, format="multipart")

        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MediaFile.objects.count(), 1)
        self.assertTrue(second.data["path"].startswith("/media/sites/a-meditation/hero/"))
