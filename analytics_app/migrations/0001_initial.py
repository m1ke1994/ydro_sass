# Generated manually for initial schema.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event_type",
                    models.CharField(
                        choices=[("visit", "Visit"), ("click", "Click"), ("form_submit", "Form Submit")],
                        max_length=20,
                    ),
                ),
                ("element_id", models.CharField(blank=True, max_length=255, null=True)),
                ("page_url", models.URLField(max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="clients.client",
                    ),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(
                fields=["client", "event_type", "created_at"], name="analytics_a_client__fe5f61_idx"
            ),
        ),
    ]

