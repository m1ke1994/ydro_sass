from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0005_alter_client_options_alter_client_api_key_and_more"),
        ("subscriptions", "0002_seed_default_plans"),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("telegram_user_id", models.BigIntegerField(db_index=True, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="telegram_links",
                        to="clients.client",
                    ),
                ),
            ],
            options={
                "ordering": ("-updated_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="telegramlink",
            constraint=models.UniqueConstraint(fields=("client",), name="unique_telegram_link_per_client"),
        ),
    ]

