from django.db import migrations


def seed_default_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")

    # Idempotent seed: create defaults only when plans table is empty.
    if SubscriptionPlan.objects.count() != 0:
        return

    SubscriptionPlan.objects.get_or_create(
        name="1 месяц",
        defaults={
            "duration_days": 30,
            "price": "1999",
            "is_active": True,
        },
    )
    SubscriptionPlan.objects.get_or_create(
        name="3 месяца",
        defaults={
            "duration_days": 90,
            "price": "5499",
            "is_active": True,
        },
    )
    SubscriptionPlan.objects.get_or_create(
        name="6 месяцев",
        defaults={
            "duration_days": 180,
            "price": "9990",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_plans, migrations.RunPython.noop),
    ]

