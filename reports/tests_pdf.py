from django.contrib.auth import get_user_model
from django.test import TestCase

from clients.models import Client
from reports.services.pdf_generator import build_pdf_for_client


class ReportPdfGeneratorTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="pdf-owner@example.com",
            email="pdf-owner@example.com",
            password="test-pass-123",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="A Meditation / Амедиа", is_active=True)

    def test_build_pdf_generates_document(self):
        pdf_bytes, filename = build_pdf_for_client(client=self.client_obj, user=self.user)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertIn("tracknode-full-report-client", filename)
