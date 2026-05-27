# Generated manually for media upload refactor.

from django.db import migrations, models
import apps.mediafiles.models


class Migration(migrations.Migration):

    dependencies = [
        ("mediafiles", "0002_mediafile_description_mediafile_mime_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="mediafile",
            name="field_key",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Поле"),
        ),
        migrations.AddField(
            model_name="mediafile",
            name="original_name",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Оригинальное имя"),
        ),
        migrations.AddField(
            model_name="mediafile",
            name="section_key",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Секция"),
        ),
        migrations.AlterField(
            model_name="mediafile",
            name="file",
            field=models.FileField(upload_to=apps.mediafiles.models._build_upload_path, verbose_name="Файл"),
        ),
        migrations.AddConstraint(
            model_name="mediafile",
            constraint=models.UniqueConstraint(
                fields=("site", "section_key", "field_key", "original_name"),
                name="unique_site_section_field_original_media",
            ),
        ),
    ]
