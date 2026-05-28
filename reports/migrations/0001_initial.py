from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0005_alter_client_options_alter_client_api_key_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=False)),
                ("daily_time", models.TimeField(default="09:00")),
                ("timezone", models.CharField(default="Europe/Moscow", max_length=64)),
                ("last_sent_at", models.DateTimeField(blank=True, null=True)),
                (
                    "last_status",
                    models.CharField(
                        choices=[("idle", "Idle"), ("success", "Success"), ("error", "Error")],
                        default="idle",
                        max_length=16,
                    ),
                ),
                ("last_error", models.TextField(blank=True, default="")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "client",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="report_settings", to="clients.client"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="report_settings", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ("-updated_at",)},
        ),
        migrations.CreateModel(
            name="ReportLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("period_from", models.DateField()),
                ("period_to", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(choices=[("success", "Success"), ("error", "Error")], max_length=16),
                ),
                (
                    "trigger_type",
                    models.CharField(
                        choices=[("manual", "Manual"), ("scheduled", "Scheduled")],
                        default="manual",
                        max_length=16,
                    ),
                ),
                ("file_path", models.CharField(blank=True, default="", max_length=500)),
                ("error", models.TextField(blank=True, default="")),
                (
                    "client",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="report_logs", to="clients.client"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="report_logs", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "indexes": [
                    models.Index(fields=["client", "created_at"], name="reports_rep_client__9f4e1f_idx"),
                    models.Index(fields=["client", "status", "created_at"], name="reports_rep_client__4a6cab_idx"),
                ],
            },
        ),
    ]
