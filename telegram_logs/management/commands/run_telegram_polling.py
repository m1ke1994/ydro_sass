import json
import logging
import os
import time
import uuid
from pathlib import Path

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone

from clients.models import Client
from clients.telegram_binding import resolve_secure_start_payload
from subscriptions.models import Subscription, TelegramLink
from telegram_logs.models import TelegramUpdateLog
from telegram_logs.services import extract_message, save_telegram_update

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run Telegram long polling and store updates in TelegramUpdateLog."

    def add_arguments(self, parser):
        parser.add_argument("--offset", type=int, default=None, help="Start polling from this update_id offset.")

    def _acquire_file_lock(self) -> int | None:
        lock_file = Path(str(getattr(settings, "TELEGRAM_POLLING_LOCK_FILE", "/tmp/tracknode_telegram_polling.lock")))
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("utf-8"))
            logger.info("Telegram polling file lock acquired. lock_file=%s pid=%s", lock_file, os.getpid())
            return fd
        except FileExistsError:
            holder_pid = None
            try:
                holder_pid = lock_file.read_text(encoding="utf-8").strip()
            except OSError:
                holder_pid = "unknown"
            logger.error(
                "Telegram polling file lock already exists. lock_file=%s holder_pid=%s current_pid=%s",
                lock_file,
                holder_pid,
                os.getpid(),
            )
            return None
        except OSError:
            logger.exception("Failed to acquire Telegram polling file lock. lock_file=%s", lock_file)
            return None

    def _release_file_lock(self, fd: int | None) -> None:
        lock_file = Path(str(getattr(settings, "TELEGRAM_POLLING_LOCK_FILE", "/tmp/tracknode_telegram_polling.lock")))
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                logger.warning("Failed to close Telegram polling file lock descriptor. pid=%s", os.getpid())
        try:
            if lock_file.exists():
                lock_file.unlink()
        except OSError:
            logger.warning("Failed to remove Telegram polling file lock file. lock_file=%s", lock_file)
        else:
            logger.info("Telegram polling file lock released. lock_file=%s pid=%s", lock_file, os.getpid())

    def _log_webhook_info(self, token: str) -> dict:
        endpoint = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        try:
            response = requests.get(endpoint, timeout=15)
            response.raise_for_status()
            payload = response.json() if response.content else {}
            result = payload.get("result") if isinstance(payload, dict) else {}
            logger.info(
                "Telegram getWebhookInfo: ok=%s url=%r pending_update_count=%s last_error_date=%s last_error_message=%r",
                payload.get("ok") if isinstance(payload, dict) else None,
                result.get("url") if isinstance(result, dict) else "",
                result.get("pending_update_count") if isinstance(result, dict) else None,
                result.get("last_error_date") if isinstance(result, dict) else None,
                result.get("last_error_message") if isinstance(result, dict) else None,
            )
            return result if isinstance(result, dict) else {}
        except requests.RequestException:
            logger.exception("Failed to get Telegram webhook info before polling start.")
            return {}

    def _send_message(self, token: str, chat_id: int, text: str, reply_markup: dict | None = None) -> None:
        endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            response = requests.post(endpoint, json=payload, timeout=15)
            response.raise_for_status()
            response_payload = response.json()
            if not response_payload.get("ok"):
                logger.warning("Telegram sendMessage not ok: chat_id=%s payload=%s", chat_id, response_payload)
        except requests.RequestException:
            logger.exception("Failed to send Telegram message to chat_id=%s", chat_id)

    def _answer_callback(self, token: str, callback_query_id: str, text: str | None = None) -> None:
        endpoint = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        try:
            response = requests.post(endpoint, json=payload, timeout=15)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Failed to answer callback_query_id=%s", callback_query_id)

    def _upsert_telegram_link(self, *, sender_id: int, chat_id: int, client: Client) -> TelegramLink:
        link_by_sender = TelegramLink.objects.filter(telegram_user_id=sender_id).select_related("client").first()
        link_by_client = TelegramLink.objects.filter(client=client).select_related("client").first()

        if link_by_sender and link_by_client and link_by_sender.pk != link_by_client.pk:
            logger.warning(
                "telegram link conflict resolved by sender sender_id=%s chat_id=%s sender_client_id=%s target_client_id=%s",
                sender_id,
                chat_id,
                link_by_sender.client_id,
                client.id,
            )
            link_by_client.delete()

        link = link_by_sender or link_by_client
        if link is None:
            return TelegramLink.objects.create(telegram_user_id=sender_id, telegram_chat_id=chat_id, client=client)

        update_fields = []
        if link.telegram_user_id != sender_id:
            link.telegram_user_id = sender_id
            update_fields.append("telegram_user_id")
        if link.telegram_chat_id != chat_id:
            link.telegram_chat_id = chat_id
            update_fields.append("telegram_chat_id")
        if link.client_id != client.id:
            link.client = client
            update_fields.append("client")
        if update_fields:
            link.save(update_fields=[*update_fields, "updated_at"])
        return link

    def _handle_start_command(self, token: str, text: str | None, chat_id: int | None, sender_id: int | None) -> None:
        if not text or chat_id is None:
            return

        normalized = text.strip()
        if not normalized:
            return

        command = normalized.split(maxsplit=1)[0].lower()
        if command == "/trial":
            self._handle_trial_command(token, chat_id, sender_id)
            return
        if not command.startswith("/start"):
            return

        parts = normalized.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            self._send_message(token, chat_id, "Use the Telegram connect button from TrackNode dashboard.")
            return

        payload = parts[1].strip()
        logger.info(
            "Telegram /start payload received chat_id=%s sender_id=%s payload=%r",
            chat_id,
            sender_id,
            payload,
        )

        client = resolve_secure_start_payload(payload)
        if client is None:
            self._send_message(token, chat_id, "Перейдите в панель управления")
            return

        previous_chat_id = client.telegram_chat_id
        client.telegram_chat_id = str(chat_id)
        client.send_to_telegram = True
        client.save(update_fields=["telegram_chat_id", "send_to_telegram"])

        if sender_id is not None:
            self._upsert_telegram_link(sender_id=sender_id, chat_id=chat_id, client=client)
        logger.info(
            "telegram binding success client_id=%s old_chat_id=%s new_chat_id=%s",
            client.id,
            previous_chat_id,
            client.telegram_chat_id,
        )
        self._send_message(token, chat_id, "Telegram подключен к вашему аккаунту TrackNode.")

    def _handle_trial_command(self, token: str, chat_id: int, sender_id: int | None) -> None:
        subscription = None

        if sender_id is not None:
            link = TelegramLink.objects.filter(telegram_user_id=sender_id).select_related("client").first()
            if link is not None:
                subscription = Subscription.objects.filter(client=link.client).first()

        if subscription is None:
            client = Client.objects.filter(telegram_chat_id=str(chat_id), is_active=True).first()
            if client is not None:
                subscription = Subscription.objects.filter(client=client).first()

        if subscription is None:
            self._send_message(token, chat_id, "Trial was not found. Connect Telegram from TrackNode dashboard.")
            return

        if subscription.status == Subscription.Status.ACTIVE and subscription.paid_until and subscription.paid_until <= timezone.now():
            subscription.status = Subscription.Status.EXPIRED
            subscription.save(update_fields=["status", "updated_at"])

        if not subscription.is_trial or subscription.status != Subscription.Status.ACTIVE:
            self._send_message(token, chat_id, "Trial is not active.")
            return

        paid_until_text = timezone.localtime(subscription.paid_until).strftime("%d.%m.%Y %H:%M") if subscription.paid_until else "-"
        self._send_message(token, chat_id, f"Trial access is active until: {paid_until_text}")

    def _resolve_callback_context(self, callback_query: dict) -> tuple[str | None, int | None, int | None]:
        data = callback_query.get("data") or ""
        sender = callback_query.get("from") if isinstance(callback_query.get("from"), dict) else {}
        sender_id = sender.get("id")
        message = callback_query.get("message") if isinstance(callback_query.get("message"), dict) else {}
        chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
        chat_id = chat.get("id")
        return data, sender_id, chat_id

    def _handle_disable_auto_renew_callback(self, token: str, sender_id: int, chat_id: int, data: str) -> None:
        subscription_id_raw = data.split("disable_auto_renew_", 1)[1].strip()
        if not subscription_id_raw.isdigit():
            self._send_message(token, chat_id, "Invalid auto-renew arguments.")
            return

        link = TelegramLink.objects.filter(telegram_user_id=sender_id).select_related("client").first()
        if link is None:
            self._send_message(token, chat_id, "Telegram link is not configured.")
            return

        subscription = Subscription.objects.filter(id=int(subscription_id_raw), client_id=link.client_id).first()
        if subscription is None:
            self._send_message(token, chat_id, "Subscription not found.")
            return

        if not subscription.auto_renew:
            self._send_message(token, chat_id, "Auto-renew is already disabled.")
            return

        subscription.auto_renew = False
        subscription.save(update_fields=["auto_renew", "updated_at"])
        self._send_message(token, chat_id, "Auto-renew disabled.")

    def _handle_callback(self, token: str, callback_query: dict) -> None:
        callback_id = callback_query.get("id")
        if callback_id:
            self._answer_callback(token, callback_id)

        data, sender_id, chat_id = self._resolve_callback_context(callback_query)
        if not data or sender_id is None or chat_id is None:
            return

        if data.startswith("disable_auto_renew_"):
            self._handle_disable_auto_renew_callback(token, sender_id, chat_id, data)
            return

    def handle(self, *args, **options):
        mode = "webhook" if bool(getattr(settings, "TELEGRAM_USE_WEBHOOK", False)) else "polling"
        logger.info("Telegram runtime mode=%s pid=%s", mode, os.getpid())
        if mode == "webhook":
            logger.info("Telegram polling disabled because TELEGRAM_USE_WEBHOOK=true. pid=%s", os.getpid())
            return

        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN is empty. Polling cannot start.")
            return

        timeout_seconds = int(getattr(settings, "TELEGRAM_POLLING_TIMEOUT", 30))
        sleep_seconds = float(getattr(settings, "TELEGRAM_POLLING_RETRY_DELAY", 2))
        get_updates_endpoint = f"https://api.telegram.org/bot{token}/getUpdates"
        delete_webhook_endpoint = f"https://api.telegram.org/bot{token}/deleteWebhook"
        lock_key = str(getattr(settings, "TELEGRAM_POLLING_LOCK_KEY", "telegram:polling:lock"))
        lock_ttl = int(getattr(settings, "TELEGRAM_POLLING_LOCK_TTL", 120))
        lock_value = f"{os.getpid()}:{uuid.uuid4().hex}"
        file_lock_fd = self._acquire_file_lock()
        if file_lock_fd is None:
            logger.error("Telegram polling duplicate start prevented by file lock. pid=%s", os.getpid())
            return

        if not cache.add(lock_key, lock_value, timeout=lock_ttl):
            current_holder = cache.get(lock_key)
            logger.error(
                "Telegram polling redis lock is already held. lock_key=%s holder=%s current_pid=%s",
                lock_key,
                current_holder,
                os.getpid(),
            )
            self._release_file_lock(file_lock_fd)
            return
        logger.info("Telegram polling redis lock acquired. lock_key=%s ttl=%s pid=%s", lock_key, lock_ttl, os.getpid())

        try:
            try:
                response = requests.post(delete_webhook_endpoint, json={"drop_pending_updates": True}, timeout=15)
                response.raise_for_status()
                logger.info("Telegram deleteWebhook executed with drop_pending_updates=True. pid=%s", os.getpid())
            except requests.RequestException:
                logger.exception("Failed to disable Telegram webhook before polling start. pid=%s", os.getpid())
                return

            webhook_info = self._log_webhook_info(token)
            webhook_url = (webhook_info.get("url") or "").strip() if isinstance(webhook_info, dict) else ""
            if webhook_url:
                logger.error(
                    "Telegram webhook remains enabled after deleteWebhook. polling aborted to avoid 409. webhook_url=%r pid=%s",
                    webhook_url,
                    os.getpid(),
                )
                return
            logger.info("Telegram webhook is disabled. Polling can start. pid=%s", os.getpid())

            offset = options.get("offset")
            if offset is None:
                latest = TelegramUpdateLog.objects.order_by("-update_id").values_list("update_id", flat=True).first()
                if latest is not None:
                    offset = latest + 1

            logger.info(
                "Telegram polling started. timeout=%s retry=%s offset=%s pid=%s",
                timeout_seconds,
                sleep_seconds,
                offset,
                os.getpid(),
            )

            while True:
                if not cache.touch(lock_key, lock_ttl):
                    current_holder = cache.get(lock_key)
                    if current_holder != lock_value:
                        logger.error(
                            "Telegram polling redis lock lost. Stopping polling loop. lock_key=%s holder=%s pid=%s",
                            lock_key,
                            current_holder,
                            os.getpid(),
                        )
                        return
                    cache.set(lock_key, lock_value, timeout=lock_ttl)

                params = {
                    "timeout": timeout_seconds,
                    "allowed_updates": ["message", "edited_message", "channel_post", "edited_channel_post", "callback_query"],
                }
                if offset is not None:
                    params["offset"] = offset

                try:
                    response = requests.get(get_updates_endpoint, params=params, timeout=timeout_seconds + 10)
                    response.raise_for_status()
                    payload = response.json()
                    if not payload.get("ok"):
                        logger.warning("Telegram API non-ok payload: %s", payload)
                        time.sleep(sleep_seconds)
                        continue

                    updates = payload.get("result", [])
                    if updates:
                        logger.info("Received updates count=%s", len(updates))

                    for update in updates:
                        update_id = update.get("update_id")
                        try:
                            message = extract_message(update)
                            chat = message.get("chat", {}) if isinstance(message, dict) else {}
                            sender = message.get("from", {}) if isinstance(message, dict) else {}
                            text = message.get("text") if isinstance(message, dict) else None
                            if not text and isinstance(message, dict):
                                text = message.get("caption")

                            callback_query = update.get("callback_query") if isinstance(update.get("callback_query"), dict) else {}
                            callback_data = callback_query.get("data") if callback_query else None

                            logger.info(
                                "Incoming update update_id=%s chat_id=%s from_id=%s username=%s text=%r callback=%r payload=%s",
                                update_id,
                                chat.get("id"),
                                sender.get("id"),
                                sender.get("username"),
                                text,
                                callback_data,
                                json.dumps(update, ensure_ascii=False),
                            )

                            if update_id is None:
                                logger.warning("Update without update_id skipped. payload=%s", update)
                                continue

                            _, created = save_telegram_update(update)
                            if not created:
                                logger.info("Duplicate update ignored update_id=%s", update_id)

                            chat_id = chat.get("id")
                            sender_id = sender.get("id")
                            self._handle_start_command(token, text, chat_id, sender_id)
                            if callback_query:
                                self._handle_callback(token, callback_query)
                        except Exception:
                            logger.exception("Failed to process update_id=%s", update_id)
                        finally:
                            if update_id is not None:
                                offset = update_id + 1
                except requests.HTTPError as exc:
                    status_code = exc.response.status_code if exc.response is not None else None
                    if status_code == 409:
                        logger.error(
                            "Telegram polling conflict (409) at getUpdates. Another getUpdates consumer is active or webhook conflicts. pid=%s",
                            os.getpid(),
                        )
                    else:
                        logger.exception("Telegram polling HTTP error status=%s", status_code)
                    time.sleep(sleep_seconds)
                except requests.RequestException:
                    logger.exception("Telegram polling request error.")
                    time.sleep(sleep_seconds)
                except Exception:
                    logger.exception("Unexpected polling loop error.")
                    time.sleep(sleep_seconds)
        finally:
            if cache.get(lock_key) == lock_value:
                cache.delete(lock_key)
                logger.info("Telegram polling redis lock released. lock_key=%s pid=%s", lock_key, os.getpid())
            self._release_file_lock(file_lock_fd)
