from copy import deepcopy

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
import secrets

from .presets import (
    ABOUT_SCHEMA,
    CONTACTS_SCHEMA,
    HERO_DEFAULT_SETTINGS,
    HERO_SCHEMA,
    REVIEWS_DEFAULT_SETTINGS,
    REVIEWS_SCHEMA,
    SERVICES_DEFAULT_SETTINGS,
    SERVICES_SCHEMA,
)

SUPPORTED_FIELD_TYPES = {
    "text",
    "textarea",
    "image",
    "video",
    "media",
    "number",
    "boolean",
    "select",
    "repeater",
}


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)

AUTO_SCHEMA_BY_SECTION_TYPE = {
    "hero": HERO_SCHEMA,
    "about": ABOUT_SCHEMA,
    "services": SERVICES_SCHEMA,
    "meditations": SERVICES_SCHEMA,
    "reviews": REVIEWS_SCHEMA,
    "contacts": CONTACTS_SCHEMA,
}

AUTO_COMPONENT_KEY_BY_SECTION_TYPE = {
    "hero": "hero-centered",
    "about": "about-simple",
    "services": "services-grid",
    "meditations": "services-grid",
    "reviews": "reviews-slider",
    "gallery": "gallery-grid",
    "contacts": "contacts-simple",
    "prices": "prices-grid",
    "footer": "footer-simple",
}

AUTO_SETTINGS_BY_SECTION_TYPE = {
    "hero": HERO_DEFAULT_SETTINGS,
    "services": SERVICES_DEFAULT_SETTINGS,
    "meditations": SERVICES_DEFAULT_SETTINGS,
    "reviews": REVIEWS_DEFAULT_SETTINGS,
}


def _schema_error(message):
    raise ValidationError({"schema": message})


def _content_error(message):
    raise ValidationError({"content": message})


def _settings_error(message):
    raise ValidationError({"settings": message})


def _get_schema_fields(schema):
    if not isinstance(schema, dict):
        return []
    fields = schema.get("fields", [])
    return fields if isinstance(fields, list) else []


def _validate_fields_schema(fields, path):
    if not isinstance(fields, list):
        _schema_error(f"{path}: expected a list of fields.")

    seen_keys = set()
    for index, field in enumerate(fields):
        field_path = f"{path}[{index}]"

        if not isinstance(field, dict):
            _schema_error(f"{field_path}: field must be an object.")

        key = field.get("key")
        if not isinstance(key, str) or not key.strip():
            _schema_error(f"{field_path}: key is required and must be a string.")
        key = key.strip()

        if key in seen_keys:
            _schema_error(f"{field_path}: duplicate key '{key}'.")
        seen_keys.add(key)

        field_type = field.get("type")
        if not isinstance(field_type, str) or not field_type.strip():
            _schema_error(f"{field_path}: type is required and must be a string.")
        field_type = field_type.strip()

        if field_type not in SUPPORTED_FIELD_TYPES:
            _schema_error(f"{field_path}: unsupported type '{field_type}'.")

        required = field.get("required")
        if required is not None and not isinstance(required, bool):
            _schema_error(f"{field_path}: required must be a boolean.")

        for string_field in ("label", "placeholder", "help_text"):
            value = field.get(string_field)
            if value is not None and not isinstance(value, str):
                _schema_error(f"{field_path}: {string_field} must be a string.")

        if field_type == "select":
            options = field.get("options")
            if options is not None and not isinstance(options, list):
                _schema_error(f"{field_path}: options must be a list.")

        if field_type == "repeater":
            nested_fields = field.get("fields")
            if not isinstance(nested_fields, list):
                _schema_error(f"{field_path}: repeater must contain fields list.")
            _validate_fields_schema(nested_fields, f"{field_path}.fields")


def _validate_schema(schema):
    if not isinstance(schema, dict):
        _schema_error("schema must be a JSON object.")
    _validate_fields_schema(_get_schema_fields(schema), "fields")


def _default_value_for_field(field):
    if "default" in field:
        return deepcopy(field.get("default"))

    field_type = field.get("type")
    if field_type == "number":
        return 0
    if field_type == "boolean":
        return False
    if field_type == "repeater":
        return []
    return ""


def _build_defaults_from_fields(fields):
    defaults = {}
    for field in fields:
        key = field.get("key")
        if not key:
            continue
        defaults[key] = _default_value_for_field(field)
    return defaults


def _validate_value_by_type(value, field_schema, path):
    if value is None:
        return

    field_type = field_schema.get("type")
    if field_type in {"text", "textarea", "image", "video", "media", "select"}:
        if not isinstance(value, str):
            _content_error(f"{path}: expected a string.")
        return

    if field_type == "boolean":
        if not isinstance(value, bool):
            _content_error(f"{path}: expected a boolean.")
        return

    if field_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _content_error(f"{path}: expected a number.")
        return

    if field_type == "repeater":
        if not isinstance(value, list):
            _content_error(f"{path}: expected a list for repeater.")

        nested_fields = field_schema.get("fields", [])
        nested_map = {field.get("key"): field for field in nested_fields if isinstance(field, dict)}

        for row_index, row in enumerate(value):
            row_path = f"{path}[{row_index}]"
            if not isinstance(row, dict):
                _content_error(f"{row_path}: repeater row must be an object.")

            unknown_keys = set(row.keys()) - set(nested_map.keys())
            if unknown_keys:
                key_list = ", ".join(sorted(unknown_keys))
                _content_error(f"{row_path}: unknown keys: {key_list}.")

            for nested_key, nested_value in row.items():
                nested_schema = nested_map[nested_key]
                _validate_value_by_type(
                    value=nested_value,
                    field_schema=nested_schema,
                    path=f"{row_path}.{nested_key}",
                )


def _validate_content(content, schema):
    if not isinstance(content, dict):
        _content_error("content must be a JSON object.")

    fields = _get_schema_fields(schema)
    fields_map = {field.get("key"): field for field in fields if isinstance(field, dict)}

    unknown_keys = set(content.keys()) - set(fields_map.keys())
    if unknown_keys:
        key_list = ", ".join(sorted(unknown_keys))
        _content_error(f"unknown keys not present in schema: {key_list}.")

    for key, value in content.items():
        _validate_value_by_type(value=value, field_schema=fields_map[key], path=f"content.{key}")


def _validate_settings(settings):
    if not isinstance(settings, dict):
        _settings_error("settings must be a JSON object.")


class Site(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название сайта")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="Slug сайта")
    domain = models.CharField(max_length=255, blank=True, verbose_name="Домен")
    api_key = models.CharField(
        max_length=128,
        unique=True,
        editable=False,
        default=generate_api_key,
        verbose_name="Ключ аналитики",
    )
    telegram_chat_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="ID чата Telegram",
    )
    send_to_telegram = models.BooleanField(
        default=False,
        verbose_name="Отправлять заявки в Telegram",
    )
    telegram_connected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Telegram подключен",
    )
    seo = models.JSONField(default=dict, blank=True, verbose_name="SEO-настройки")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sites",
        verbose_name="Владелец",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Сайт"
        verbose_name_plural = "Сайты"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = generate_api_key()
        super().save(*args, **kwargs)


class SectionSchema(models.Model):
    section_key = models.SlugField(max_length=100, unique=True, verbose_name="Section key")
    title = models.CharField(max_length=255, verbose_name="Schema title")
    schema = models.JSONField(default=dict, blank=True, verbose_name="Schema")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Section schema"
        verbose_name_plural = "Section schemas"
        ordering = ["section_key"]

    def clean(self):
        SiteSection.validate_schema(self.schema)

    def save(self, *args, **kwargs):
        if not self.section_key and self.title:
            self.section_key = slugify(self.title)
        SiteSection.validate_schema(self.schema)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.section_key} ({self.title})"


class SiteSection(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="Site",
    )
    title = models.CharField(max_length=255, verbose_name="Section title")
    key = models.SlugField(max_length=100, verbose_name="Section key")
    section_type = models.CharField(max_length=100, blank=True, default="", verbose_name="Section type")
    order = models.PositiveIntegerField(default=0, verbose_name="Sort order")
    is_active = models.BooleanField(default=True, verbose_name="Is active")
    schema = models.JSONField(default=dict, blank=True, verbose_name="Field schema")
    content = models.JSONField(default=dict, blank=True, verbose_name="Content")
    component_key = models.CharField(max_length=100, blank=True, verbose_name="Component key")
    settings = models.JSONField(default=dict, blank=True, verbose_name="Section settings")
    seo = models.JSONField(default=dict, blank=True, verbose_name="SEO settings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site section"
        verbose_name_plural = "Site sections"
        ordering = ["site", "order", "title"]
        constraints = [
            models.UniqueConstraint(fields=("site", "key"), name="unique_site_section_key"),
        ]

    @property
    def slug(self):
        return self.key

    @slug.setter
    def slug(self, value):
        self.key = value

    @property
    def name(self):
        return self.title

    @name.setter
    def name(self, value):
        self.title = value

    def _section_identity(self):
        return self.section_type or self.key

    def _apply_schema_preset_if_needed(self):
        if self.schema:
            return
        schema_template = AUTO_SCHEMA_BY_SECTION_TYPE.get(self._section_identity())
        if schema_template:
            self.schema = deepcopy(schema_template)

    def _apply_component_key_if_needed(self):
        if self.component_key:
            return
        self.component_key = AUTO_COMPONENT_KEY_BY_SECTION_TYPE.get(self._section_identity(), "")

    def _apply_settings_preset_if_needed(self):
        if self.settings:
            return
        settings_template = AUTO_SETTINGS_BY_SECTION_TYPE.get(self._section_identity())
        if settings_template:
            self.settings = deepcopy(settings_template)

    @staticmethod
    def validate_schema(schema):
        _validate_schema(schema)

    @staticmethod
    def validate_content(content, schema):
        _validate_content(content=content, schema=schema)

    @staticmethod
    def validate_settings(settings):
        _validate_settings(settings=settings)

    def get_schema_fields(self):
        return _get_schema_fields(self.schema)

    def get_default_content(self):
        return _build_defaults_from_fields(self.get_schema_fields())

    def get_default_settings(self):
        return deepcopy(AUTO_SETTINGS_BY_SECTION_TYPE.get(self._section_identity(), {}))

    def clean(self):
        effective_schema = self.schema or AUTO_SCHEMA_BY_SECTION_TYPE.get(self._section_identity(), {"fields": []})
        effective_settings = self.settings or AUTO_SETTINGS_BY_SECTION_TYPE.get(self._section_identity(), {})
        self.validate_schema(effective_schema)
        self.validate_settings(effective_settings)
        if self.content:
            self.validate_content(content=self.content, schema=effective_schema)

    def save(self, *args, **kwargs):
        if self.key:
            self.key = slugify(self.key)

        if not self.section_type:
            self.section_type = self.key

        self._apply_schema_preset_if_needed()
        self._apply_component_key_if_needed()
        self._apply_settings_preset_if_needed()

        self.validate_schema(self.schema)
        self.validate_settings(self.settings)

        if not self.content:
            self.content = self.get_default_content()

        self.validate_content(content=self.content, schema=self.schema)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.site.name} - {self.title}"


class SiteLead(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_PROGRESS = "in_progress", "В работе"
        DONE = "done", "Завершена"
        ARCHIVED = "archived", "Архив"

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="leads",
        verbose_name="Сайт",
    )
    section_key = models.CharField(max_length=100, blank=True, verbose_name="Ключ секции")
    form_name = models.CharField(max_length=255, blank=True, verbose_name="Название формы")
    name = models.CharField(max_length=255, verbose_name="Имя")
    phone = models.CharField(max_length=100, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    message = models.TextField(blank=True, verbose_name="Сообщение")
    service_type = models.CharField(max_length=100, blank=True, verbose_name="Тип услуги")
    service_title = models.CharField(max_length=255, blank=True, verbose_name="Название услуги")
    source_url = models.URLField(blank=True, verbose_name="Источник (URL)")
    user_agent = models.TextField(blank=True, verbose_name="User-Agent")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP-адрес")
    payload = models.JSONField(default=dict, blank=True, verbose_name="Дополнительные данные")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["site", "status", "created_at"]),
            models.Index(fields=["service_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.site.slug}"
