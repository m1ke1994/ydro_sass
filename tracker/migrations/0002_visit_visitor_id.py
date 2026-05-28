from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="visit",
            name="visitor_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64),
        ),
        migrations.AddIndex(
            model_name="visit",
            index=models.Index(fields=["site", "visitor_id", "started_at"], name="tracker_vis_site_id_visitor_idx"),
        ),
    ]
