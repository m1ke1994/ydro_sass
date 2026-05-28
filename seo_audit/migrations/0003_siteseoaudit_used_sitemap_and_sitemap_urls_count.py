# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seo_audit", "0002_siteseoaudit_cancel_fields_and_stopped_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteseoaudit",
            name="used_sitemap",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="siteseoaudit",
            name="sitemap_urls_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
