from celery import shared_task
from django.utils import timezone

from leads.models import Lead
from leads.services import send_telegram_message
from leads.utils import normalize_phone


@shared_task
def send_lead_notification_task(lead_id: int) -> None:
    try:
        lead = Lead.objects.select_related("client").get(id=lead_id)
    except Lead.DoesNotExist:
        return

    client = lead.client
    if not client.send_to_telegram or not client.telegram_chat_id:
        return

    local_created_at = timezone.localtime(lead.created_at)
    source_value = lead.source_url or lead.utm_source or lead.utm_campaign or "не указано"

    name_value = (lead.name or "").strip() or "не указано"
    if name_value.lower() == "unknown":
        name_value = "не указано"

    phone_value = normalize_phone(lead.phone) or "не указано"
    email_value = (lead.email or "").strip() or "не указано"
    message_value = (lead.message or "").strip() or "не указано"

    message_lines = [
        "Новая заявка с сайта",
        "",
        f"Сайт: {client.name}",
        f"Имя: {name_value}",
        f"Телефон: {phone_value}",
        f"Email: {email_value}",
        f"Комментарий: {message_value}",
        f"Страница: {source_value}",
        f"Дата: {local_created_at.strftime('%d.%m.%Y %H:%M')}",
    ]
    send_telegram_message(client.telegram_chat_id, "\n".join(message_lines))
