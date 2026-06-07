import logging
from urllib.parse import parse_qs, urlparse

import requests
from django.conf import settings
from django.utils import timezone
from user_agents import parse as parse_user_agent

logger = logging.getLogger(__name__)

EMPTY_VALUE = "не указано"


def _display_value(value) -> str:
    if value is None:
        return EMPTY_VALUE
    text = str(value).strip()
    if not text or text.lower() == "unknown":
        return EMPTY_VALUE
    return text


def _payload_dict(lead) -> dict:
    payload = getattr(lead, "payload", None)
    if isinstance(payload, dict):
        return payload
    context = getattr(lead, "notification_context", None)
    return context if isinstance(context, dict) else {}


def _url_context(value) -> dict:
    raw_url = str(value or "").strip()
    if not raw_url:
        return {}
    parsed = urlparse(raw_url)
    query = parse_qs(parsed.query or "")
    return {
        "domain": parsed.netloc,
        "page": parsed.path or "/",
        "utm_source": (query.get("utm_source") or [""])[0],
        "utm_medium": (query.get("utm_medium") or [""])[0],
        "utm_campaign": (query.get("utm_campaign") or [""])[0],
        "utm_term": (query.get("utm_term") or [""])[0],
        "utm_content": (query.get("utm_content") or [""])[0],
    }


def _user_agent_context(value) -> dict:
    user_agent_string = str(value or "").strip()
    if not user_agent_string:
        return {}
    try:
        user_agent = parse_user_agent(user_agent_string)
    except Exception:
        return {}

    if user_agent.is_mobile:
        device = "mobile"
    elif user_agent.is_tablet:
        device = "tablet"
    else:
        device = "desktop"
    return {
        "device": device,
        "browser": user_agent.browser.family or "",
        "os": user_agent.os.family or "",
    }


def build_lead_telegram_message(lead, *, client=None, site=None) -> str:
    payload = _payload_dict(lead)
    source_url = getattr(lead, "source_url", None) or payload.get("page_url") or payload.get("url")
    url_context = _url_context(source_url)
    user_agent_context = _user_agent_context(getattr(lead, "user_agent", None) or payload.get("user_agent"))

    resolved_site = site or getattr(lead, "site", None)
    resolved_client = client or getattr(lead, "client", None)
    site_name = getattr(resolved_site, "name", None) or getattr(resolved_client, "name", None)
    site_domain = getattr(resolved_site, "domain", None)
    form_name = (
        getattr(lead, "form_name", None)
        or payload.get("form")
        or payload.get("form_name")
        or payload.get("form_key")
        or payload.get("action")
        or getattr(lead, "section_key", None)
    )
    created_at = timezone.localtime(lead.created_at).strftime("%d.%m.%Y %H:%M")

    return "\n".join(
        [
            "Новая заявка с сайта",
            "",
            f"Сайт: {_display_value(site_name)}",
            f"Домен: {_display_value(payload.get('domain') or site_domain or url_context.get('domain'))}",
            f"Страница: {_display_value(payload.get('page') or url_context.get('page'))}",
            f"Форма: {_display_value(form_name)}",
            "",
            f"Имя: {_display_value(getattr(lead, 'name', None))}",
            f"Телефон: {_display_value(getattr(lead, 'phone', None))}",
            f"Email: {_display_value(getattr(lead, 'email', None))}",
            f"Комментарий: {_display_value(getattr(lead, 'message', None))}",
            "",
            f"Устройство: {_display_value(payload.get('device') or user_agent_context.get('device'))}",
            f"Браузер: {_display_value(payload.get('browser') or user_agent_context.get('browser'))}",
            f"ОС: {_display_value(payload.get('os') or user_agent_context.get('os'))}",
            f"IP: {_display_value(getattr(lead, 'ip_address', None) or payload.get('ip'))}",
            f"Дата: {created_at}",
        ]
    )


def send_lead_telegram_notification(lead, *, client=None, site=None) -> bool:
    resolved_site = site or getattr(lead, "site", None)
    resolved_client = client or getattr(lead, "client", None)
    if (
        resolved_site is not None
        and getattr(resolved_site, "send_to_telegram", False)
        and getattr(resolved_site, "telegram_chat_id", None)
    ):
        message = build_lead_telegram_message(lead, client=resolved_client, site=resolved_site)
        return send_telegram_message(resolved_site.telegram_chat_id, message)

    if resolved_client is None and resolved_site is not None:
        resolved_client = getattr(getattr(resolved_site, "owner", None), "client", None)
    if resolved_client is None or not resolved_client.send_to_telegram or not resolved_client.telegram_chat_id:
        return False
    message = build_lead_telegram_message(lead, client=resolved_client, site=resolved_site)
    return send_telegram_message(resolved_client.telegram_chat_id, message)


def send_telegram_message(chat_id: str, message: str, parse_mode: str | None = None) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.info("Telegram token is not configured, skipping message.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    if parse_mode:
        payload["parse_mode"] = parse_mode
        payload["disable_web_page_preview"] = True
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        body = response.json()
        if not body.get("ok"):
            logger.warning("Telegram sendMessage not ok: chat_id=%s payload=%s", chat_id, body)
            return False
        return True
    except requests.RequestException:
        logger.exception("Failed to send telegram message for chat_id=%s", chat_id)
        return False

