from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0005_alter_client_options_alter_client_api_key_and_more"),
        ("subscriptions", "0003_telegramlink"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="auto_renew",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="telegramlink",
            name="telegram_chat_id",
            field=models.BigIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.CreateModel(
            name="SubscriptionPayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("yookassa_payment_id", models.CharField(db_index=True, max_length=128, unique=True)),
                ("status", models.CharField(choices=[("pending", "pending"), ("succeeded", "succeeded"), ("canceled", "canceled")], db_index=True, default="pending", max_length=16)),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subscription_payments", to="clients.client")),
                ("plan", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="subscription_payments", to="subscriptions.subscriptionplan")),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
