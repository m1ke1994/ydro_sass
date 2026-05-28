import logging
from zoneinfo import ZoneInfo

from celery import shared_task
from django.utils import timezone

from reports.models import ReportSettings
from reports.services.pdf_generator import build_pdf_for_client
from reports.services.telegram_sender import send_pdf_to_client_telegram

logger = logging.getLogger(__name__)


@shared_task
def send_daily_pdf_task() -> int:
    now_msk = timezone.now().astimezone(ZoneInfo("Europe/Moscow"))
    if now_msk.hour != 20:
        return 0

    sent_count = 0
    for settings_obj in ReportSettings.objects.select_related("client").filter(daily_pdf_enabled=True):
        try:
            if settings_obj.last_sent_at:
                last_msk = settings_obj.last_sent_at.astimezone(ZoneInfo("Europe/Moscow"))
                if last_msk.date() == now_msk.date():
                    continue

            owner_user = getattr(settings_obj.client, "owner", None)
            pdf_bytes, filename = build_pdf_for_client(client=settings_obj.client, user=owner_user)
            send_pdf_to_client_telegram(client=settings_obj.client, filename=filename, pdf_bytes=pdf_bytes)

            settings_obj.last_sent_at = timezone.now()
            settings_obj.last_error = ""
            settings_obj.save(update_fields=["last_sent_at", "last_error", "updated_at"])
            sent_count += 1
        except Exception as exc:
            logger.exception("Failed to send daily PDF for client_id=%s", settings_obj.client_id)
            settings_obj.last_error = str(exc)
            settings_obj.save(update_fields=["last_error", "updated_at"])

    return sent_count
