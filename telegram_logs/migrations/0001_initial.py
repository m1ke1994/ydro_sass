# Generated manually for telegram update logs.
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TelegramUpdateLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("update_id", models.BigIntegerField(db_index=True)),
                ("message_id", models.BigIntegerField(blank=True, db_index=True, null=True)),
                ("chat_id", models.BigIntegerField(blank=True, db_index=True, null=True)),
                ("chat_type", models.CharField(blank=True, max_length=32, null=True)),
                ("chat_title", models.CharField(blank=True, max_length=255, null=True)),
                ("user_id", models.BigIntegerField(blank=True, db_index=True, null=True)),
                ("username", models.CharField(blank=True, max_length=255, null=True)),
                ("first_name", models.CharField(blank=True, max_length=255, null=True)),
                ("last_name", models.CharField(blank=True, max_length=255, null=True)),
                ("text", models.TextField(blank=True, null=True)),
                ("command", models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "ordering": ("-created_at",),
                "verbose_name": "Telegram update log",
                "verbose_name_plural": "Telegram update logs",
            },
        ),
    ]
