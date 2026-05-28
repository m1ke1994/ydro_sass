from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0004_simplify_reports"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportsettings",
            name="last_manual_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
