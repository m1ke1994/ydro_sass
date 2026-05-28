# Generated manually for localization metadata.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0002_localization"),
        ("analytics_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="event",
            options={"ordering": ("-created_at",), "verbose_name": "Событие", "verbose_name_plural": "События"},
        ),
        migrations.AlterField(
            model_name="event",
            name="client",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to="clients.client",
                verbose_name="Клиент",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="event_type",
            field=models.CharField(
                choices=[("visit", "Визит"), ("click", "Клик"), ("form_submit", "Отправка формы")],
                max_length=20,
                verbose_name="Тип события",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="element_id",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="ID элемента"),
        ),
        migrations.AlterField(
            model_name="event",
            name="page_url",
            field=models.URLField(max_length=1000, verbose_name="URL страницы"),
        ),
        migrations.AlterField(
            model_name="event",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Дата создания"),
        ),
    ]

