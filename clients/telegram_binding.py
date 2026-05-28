import time

from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36

from clients.models import Client

TELEGRAM_BIND_PREFIX = "bind_"
TELEGRAM_BIND_SALT = "clients.telegram.bind.v1"


def build_secure_start_payload(client: Client) -> str:
    issued_at = int(time.time())
    timestamp = int_to_base36(issued_at)
    signature_input = f"{client.id}:{client.api_key}:{issued_at}"
    signature = salted_hmac(TELEGRAM_BIND_SALT, signature_input).hexdigest()[:20]
    return f"{TELEGRAM_BIND_PREFIX}{client.id}_{timestamp}_{signature}"


def resolve_secure_start_payload(start_payload: str) -> Client | None:
    if not start_payload or not start_payload.startswith(TELEGRAM_BIND_PREFIX):
        return None

    token = start_payload[len(TELEGRAM_BIND_PREFIX):]
    parts = token.split("_")
    if len(parts) != 3:
        return None

    client_id_raw, timestamp_raw, signature = parts
    if not client_id_raw.isdigit() or not signature:
        return None

    try:
        issued_at = base36_to_int(timestamp_raw)
    except ValueError:
        return None

    max_age_seconds = int(getattr(settings, "TELEGRAM_BIND_TOKEN_MAX_AGE", "3600"))
    if time.time() - issued_at > max_age_seconds:
        return None

    client = Client.objects.filter(id=int(client_id_raw), is_active=True).first()
    if client is None:
        return None

    expected_input = f"{client.id}:{client.api_key}:{issued_at}"
    expected_signature = salted_hmac(TELEGRAM_BIND_SALT, expected_input).hexdigest()[:20]
    if not constant_time_compare(signature, expected_signature):
        return None
    return client
