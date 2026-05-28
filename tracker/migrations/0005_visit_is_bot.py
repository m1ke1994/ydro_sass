from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0004_visit_device_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="visit",
            name="is_bot",
            field=models.BooleanField(default=False),
        ),
    ]
