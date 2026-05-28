from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0007_set_monthly_plan_price_to_one_ruble"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="admin_override",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="status",
            field=models.CharField(
                choices=[("active", "active"), ("expired", "expired"), ("canceled", "canceled")],
                db_index=True,
                default="expired",
                max_length=16,
            ),
        ),
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
            name="telegramlink",
            options={
                "ordering": ("-updated_at",),
                "verbose_name": "Связь с Telegram",
                "verbose_name_plural": "Связи с Telegram",
            },
        ),
    ]
