from django.db import models

from clients.models import Client


class Lead(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_PROGRESS = "in_progress", "В работе"
        CLOSED = "closed", "Закрыта"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="leads", verbose_name="Клиент")
    name = models.CharField(max_length=255, blank=True, default="", verbose_name="Имя")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    message = models.TextField(blank=True, null=True, verbose_name="Сообщение")
    source_url = models.URLField(max_length=1000, blank=True, null=True, verbose_name="URL страницы")
    utm_source = models.CharField(max_length=255, blank=True, null=True, verbose_name="UTM Source")
    utm_medium = models.CharField(max_length=255, blank=True, null=True, verbose_name="UTM Medium")
    utm_campaign = models.CharField(max_length=255, blank=True, null=True, verbose_name="UTM Campaign")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        indexes = [
            models.Index(fields=["client", "status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.name or 'Без имени'} ({self.phone or 'без телефона'})"
