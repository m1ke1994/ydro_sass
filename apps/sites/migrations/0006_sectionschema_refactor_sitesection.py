from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0005_sitesection_seo"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectionSchema",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("section_key", models.SlugField(max_length=100, unique=True, verbose_name="Section key")),
                ("title", models.CharField(max_length=255, verbose_name="Schema title")),
                ("schema", models.JSONField(blank=True, default=dict, verbose_name="Schema")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Section schema",
                "verbose_name_plural": "Section schemas",
                "ordering": ["section_key"],
            },
        ),
        migrations.RenameField(
            model_name="sitesection",
            old_name="name",
            new_name="title",
        ),
        migrations.RenameField(
            model_name="sitesection",
            old_name="slug",
            new_name="key",
        ),
        migrations.AlterField(
            model_name="sitesection",
            name="key",
            field=models.SlugField(max_length=100, verbose_name="Section key"),
        ),
        migrations.AlterField(
            model_name="sitesection",
            name="section_type",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Section type"),
        ),
        migrations.AlterModelOptions(
            name="sitesection",
            options={
                "ordering": ["site", "order", "title"],
                "verbose_name": "Site section",
                "verbose_name_plural": "Site sections",
            },
        ),
        migrations.AlterUniqueTogether(
            name="sitesection",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="sitesection",
            constraint=models.UniqueConstraint(fields=("site", "key"), name="unique_site_section_key"),
        ),
    ]
