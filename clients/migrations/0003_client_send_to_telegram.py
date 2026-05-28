# Generated manually for telegram delivery flag.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0002_localization"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="send_to_telegram",
            field=models.BooleanField(default=False, verbose_name="Отправлять лиды в Telegram"),
        ),
    ]
