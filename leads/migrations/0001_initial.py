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
            name="Lead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("phone", models.CharField(max_length=50)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("message", models.TextField(blank=True, null=True)),
                ("source_url", models.URLField(blank=True, max_length=1000, null=True)),
                ("utm_source", models.CharField(blank=True, max_length=255, null=True)),
                ("utm_medium", models.CharField(blank=True, max_length=255, null=True)),
                ("utm_campaign", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("new", "New"), ("in_progress", "In Progress"), ("closed", "Closed")],
                        default="new",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="leads",
                        to="clients.client",
                    ),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddIndex(
            model_name="lead",
            index=models.Index(fields=["client", "status", "created_at"], name="leads_lead_client__363fe4_idx"),
        ),
    ]

