# Generated manually for localization metadata.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="client",
            options={"ordering": ("-created_at",), "verbose_name": "Клиент", "verbose_name_plural": "Клиенты"},
        ),
        migrations.AlterField(
            model_name="client",
            name="owner",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="client",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Владелец",
            ),
        ),
        migrations.AlterField(
            model_name="client",
            name="name",
            field=models.CharField(max_length=255, verbose_name="Название клиента"),
        ),
        migrations.AlterField(
            model_name="client",
            name="api_key",
            field=models.CharField(
                db_index=True,
                editable=False,
                max_length=128,
                unique=True,
                verbose_name="API-ключ",
            ),
        ),
        migrations.AlterField(
            model_name="client",
            name="telegram_chat_id",
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name="Telegram chat ID"),
        ),
        migrations.AlterField(
            model_name="client",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Активен"),
        ),
        migrations.AlterField(
            model_name="client",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Дата создания"),
        ),
    ]

