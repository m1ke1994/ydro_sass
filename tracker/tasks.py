import logging
from html import escape
from urllib.parse import urlparse

from celery import shared_task
from django.utils import timezone

from clients.models import Client
from leads.services import send_telegram_message
from tracker.models import Event

logger = logging.getLogger(__name__)


def _safe_text(value, *, fallback: str = "-", max_len: int = 1024) -> str:
    text = (value or "").strip()
    if not text:
        return fallback
    return text[:max_len]


def _escape_html(value: str) -> str:
    return escape(value, quote=True)


@shared_task
def send_tracker_form_submit_notification_task(event_id: int, client_id: int) -> None:
    try:
        event = Event.objects.select_related("visit", "visit__site").get(id=event_id)
        client = Client.objects.get(id=client_id, is_active=True)
    except (Event.DoesNotExist, Client.DoesNotExist):
        return

    if event.type != "form_submit":
        return
    if not client.send_to_telegram or not client.telegram_chat_id:
        return

    payload = event.payload if isinstance(event.payload, dict) else {}
    if payload.get("telegram_notified") is True:
        return

    page_url = _safe_text(payload.get("page_url") or payload.get("url"), fallback="")
    page_path = _safe_text(payload.get("path"), fallback="")
    if not page_path and page_url:
        parsed_page_url = urlparse(page_url)
        page_path = _safe_text(parsed_page_url.path, fallback="/", max_len=256)
        if parsed_page_url.query:
            page_path = f"{page_path}?{parsed_page_url.query}"[:512]
    if not page_path:
        page_path = "/"

    site_name = _safe_text(payload.get("domain"), fallback="")
    if not site_name and page_url:
        site_name = _safe_text(urlparse(page_url).netloc, fallback="", max_len=255)
    if not site_name:
        site_name = _safe_text(event.visit.site.domain, fallback="unknown", max_len=255)

    local_time = timezone.localtime(event.timestamp).strftime("%d.%m.%Y %H:%M")
    form_method = _safe_text(payload.get("method"), fallback="-", max_len=16).upper()
    form_action = _safe_text(payload.get("action"), fallback="-", max_len=1024)

    safe_site = _escape_html(site_name)
    safe_page = _escape_html(page_path)
    safe_form = _escape_html(form_action)
    safe_timestamp = _escape_html(local_time)
    safe_method = _escape_html(form_method)

    message = (
        f"📥 <b>Новый лид</b>\n\n"
        f"🌐 <b>Сайт:</b> <code>{safe_site}</code>\n"
        f"📄 <b>Страница:</b> <code>{safe_page}</code>\n"
        f"🕒 <b>Время:</b> {safe_timestamp}\n"
        f"⚙️ <b>Метод:</b> {safe_method}\n\n"
        f"🧾 <b>Форма:</b>\n"
        f"{safe_form}\n\n"
        f"ℹ️ <i>Для подробной информации зайдите в админ-панель сайта.</i>"
    )

    try:
        delivered = send_telegram_message(client.telegram_chat_id, message, parse_mode="HTML")
        if delivered:
            payload_for_update = dict(payload)
            payload_for_update["telegram_notified"] = True
            payload_for_update["telegram_notified_at"] = timezone.now().isoformat()
            event.payload = payload_for_update
            event.save(update_fields=["payload"])
    except Exception:
        logger.exception(
            "tracker.form_submit telegram notify failed event_id=%s client_id=%s",
            event_id,
            client_id,
        )
