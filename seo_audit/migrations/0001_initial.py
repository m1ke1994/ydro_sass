# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0005_alter_client_options_alter_client_api_key_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteSEOAudit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("domain", models.CharField(db_index=True, max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "pending"), ("running", "running"), ("done", "done"), ("error", "error")],
                        db_index=True,
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("seo_score", models.IntegerField(default=0)),
                ("pages_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seo_audits", to="clients.client")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="SEOPage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("url", models.TextField()),
                ("status_code", models.PositiveIntegerField(default=0)),
                ("title", models.CharField(blank=True, default="", max_length=512)),
                ("title_length", models.PositiveIntegerField(default=0)),
                ("description", models.TextField(blank=True, default="")),
                ("description_length", models.PositiveIntegerField(default=0)),
                ("h1", models.TextField(blank=True, default="")),
                ("h1_count", models.PositiveIntegerField(default=0)),
                ("word_count", models.PositiveIntegerField(default=0)),
                ("audit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pages", to="seo_audit.siteseoaudit")),
            ],
            options={"ordering": ("url", "id")},
        ),
        migrations.CreateModel(
            name="SEOIssue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "issue_type",
                    models.CharField(
                        choices=[
                            ("missing_title", "missing_title"),
                            ("bad_title_length", "bad_title_length"),
                            ("missing_description", "missing_description"),
                            ("duplicate_title", "duplicate_title"),
                            ("missing_h1", "missing_h1"),
                            ("multiple_h1", "multiple_h1"),
                            ("bad_status", "bad_status"),
                        ],
                        max_length=64,
                    ),
                ),
                ("severity", models.CharField(choices=[("low", "low"), ("medium", "medium"), ("high", "high")], max_length=16)),
                ("recommendation", models.TextField()),
                ("page", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="issues", to="seo_audit.seopage")),
            ],
            options={"ordering": ("page__url", "id")},
        ),
        migrations.AddIndex(
            model_name="seopage",
            index=models.Index(fields=["audit", "url"], name="seo_audit_s_audit_i_4e9b6c_idx"),
        ),
    ]

