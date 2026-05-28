import requests
from django.conf import settings


def send_pdf_to_client_telegram(*, client, filename: str, pdf_bytes: bytes):
    token = (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")

    chat_id = (client.telegram_chat_id or "").strip()
    if not chat_id:
        raise RuntimeError("Telegram chat_id is not configured for this client")

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendDocument",
        data={"chat_id": chat_id, "caption": "PDF отчёт TrackNode"},
        files={"document": (filename, pdf_bytes, "application/pdf")},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(str(payload))
    return True
