from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="reportsettings",
            name="send_email",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="reportsettings",
            name="email_to",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name="reportsettings",
            name="send_telegram",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="reportsettings",
            name="telegram_chat_id",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="reportsettings",
            name="telegram_username",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="reportsettings",
            name="telegram_is_connected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="reportlog",
            name="delivery_channels",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.CreateModel(
            name="TelegramLinkToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=16, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("is_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "client",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="telegram_link_tokens", to="clients.client"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="telegram_link_tokens", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "indexes": [
                    models.Index(fields=["code", "expires_at"], name="reports_tel_code_2e56d0_idx"),
                    models.Index(fields=["client", "created_at"], name="reports_tel_client_c4d19a_idx"),
                ],
            },
        ),
    ]
