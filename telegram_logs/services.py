from telegram_logs.models import TelegramUpdateLog


def extract_message(update: dict) -> dict:
    for key in ("message", "edited_message", "channel_post", "edited_channel_post"):
        message = update.get(key)
        if isinstance(message, dict):
            return message
    return {}


def extract_command(text: str | None) -> str | None:
    if not text:
        return None
    text = text.strip()
    if not text.startswith("/"):
        return None
    return text.split()[0].lower()


def save_telegram_update(update: dict) -> tuple[TelegramUpdateLog, bool]:
    update_id = update.get("update_id")
    if update_id is None:
        raise ValueError("Missing update_id in telegram update payload")

    existing = TelegramUpdateLog.objects.filter(update_id=update_id).first()
    if existing:
        return existing, False

    message = extract_message(update)
    chat = message.get("chat", {}) if isinstance(message, dict) else {}
    user = message.get("from", {}) if isinstance(message, dict) else {}
    text = None
    if isinstance(message, dict):
        text = message.get("text") or message.get("caption")
    command = extract_command(text)

    log = TelegramUpdateLog.objects.create(
        update_id=update_id,
        message_id=message.get("message_id") if isinstance(message, dict) else None,
        chat_id=chat.get("id"),
        chat_type=chat.get("type"),
        chat_title=chat.get("title"),
        user_id=user.get("id"),
        username=user.get("username"),
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        text=text,
        command=command,
        payload=update,
    )
    return log, True
