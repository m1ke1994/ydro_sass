from copy import deepcopy

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

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

SECTION_TYPES = [
    ("hero", "Hero"),
    ("about", "\u041e \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438"),
    ("services", "\u0423\u0441\u043b\u0443\u0433\u0438"),
    ("reviews", "\u041e\u0442\u0437\u044b\u0432\u044b"),
    ("gallery", "\u0413\u0430\u043b\u0435\u0440\u0435\u044f"),
    ("contacts", "\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u044b"),
]

SUPPORTED_FIELD_TYPES = {
    "text",
    "textarea",
    "image",
    "video",
    "number",
    "boolean",
    "select",
    "repeater",
}

AUTO_SCHEMA_BY_SECTION_TYPE = {
    "hero": HERO_SCHEMA,
    "about": ABOUT_SCHEMA,
    "services": SERVICES_SCHEMA,
    "reviews": REVIEWS_SCHEMA,
    "contacts": CONTACTS_SCHEMA,
}

AUTO_COMPONENT_KEY_BY_SECTION_TYPE = {
    "hero": "hero-centered",
    "about": "about-simple",
    "services": "services-grid",
    "reviews": "reviews-slider",
    "gallery": "gallery-grid",
}

AUTO_SETTINGS_BY_SECTION_TYPE = {
    "hero": HERO_DEFAULT_SETTINGS,
    "services": SERVICES_DEFAULT_SETTINGS,
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
        _schema_error(f"{path}: ожидается список полей.")

    seen_keys = set()
    for index, field in enumerate(fields):
        field_path = f"{path}[{index}]"

        if not isinstance(field, dict):
            _schema_error(f"{field_path}: поле должно быть объектом.")

        key = field.get("key")
        if not isinstance(key, str) or not key.strip():
            _schema_error(f"{field_path}: поле key обязательно и должно быть строкой.")
        key = key.strip()

        if key in seen_keys:
            _schema_error(f"{field_path}: key '{key}' дублируется.")
        seen_keys.add(key)

        field_type = field.get("type")
        if not isinstance(field_type, str) or not field_type.strip():
            _schema_error(f"{field_path}: поле type обязательно и должно быть строкой.")
        field_type = field_type.strip()

        if field_type not in SUPPORTED_FIELD_TYPES:
            _schema_error(f"{field_path}: type '{field_type}' не поддерживается.")

        required = field.get("required")
        if required is not None and not isinstance(required, bool):
            _schema_error(f"{field_path}: required должно быть boolean.")

        for string_field in ("label", "placeholder", "help_text"):
            value = field.get(string_field)
            if value is not None and not isinstance(value, str):
                _schema_error(f"{field_path}: {string_field} должно быть строкой.")

        if field_type == "select":
            options = field.get("options")
            if options is not None and not isinstance(options, list):
                _schema_error(f"{field_path}: options должно быть списком.")

        if field_type == "repeater":
            nested_fields = field.get("fields")
            if not isinstance(nested_fields, list):
                _schema_error(f"{field_path}: repeater должен содержать список fields.")
            _validate_fields_schema(nested_fields, f"{field_path}.fields")


def _validate_schema(schema):
    if not isinstance(schema, dict):
        _schema_error("schema должна быть объектом JSON.")
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
    if field_type in {"text", "textarea", "image", "video", "select"}:
        if not isinstance(value, str):
            _content_error(f"{path}: ожидается строка.")
        return

    if field_type == "boolean":
        if not isinstance(value, bool):
            _content_error(f"{path}: ожидается boolean.")
        return

    if field_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _content_error(f"{path}: ожидается number.")
        return

    if field_type == "repeater":
        if not isinstance(value, list):
            _content_error(f"{path}: для repeater ожидается список.")

        nested_fields = field_schema.get("fields", [])
        nested_map = {field.get("key"): field for field in nested_fields if isinstance(field, dict)}

        for row_index, row in enumerate(value):
            row_path = f"{path}[{row_index}]"
            if not isinstance(row, dict):
                _content_error(f"{row_path}: элемент repeater должен быть объектом.")

            unknown_keys = set(row.keys()) - set(nested_map.keys())
            if unknown_keys:
                key_list = ", ".join(sorted(unknown_keys))
                _content_error(f"{row_path}: неизвестные ключи: {key_list}.")

            for nested_key, nested_value in row.items():
                nested_schema = nested_map[nested_key]
                _validate_value_by_type(
                    value=nested_value,
                    field_schema=nested_schema,
                    path=f"{row_path}.{nested_key}",
                )


def _validate_content(content, schema):
    if not isinstance(content, dict):
        _content_error("content должен быть объектом JSON.")

    fields = _get_schema_fields(schema)
    fields_map = {field.get("key"): field for field in fields if isinstance(field, dict)}

    unknown_keys = set(content.keys()) - set(fields_map.keys())
    if unknown_keys:
        key_list = ", ".join(sorted(unknown_keys))
        _content_error(f"Обнаружены ключи, отсутствующие в schema: {key_list}.")

    for key, value in content.items():
        _validate_value_by_type(value=value, field_schema=fields_map[key], path=f"content.{key}")


def _validate_settings(settings):
    if not isinstance(settings, dict):
        _settings_error("settings должен быть JSON-объектом.")


class Site(models.Model):
    name = models.CharField(max_length=255, verbose_name="\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0441\u0430\u0439\u0442\u0430")
    slug = models.SlugField(max_length=255, unique=True, verbose_name="Slug \u0441\u0430\u0439\u0442\u0430")
    domain = models.CharField(max_length=255, blank=True, verbose_name="\u0414\u043e\u043c\u0435\u043d")
    seo = models.JSONField(default=dict, blank=True, verbose_name="SEO настройки")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sites",
        verbose_name="\u0412\u043b\u0430\u0434\u0435\u043b\u0435\u0446",
    )
    is_active = models.BooleanField(default=True, verbose_name="\u0410\u043a\u0442\u0438\u0432\u0435\u043d")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "\u0421\u0430\u0439\u0442"
        verbose_name_plural = "\u0421\u0430\u0439\u0442\u044b"
        ordering = ["name"]

    def __str__(self):
        return self.name


class SiteSection(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="\u0421\u0430\u0439\u0442",
    )
    name = models.CharField(max_length=255, verbose_name="\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0440\u0430\u0437\u0434\u0435\u043b\u0430")
    slug = models.SlugField(max_length=255, verbose_name="Slug \u0440\u0430\u0437\u0434\u0435\u043b\u0430")
    section_type = models.CharField(
        max_length=100,
        choices=SECTION_TYPES,
        verbose_name="\u0422\u0438\u043f \u0441\u0435\u043a\u0446\u0438\u0438",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="\u041f\u043e\u0440\u044f\u0434\u043e\u043a")
    is_active = models.BooleanField(default=True, verbose_name="\u0410\u043a\u0442\u0438\u0432\u043d\u0430")
    schema = models.JSONField(default=dict, blank=True, verbose_name="\u0421\u0445\u0435\u043c\u0430 \u043f\u043e\u043b\u0435\u0439")
    content = models.JSONField(default=dict, blank=True, verbose_name="\u041a\u043e\u043d\u0442\u0435\u043d\u0442")
    component_key = models.CharField(max_length=100, blank=True, verbose_name="\u041a\u043b\u044e\u0447 \u043a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442\u0430")
    settings = models.JSONField(default=dict, blank=True, verbose_name="\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u0441\u0435\u043a\u0446\u0438\u0438")
    seo = models.JSONField(default=dict, blank=True, verbose_name="SEO settings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "\u0420\u0430\u0437\u0434\u0435\u043b \u0441\u0430\u0439\u0442\u0430"
        verbose_name_plural = "\u0420\u0430\u0437\u0434\u0435\u043b\u044b \u0441\u0430\u0439\u0442\u0430"
        ordering = ["site", "order", "name"]
        unique_together = ("site", "slug")

    def _apply_schema_preset_if_needed(self):
        if self.schema:
            return
        schema_template = AUTO_SCHEMA_BY_SECTION_TYPE.get(self.section_type)
        if schema_template:
            self.schema = deepcopy(schema_template)

    def _apply_component_key_if_needed(self):
        if self.component_key:
            return
        self.component_key = AUTO_COMPONENT_KEY_BY_SECTION_TYPE.get(self.section_type, "")

    def _apply_settings_preset_if_needed(self):
        if self.settings:
            return
        settings_template = AUTO_SETTINGS_BY_SECTION_TYPE.get(self.section_type)
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
        return deepcopy(AUTO_SETTINGS_BY_SECTION_TYPE.get(self.section_type, {}))

    def clean(self):
        effective_schema = self.schema or AUTO_SCHEMA_BY_SECTION_TYPE.get(self.section_type, {"fields": []})
        effective_settings = self.settings or AUTO_SETTINGS_BY_SECTION_TYPE.get(self.section_type, {})
        self.validate_schema(effective_schema)
        self.validate_settings(effective_settings)
        if self.content:
            self.validate_content(content=self.content, schema=effective_schema)

    def save(self, *args, **kwargs):
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
        return f"{self.site.name} \u2014 {self.name}"
