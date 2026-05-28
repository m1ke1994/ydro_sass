from django.db import models

from clients.models import Client


class ReportSettings(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="report_settings")
    daily_pdf_enabled = models.BooleanField(default=False)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    last_manual_sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return f"Report settings: client={self.client_id} daily_pdf_enabled={self.daily_pdf_enabled}"
