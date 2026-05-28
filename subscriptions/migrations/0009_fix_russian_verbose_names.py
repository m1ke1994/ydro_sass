from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0008_subscription_admin_override_and_status_canceled"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="subscription",
            options={
                "ordering": ("-updated_at",),
                "verbose_name": "Подписка",
                "verbose_name_plural": "Подписки",
            },
        ),
        migrations.AlterModelOptions(
            name="subscriptionpayment",
            options={
                "ordering": ("-created_at",),
                "verbose_name": "Платёж подписки",
                "verbose_name_plural": "Платежи подписки",
            },
        ),
        migrations.AlterModelOptions(
            name="subscriptionplan",
            options={
                "ordering": ("price",),
                "verbose_name": "Тариф",
                "verbose_name_plural": "Тарифы",
            },
        ),
        migrations.AlterModelOptions(
            name="subscriptionsettings",
            options={
                "verbose_name": "Настройки подписки",
                "verbose_name_plural": "Настройки подписки",
            },
        ),
        migrations.AlterModelOptions(
            name="telegramlink",
            options={
                "ordering": ("-updated_at",),
                "verbose_name": "Связь с Telegram",
                "verbose_name_plural": "Связи с Telegram",
            },
        ),
        migrations.AlterField(
            model_name="subscriptionsettings",
            name="demo_days",
            field=models.PositiveIntegerField(default=3, verbose_name="Длительность демо (дней)"),
        ),
        migrations.AlterField(
            model_name="subscriptionsettings",
            name="demo_enabled",
            field=models.BooleanField(default=True, verbose_name="Демо-доступ включен"),
        ),
    ]
