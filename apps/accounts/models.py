from django.conf import settings
from django.db import models


class ClientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profile",
        verbose_name="Пользователь",
    )
    display_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Отображаемое имя",
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Телефон",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

    def __str__(self):
        if self.display_name:
            return self.display_name
        return self.user.username or self.user.email
