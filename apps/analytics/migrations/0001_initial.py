from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("sites", "0009_site_api_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="Visit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visitor_id", models.CharField(blank=True, db_index=True, default="", max_length=64, verbose_name="Visitor ID")),
                ("session_id", models.CharField(db_index=True, max_length=64, verbose_name="Session ID")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True, verbose_name="IP")),
                ("user_agent", models.TextField(blank=True, default="", verbose_name="User-Agent")),
                ("referrer", models.TextField(blank=True, default="", verbose_name="Referrer")),
                ("started_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name="Начало визита")),
                ("ended_at", models.DateTimeField(blank=True, null=True, verbose_name="Окончание визита")),
                ("duration", models.PositiveIntegerField(default=0, verbose_name="Длительность (сек)")),
                (
                    "site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="visits",
                        to="sites.site",
                        verbose_name="Сайт",
                    ),
                ),
            ],
            options={
                "verbose_name": "Визит",
                "verbose_name_plural": "Визиты",
                "ordering": ("-started_at",),
            },
        ),
        migrations.CreateModel(
            name="TrackingEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(max_length=64, verbose_name="Тип события")),
                ("payload", models.JSONField(blank=True, default=dict, verbose_name="Payload")),
                ("timestamp", models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name="Время события")),
                (
                    "visit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="analytics.visit",
                        verbose_name="Визит",
                    ),
                ),
            ],
            options={
                "verbose_name": "Событие",
                "verbose_name_plural": "События",
                "ordering": ("-timestamp",),
            },
        ),
        migrations.CreateModel(
            name="PageView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("url", models.TextField(verbose_name="URL")),
                ("pathname", models.CharField(blank=True, db_index=True, default="", max_length=512, verbose_name="Pathname")),
                ("title", models.CharField(blank=True, default="", max_length=512, verbose_name="Заголовок страницы")),
                ("timestamp", models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name="Время просмотра")),
                (
                    "visit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pageviews",
                        to="analytics.visit",
                        verbose_name="Визит",
                    ),
                ),
            ],
            options={
                "verbose_name": "Просмотр страницы",
                "verbose_name_plural": "Просмотры страниц",
                "ordering": ("-timestamp",),
            },
        ),
        migrations.AddIndex(
            model_name="visit",
            index=models.Index(fields=["site", "session_id", "started_at"], name="analytics_v_site_id_0b8cd8_idx"),
        ),
        migrations.AddIndex(
            model_name="visit",
            index=models.Index(fields=["site", "visitor_id", "started_at"], name="analytics_v_site_id_3d6b7d_idx"),
        ),
        migrations.AddIndex(
            model_name="trackingevent",
            index=models.Index(fields=["visit", "type", "timestamp"], name="analytics_t_visit_i_79b319_idx"),
        ),
        migrations.AddIndex(
            model_name="pageview",
            index=models.Index(fields=["visit", "timestamp"], name="analytics_p_visit_i_415ecc_idx"),
        ),
    ]
