import secrets

from django.db import migrations, models

import apps.sites.models


def fill_site_api_keys(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    for site in Site.objects.all():
        if site.api_key:
            continue
        token = secrets.token_urlsafe(32)
        while Site.objects.filter(api_key=token).exists():
            token = secrets.token_urlsafe(32)
        site.api_key = token
        site.save(update_fields=["api_key"])


class Migration(migrations.Migration):
    dependencies = [
        ("sites", "0008_sitelead"),
    ]

    operations = [
        migrations.AddField(
            model_name="site",
            name="api_key",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=128,
                null=True,
                verbose_name="API key",
            ),
        ),
        migrations.RunPython(fill_site_api_keys, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="site",
            name="api_key",
            field=models.CharField(
                default=apps.sites.models.generate_api_key,
                editable=False,
                max_length=128,
                unique=True,
                verbose_name="API key",
            ),
        ),
    ]
