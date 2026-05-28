from django.db import models


class TelegramUpdateLog(models.Model):
    update_id = models.BigIntegerField(db_index=True)
    message_id = models.BigIntegerField(null=True, blank=True, db_index=True)

    chat_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    chat_type = models.CharField(max_length=32, blank=True, null=True)
    chat_title = models.CharField(max_length=255, blank=True, null=True)

    user_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)

    text = models.TextField(blank=True, null=True)
    command = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Telegram update log"
        verbose_name_plural = "Telegram update logs"

    def __str__(self) -> str:
        return f"update={self.update_id} chat={self.chat_id} command={self.command or '-'}"
