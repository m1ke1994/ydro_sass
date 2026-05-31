from datetime import timedelta
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from clients.models import Client
from reports.models import ReportSettings
from reports.services.pdf_generator import build_pdf_for_client
from reports.services.telegram_sender import send_pdf_to_client_telegram

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate daily PDF reports and send them to Telegram for active clients."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24, help="Time window in hours (default: 24).")
        parser.add_argument("--client-id", type=int, default=None, help="Process only one client id.")

    def handle(self, *args, **options):
        hours = max(1, int(options["hours"] or 24))
        client_id = options.get("client_id")
        date_to = timezone.localdate()
        date_from = timezone.localdate() - timedelta(days=1 if hours <= 24 else max(1, hours // 24))

        clients_qs = Client.objects.filter(is_active=True).select_related("owner").order_by("id")
        if client_id:
            clients_qs = clients_qs.filter(id=client_id)

        processed = 0
        sent = 0
        skipped = 0
        failed = 0

        for client in clients_qs:
            processed += 1
            settings_obj, _ = ReportSettings.objects.get_or_create(client=client)
            owner = getattr(client, "owner", None)
            try:
                pdf_bytes, filename = build_pdf_for_client(
                    client=client,
                    user=owner,
                    date_from=date_from,
                    date_to=date_to,
                )
            except Exception as exc:
                failed += 1
                settings_obj.last_error = str(exc)
                settings_obj.save(update_fields=["last_error", "updated_at"])
                logger.exception("daily_reports failed to build pdf client_id=%s", client.id)
                continue

            if not client.telegram_chat_id or not client.send_to_telegram:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f"skip client_id={client.id}: telegram not connected or disabled")
                )
                continue

            try:
                send_pdf_to_client_telegram(client=client, filename=filename, pdf_bytes=pdf_bytes)
                sent += 1
                settings_obj.last_sent_at = timezone.now()
                settings_obj.last_error = ""
                settings_obj.save(update_fields=["last_sent_at", "last_error", "updated_at"])
                self.stdout.write(self.style.SUCCESS(f"sent client_id={client.id} filename={filename}"))
            except Exception as exc:
                failed += 1
                settings_obj.last_error = str(exc)
                settings_obj.save(update_fields=["last_error", "updated_at"])
                logger.exception("daily_reports failed to send telegram client_id=%s", client.id)

        self.stdout.write(
            f"done processed={processed} sent={sent} skipped={skipped} failed={failed} "
            f"period={date_from:%d.%m.%Y}-{date_to:%d.%m.%Y}"
        )
