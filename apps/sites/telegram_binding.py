import time

from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36

from apps.sites.models import Site

TELEGRAM_SITE_BIND_PREFIX = "site_"
TELEGRAM_SITE_BIND_SALT = "apps.sites.telegram.bind.v1"


def build_site_start_payload(site: Site) -> str:
    issued_at = int(time.time())
    timestamp = int_to_base36(issued_at)
    signature_input = f"{site.id}:{site.api_key}:{issued_at}"
    signature = salted_hmac(TELEGRAM_SITE_BIND_SALT, signature_input).hexdigest()[:20]
    return f"{TELEGRAM_SITE_BIND_PREFIX}{site.id}_{timestamp}_{signature}"


def resolve_site_start_payload(start_payload: str) -> Site | None:
    if not start_payload or not start_payload.startswith(TELEGRAM_SITE_BIND_PREFIX):
        return None

    token = start_payload[len(TELEGRAM_SITE_BIND_PREFIX):]
    parts = token.split("_")
    if len(parts) != 3:
        return None

    site_id_raw, timestamp_raw, signature = parts
    if not site_id_raw.isdigit() or not signature:
        return None

    try:
        issued_at = base36_to_int(timestamp_raw)
    except ValueError:
        return None

    max_age_seconds = int(getattr(settings, "TELEGRAM_BIND_TOKEN_MAX_AGE", "3600"))
    if time.time() - issued_at > max_age_seconds:
        return None

    site = Site.objects.filter(id=int(site_id_raw), is_active=True).first()
    if site is None:
        return None

    expected_input = f"{site.id}:{site.api_key}:{issued_at}"
    expected_signature = salted_hmac(TELEGRAM_SITE_BIND_SALT, expected_input).hexdigest()[:20]
    if not constant_time_compare(signature, expected_signature):
        return None
    return site
