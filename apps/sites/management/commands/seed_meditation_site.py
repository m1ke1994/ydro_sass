from copy import deepcopy

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ClientProfile
from apps.sites.models import Site, SiteSection

USER_USERNAME = "meditation"
USER_EMAIL = "meditation@example.com"
USER_PASSWORD = "test-test"

SITE_NAME = "Meditation"
SITE_SLUG = "meditation"
SITE_DOMAIN = "meditation.ru"

SITE_SEO_DEFAULTS = {
    "title": "Meditation — практики и медитации",
    "description": "Премиальный сайт практик, медитаций и личных сессий.",
    "keywords": "медитация, практики, mindfulness, лила",
    "og_title": "Meditation",
    "og_description": "Практики, медитации и пространство внутреннего внимания.",
    "og_image": "",
    "favicon": "",
    "canonical": "",
    "robots_index": True,
}

SECTION_SEEDS = [
    {
        "name": "Hero",
        "slug": "hero",
        "section_type": "hero",
        "component_key": "hero-video",
        "order": 1,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text"},
                {"key": "subtitle", "label": "Подзаголовок", "type": "textarea"},
                {"key": "button_text", "label": "Текст кнопки", "type": "text"},
                {"key": "background_video", "label": "Фоновое видео", "type": "video"},
                {"key": "background_image", "label": "Фоновое изображение", "type": "image"},
            ]
        },
        "content": {
            "title": "Пространство внимания и медитации",
            "subtitle": "Мягкие практики, личные сессии и путь к внутренней ясности.",
            "button_text": "Записаться",
            "background_video": "",
            "background_image": "",
        },
        "settings": {
            "theme": "dark",
            "spacing": "large",
            "animation": "fade-up",
            "background": "video",
            "container": "xl",
            "visible": True,
            "custom_classes": "",
        },
    },
    {
        "name": "О проекте",
        "slug": "about",
        "section_type": "about",
        "component_key": "about-simple",
        "order": 2,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text"},
                {"key": "text", "label": "Текст", "type": "textarea"},
            ]
        },
        "content": {
            "title": "О проекте",
            "text": "Это пространство для бережной работы с собой, телом и вниманием.",
        },
        "settings": {
            "theme": "light",
            "spacing": "medium",
            "animation": "fade-up",
            "background": "none",
            "container": "lg",
            "visible": True,
            "custom_classes": "",
        },
    },
    {
        "name": "Услуги",
        "slug": "services",
        "section_type": "services",
        "component_key": "services-grid",
        "order": 3,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text"},
                {
                    "key": "items",
                    "label": "Список услуг",
                    "type": "repeater",
                    "fields": [
                        {"key": "title", "label": "Название", "type": "text"},
                        {"key": "description", "label": "Описание", "type": "textarea"},
                        {"key": "price", "label": "Цена", "type": "text"},
                    ],
                },
            ]
        },
        "content": {
            "title": "Услуги",
            "items": [
                {
                    "title": "Личная сессия",
                    "description": "Индивидуальная практика под ваш запрос.",
                    "price": "от 5000 ₽",
                },
                {
                    "title": "Медитация",
                    "description": "Мягкая практика для восстановления внимания.",
                    "price": "от 3000 ₽",
                },
            ],
        },
        "settings": {
            "theme": "light",
            "spacing": "medium",
            "animation": "fade-up",
            "background": "none",
            "container": "xl",
            "visible": True,
            "custom_classes": "",
        },
    },
    {
        "name": "Галерея",
        "slug": "gallery",
        "section_type": "gallery",
        "component_key": "gallery-grid",
        "order": 4,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text"},
                {
                    "key": "items",
                    "label": "Изображения",
                    "type": "repeater",
                    "fields": [
                        {"key": "image", "label": "Изображение", "type": "image"},
                        {"key": "caption", "label": "Подпись", "type": "text"},
                    ],
                },
            ]
        },
        "content": {
            "title": "Галерея",
            "items": [],
        },
        "settings": {
            "theme": "light",
            "spacing": "medium",
            "animation": "fade-up",
            "background": "none",
            "container": "xl",
            "visible": True,
            "custom_classes": "",
        },
    },
    {
        "name": "Отзывы",
        "slug": "reviews",
        "section_type": "reviews",
        "component_key": "reviews-slider",
        "order": 5,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text"},
                {
                    "key": "items",
                    "label": "Отзывы",
                    "type": "repeater",
                    "fields": [
                        {"key": "author", "label": "Автор", "type": "text"},
                        {"key": "text", "label": "Текст", "type": "textarea"},
                        {"key": "rating", "label": "Оценка", "type": "number"},
                    ],
                },
            ]
        },
        "content": {
            "title": "Отзывы",
            "items": [],
        },
        "settings": {
            "theme": "light",
            "spacing": "medium",
            "animation": "fade-up",
            "background": "none",
            "container": "lg",
            "visible": True,
            "custom_classes": "",
        },
    },
    {
        "name": "Контакты",
        "slug": "contacts",
        "section_type": "contacts",
        "component_key": "contacts-simple",
        "order": 6,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text"},
                {"key": "phone", "label": "Телефон", "type": "text"},
                {"key": "email", "label": "Email", "type": "text"},
                {"key": "telegram", "label": "Telegram", "type": "text"},
                {"key": "address", "label": "Адрес", "type": "textarea"},
            ]
        },
        "content": {
            "title": "Контакты",
            "phone": "",
            "email": "",
            "telegram": "",
            "address": "",
        },
        "settings": {
            "theme": "light",
            "spacing": "medium",
            "animation": "fade-up",
            "background": "none",
            "container": "md",
            "visible": True,
            "custom_classes": "",
        },
    },
]


class Command(BaseCommand):
    help = "Создает/обновляет тестовый сайт Meditation с базовыми секциями."

    def handle(self, *args, **options):
        with transaction.atomic():
            user = self._upsert_user()
            self._upsert_client_profile(user)
            site = self._upsert_site(user)
            created_sections, updated_sections = self._upsert_sections(site)

        self.stdout.write(self.style.SUCCESS("Seed meditation site завершен."))
        self.stdout.write(f"Пользователь: {user.username}")
        self.stdout.write(f"Сайт: {site.name} ({site.slug})")
        self.stdout.write(f"Секций создано: {created_sections}, обновлено: {updated_sections}")

    def _upsert_user(self):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=USER_USERNAME,
            defaults={"email": USER_EMAIL},
        )

        changed = False
        if user.email != USER_EMAIL:
            user.email = USER_EMAIL
            changed = True

        if not user.check_password(USER_PASSWORD):
            user.set_password(USER_PASSWORD)
            changed = True

        if created or changed:
            user.save()

        return user

    def _upsert_client_profile(self, user):
        profile, created = ClientProfile.objects.get_or_create(
            user=user,
            defaults={"display_name": "Клиент Meditation", "phone": ""},
        )

        changed = False
        if profile.display_name != "Клиент Meditation":
            profile.display_name = "Клиент Meditation"
            changed = True

        if profile.phone is None:
            profile.phone = ""
            changed = True

        if created or changed:
            profile.save()

        return profile

    def _upsert_site(self, user):
        site, created = Site.objects.get_or_create(
            slug=SITE_SLUG,
            defaults={
                "name": SITE_NAME,
                "domain": SITE_DOMAIN,
                "owner": user,
                "is_active": True,
                "seo": deepcopy(SITE_SEO_DEFAULTS),
            },
        )

        changed = False
        if site.name != SITE_NAME:
            site.name = SITE_NAME
            changed = True
        if site.domain != SITE_DOMAIN:
            site.domain = SITE_DOMAIN
            changed = True
        if site.owner_id != user.id:
            site.owner = user
            changed = True
        if not site.is_active:
            site.is_active = True
            changed = True

        current_seo = site.seo if isinstance(site.seo, dict) else {}
        merged_seo = deepcopy(SITE_SEO_DEFAULTS)
        merged_seo.update(current_seo)
        if site.seo != merged_seo:
            site.seo = merged_seo
            changed = True

        if created or changed:
            site.save()

        return site

    def _upsert_sections(self, site):
        created_count = 0
        updated_count = 0

        for section_seed in SECTION_SEEDS:
            section, created = SiteSection.objects.get_or_create(
                site=site,
                slug=section_seed["slug"],
                defaults={
                    "name": section_seed["name"],
                    "section_type": section_seed["section_type"],
                    "component_key": section_seed["component_key"],
                    "order": section_seed["order"],
                    "is_active": True,
                    "schema": deepcopy(section_seed["schema"]),
                    "content": deepcopy(section_seed["content"]),
                    "settings": deepcopy(section_seed["settings"]),
                },
            )

            if created:
                created_count += 1
                continue

            changed = False
            if section.name != section_seed["name"]:
                section.name = section_seed["name"]
                changed = True
            if section.section_type != section_seed["section_type"]:
                section.section_type = section_seed["section_type"]
                changed = True
            if section.order != section_seed["order"]:
                section.order = section_seed["order"]
                changed = True
            if not section.is_active:
                section.is_active = True
                changed = True
            if not section.component_key:
                section.component_key = section_seed["component_key"]
                changed = True
            if not section.schema:
                section.schema = deepcopy(section_seed["schema"])
                changed = True
            if not section.settings:
                section.settings = deepcopy(section_seed["settings"])
                changed = True

            if not section.content:
                candidate_content = deepcopy(section_seed["content"])
                try:
                    SiteSection.validate_schema(section.schema)
                    SiteSection.validate_content(content=candidate_content, schema=section.schema)
                except ValidationError as exc:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Секция '{section.slug}' пропущена по content: {exc}"
                        )
                    )
                else:
                    section.content = candidate_content
                    changed = True

            if changed:
                section.save()
                updated_count += 1

        return created_count, updated_count
