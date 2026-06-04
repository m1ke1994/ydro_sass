from celery import shared_task

from leads.models import Lead
from leads.services import send_lead_telegram_notification


@shared_task
def send_lead_notification_task(lead_id: int) -> None:
    try:
        lead = Lead.objects.select_related("client").get(id=lead_id)
    except Lead.DoesNotExist:
        return

    send_lead_telegram_notification(lead, client=lead.client)
