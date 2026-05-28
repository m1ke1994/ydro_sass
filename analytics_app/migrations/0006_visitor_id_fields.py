from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics_app", "0005_rename_analytics_a_client__7febe8_idx_analytics_a_client__f7943d_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="visitor_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64, verbose_name="Visitor ID"),
        ),
        migrations.AddField(
            model_name="pageview",
            name="visitor_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64, verbose_name="Visitor ID"),
        ),
        migrations.AddField(
            model_name="clickevent",
            name="visitor_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64, verbose_name="Visitor ID"),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(fields=["client", "visitor_id", "created_at"], name="analytics_a_client__visitor_evt_idx"),
        ),
        migrations.AddIndex(
            model_name="pageview",
            index=models.Index(fields=["client", "visitor_id", "created_at"], name="analytics_a_client__visitor_pv_idx"),
        ),
        migrations.AddIndex(
            model_name="clickevent",
            index=models.Index(fields=["client", "visitor_id", "created_at"], name="analytics_a_client__visitor_clk_idx"),
        ),
    ]
