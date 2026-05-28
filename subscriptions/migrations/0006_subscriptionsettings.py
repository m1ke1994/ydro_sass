from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0005_subscription_is_trial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubscriptionSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("demo_enabled", models.BooleanField(default=True, verbose_name="Демо-доступ включен")),
                ("demo_days", models.PositiveIntegerField(default=3, verbose_name="Длительность демо (дней)")),
            ],
            options={
                "verbose_name": "Настройки подписки",
                "verbose_name_plural": "Настройки подписки",
            },
        ),
    ]
