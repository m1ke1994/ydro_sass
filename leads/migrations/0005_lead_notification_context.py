from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0004_alter_lead_name_alter_lead_phone"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="notification_context",
            field=models.JSONField(blank=True, default=dict, verbose_name="Telegram notification context"),
        ),
    ]
