# Generated manually for localization metadata.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0002_localization"),
        ("leads", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="lead",
            options={"ordering": ("-created_at",), "verbose_name": "Заявка", "verbose_name_plural": "Заявки"},
        ),
        migrations.AlterField(
            model_name="lead",
            name="client",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="leads",
                to="clients.client",
                verbose_name="Клиент",
            ),
        ),
        migrations.AlterField(
            model_name="lead",
            name="name",
            field=models.CharField(max_length=255, verbose_name="Имя"),
        ),
        migrations.AlterField(
            model_name="lead",
            name="phone",
            field=models.CharField(max_length=50, verbose_name="Телефон"),
        ),
        migrations.AlterField(
            model_name="lead",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name="Email"),
        ),
        migrations.AlterField(
            model_name="lead",
            name="message",
            field=models.TextField(blank=True, null=True, verbose_name="Сообщение"),
        ),
        migrations.AlterField(
            model_name="lead",
            name="source_url",
            field=models.URLField(blank=True, max_length=1000, null=True, verbose_name="URL страницы"),
        ),
        migrations.AlterField(
            model_name="lead",
            name="utm_source",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="UTM Source"),
        ),
        migrations.AlterField(
            model_name="lead",
            name="utm_medium",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="UTM Medium"),
        ),
        migrations.AlterField(
            model_name="lead",
            name="utm_campaign",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="UTM Campaign"),
        ),
        migrations.AlterField(
            model_name="lead",
            name="status",
            field=models.CharField(
                choices=[("new", "Новая"), ("in_progress", "В работе"), ("closed", "Закрыта")],
                default="new",
                max_length=20,
                verbose_name="Статус",
            ),
        ),
        migrations.AlterField(
            model_name="lead",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Дата создания"),
        ),
    ]

