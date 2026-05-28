from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics_app", "0007_alter_clickevent_options_alter_event_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="duration_seconds",
            field=models.PositiveIntegerField(default=0, verbose_name="Duration (sec)"),
        ),
        migrations.AlterField(
            model_name="event",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("visit", "Visit"),
                    ("click", "Click"),
                    ("form_submit", "Form submit"),
                    ("time_on_page", "Time on page"),
                ],
                max_length=20,
                verbose_name="Event type",
            ),
        ),
    ]
