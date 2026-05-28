# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo_audit", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteseoaudit",
            name="celery_task_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="siteseoaudit",
            name="is_cancelled",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="siteseoaudit",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "pending"),
                    ("running", "running"),
                    ("done", "done"),
                    ("error", "error"),
                    ("stopped", "stopped"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
    ]
