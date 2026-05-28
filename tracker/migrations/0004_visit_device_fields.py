from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tracker", "0003_rename_tracker_vis_site_id_visitor_idx_tracker_vis_site_id_bce6b5_idx"),
    ]

    operations = [
        migrations.RenameField(
            model_name="visit",
            old_name="ip",
            new_name="ip_address",
        ),
        migrations.AddField(
            model_name="visit",
            name="browser",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="visit",
            name="browser_family",
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="visit",
            name="device_type",
            field=models.CharField(blank=True, db_index=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="visit",
            name="is_ios_browser",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="visit",
            name="os",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="visit",
            name="user_agent",
            field=models.TextField(blank=True, null=True),
        ),
    ]
