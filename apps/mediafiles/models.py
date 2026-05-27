import mimetypes
from pathlib import Path
from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.sites.models import Site

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "mp4", "webm"}


def _build_upload_path(instance, filename):
    site_slug = slugify(instance.site.slug if instance.site_id and instance.site else "site")
    section_slug = slugify(instance.section_key or "uploads")

    original_name = Path(filename).name
    suffix = Path(original_name).suffix.lower()
    stem = slugify(Path(original_name).stem) or "file"
    normalized_name = f"{stem}{suffix}"

    return f"sites/{site_slug}/{section_slug}/{normalized_name}"


class MediaFile(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="media_files",
        verbose_name="Сайт",
    )
    section_key = models.CharField(max_length=100, blank=True, default="", verbose_name="Секция")
    field_key = models.CharField(max_length=255, blank=True, default="", verbose_name="Поле")
    original_name = models.CharField(max_length=255, blank=True, default="", verbose_name="Оригинальное имя")
    file = models.FileField(upload_to=_build_upload_path, verbose_name="Файл")
    file_type = models.CharField(max_length=50, blank=True, verbose_name="Тип файла")
    title = models.CharField(max_length=255, blank=True, verbose_name="Название")
    alt = models.CharField(max_length=255, blank=True, verbose_name="Alt-текст")
    description = models.TextField(blank=True, verbose_name="Описание")
    size = models.PositiveIntegerField(default=0, verbose_name="Размер (байт)")
    mime_type = models.CharField(max_length=255, blank=True, verbose_name="MIME-тип")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Медиафайл"
        verbose_name_plural = "Медиафайлы"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=("site", "section_key", "field_key", "original_name"),
                name="unique_site_section_field_original_media",
            )
        ]

    def __str__(self):
        return Path(self.file.name).name if self.file else f"media-{self.pk}"

    def clean(self):
        super().clean()
        if not self.file:
            return

        extension = Path(self.file.name).suffix.lower().lstrip(".")
        if extension not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise ValidationError({"file": f"Недопустимый формат файла. Разрешены: {allowed}."})

    def _detect_metadata(self):
        if not self.file:
            self.size = 0
            self.mime_type = ""
            self.file_type = ""
            return

        self.size = getattr(self.file, "size", 0) or 0

        mime_type, _ = mimetypes.guess_type(self.file.name)
        self.mime_type = mime_type or ""

        if self.mime_type.startswith("image/"):
            self.file_type = "image"
        elif self.mime_type.startswith("video/"):
            self.file_type = "video"
        else:
            extension = Path(self.file.name).suffix.lower().lstrip(".")
            if extension in {"jpg", "jpeg", "png", "webp"}:
                self.file_type = "image"
            elif extension in {"mp4", "webm"}:
                self.file_type = "video"
            else:
                self.file_type = "file"

    def get_absolute_url(self):
        if not self.file:
            return ""

        file_url = self.file.url
        if file_url.startswith(("http://", "https://")):
            return file_url

        base_url = getattr(settings, "SITE_BASE_URL", "http://127.0.0.1:8000")
        return urljoin(f"{base_url.rstrip('/')}/", file_url.lstrip("/"))

    def get_relative_media_path(self):
        if not self.file:
            return ""
        return self.file.url

    def get_filename(self):
        if not self.file:
            return ""
        return Path(self.file.name).name

    def save(self, *args, **kwargs):
        self.clean()
        if self.file and not self.original_name:
            self.original_name = Path(self.file.name).name
        self._detect_metadata()
        super().save(*args, **kwargs)
