import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from clients.models import Client
from clients.telegram_binding import build_secure_start_payload, resolve_secure_start_payload
from subscriptions.models import TelegramLink
from telegram_logs.management.commands.run_telegram_polling import Command


class TelegramBindingTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="bind-owner@example.com",
            email="bind-owner@example.com",
            password="test-test-123",
        )
        self.client_obj = Client.objects.create(owner=self.user, name="Bind Client", is_active=True)

    def test_build_and_resolve_secure_payload(self):
        payload = build_secure_start_payload(self.client_obj)
        resolved = resolve_secure_start_payload(payload)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.id, self.client_obj.id)

    def test_resolve_secure_payload_rejects_tampered_signature(self):
        payload = build_secure_start_payload(self.client_obj)
        tampered = payload[:-1] + ("0" if payload[-1] != "0" else "1")
        self.assertIsNone(resolve_secure_start_payload(tampered))

    @override_settings(TELEGRAM_BIND_TOKEN_MAX_AGE=0)
    def test_resolve_secure_payload_rejects_expired_token(self):
        payload = build_secure_start_payload(self.client_obj)
        self.assertIsNone(resolve_secure_start_payload(payload))

    @patch.object(Command, "_send_message")
    def test_start_command_binds_chat_without_automatic_message(self, mocked_send_message):
        payload = build_secure_start_payload(self.client_obj)
        command = Command()
        command._handle_start_command(
            token="token",
            text=f"/start {payload}",
            chat_id=123456789,
            sender_id=777001,
        )

        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.telegram_chat_id, "123456789")
        self.assertTrue(self.client_obj.send_to_telegram)
        self.assertTrue(
            TelegramLink.objects.filter(
                client=self.client_obj,
                telegram_user_id=777001,
                telegram_chat_id=123456789,
            ).exists()
        )
        mocked_send_message.assert_not_called()

    def test_polling_replaces_stale_lock_from_previous_container_process(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = Path(temp_dir) / "telegram.lock"
            lock_file.write_text("1", encoding="utf-8")
            command = Command()

            with self.settings(TELEGRAM_POLLING_LOCK_FILE=str(lock_file)), patch.object(os, "getpid", return_value=1):
                file_descriptor = command._acquire_file_lock()
                self.assertIsNotNone(file_descriptor)
                command._release_file_lock(file_descriptor)

            self.assertFalse(lock_file.exists())
