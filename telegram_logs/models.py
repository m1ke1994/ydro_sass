from django.db import models


class TelegramUpdateLog(models.Model):
    update_id = models.BigIntegerField(db_index=True, verbose_name="ID обновления")
    message_id = models.BigIntegerField(null=True, blank=True, db_index=True, verbose_name="ID сообщения")

    chat_id = models.BigIntegerField(null=True, blank=True, db_index=True, verbose_name="ID чата")
    chat_type = models.CharField(max_length=32, blank=True, null=True, verbose_name="Тип чата")
    chat_title = models.CharField(max_length=255, blank=True, null=True, verbose_name="Название чата")

    user_id = models.BigIntegerField(null=True, blank=True, db_index=True, verbose_name="ID пользователя")
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name="Username")
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Имя")
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Фамилия")

    text = models.TextField(blank=True, null=True, verbose_name="Текст")
    command = models.CharField(max_length=64, blank=True, null=True, db_index=True, verbose_name="Команда")
    payload = models.JSONField(default=dict, blank=True, verbose_name="Полные данные")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Получено")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Лог Telegram"
        verbose_name_plural = "Логи Telegram"

    def __str__(self) -> str:
        return f"update={self.update_id} chat={self.chat_id} command={self.command or '-'}"
