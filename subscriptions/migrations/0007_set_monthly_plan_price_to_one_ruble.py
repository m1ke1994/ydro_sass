from decimal import Decimal

from django.db import migrations


def set_monthly_plan_price_to_one_ruble(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    SubscriptionPlan.objects.filter(name="1 месяц").update(price=Decimal("1.00"), currency="RUB")


def rollback_monthly_plan_price(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    SubscriptionPlan.objects.filter(name="1 месяц").update(price=Decimal("1999.00"), currency="RUB")


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0006_subscriptionsettings"),
    ]

    operations = [
        migrations.RunPython(set_monthly_plan_price_to_one_ruble, rollback_monthly_plan_price),
    ]
