from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0004_subscriptionpayment_auto_renew_and_telegram_chat"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="is_trial",
            field=models.BooleanField(default=False),
        ),
    ]
