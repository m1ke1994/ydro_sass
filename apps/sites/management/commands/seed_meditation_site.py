from copy import deepcopy

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.sites.models import SectionSchema, Site, SiteSection

USER_EMAIL = "test@test.ru"
USER_PASSWORD = "test-test"
USER_USERNAME = "test@test.ru"

SITE_DATA = {
    "name": "Сайт медитации",
    "slug": "meditation",
    "domain": "localhost:5173",
    "is_active": True,
}

SECTION_SEEDS = [
    {
        "key": "hero",
        "title": "Hero",
        "order": 1,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text"},
                {"key": "subtitle", "label": "Subtitle", "type": "text"},
                {"key": "description", "label": "Description", "type": "textarea"},
                {"key": "buttonText", "label": "Button text", "type": "text"},
                {"key": "buttonLink", "label": "Button link", "type": "text"},
                {"key": "backgroundVideo", "label": "Background video", "type": "video"},
                {"key": "backgroundImage", "label": "Background image", "type": "image"},
            ]
        },
        "content": {
            "title": "Лила Москва",
            "subtitle": "Игра, медитация и практика осознанности",
            "description": "Мягкая практика для возвращения ясности, ресурса и контакта с собой.",
            "buttonText": "Записаться",
            "buttonLink": "#contacts",
            "backgroundVideo": "/images/Lila_Olga_2.2_compressed.mp4",
            "backgroundImage": "/images/Lila_Olga_2.2.poster.jpg",
        },
    },
    {
        "key": "about",
        "title": "About",
        "order": 2,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text"},
                {"key": "text", "label": "Text", "type": "textarea"},
                {"key": "image", "label": "Image", "type": "image"},
                {
                    "key": "items",
                    "label": "Items",
                    "type": "repeater",
                    "fields": [
                        {"key": "title", "label": "Title", "type": "text"},
                        {"key": "text", "label": "Text", "type": "textarea"},
                    ],
                },
            ]
        },
        "content": {
            "title": "О проекте",
            "text": "Пространство для внимательной и бережной работы с внутренним состоянием.",
            "image": "/images/2025-02-26 12-35-42.JPG",
            "items": [
                {"title": "Без спешки", "text": "Практика проходит в комфортном ритме."},
                {"title": "С проводником", "text": "Поддержка и ясные шаги на каждом этапе."},
            ],
        },
    },
    {
        "key": "services",
        "title": "Services",
        "order": 3,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text"},
                {"key": "description", "label": "Description", "type": "textarea"},
                {
                    "key": "items",
                    "label": "Items",
                    "type": "repeater",
                    "fields": [
                        {"key": "title", "label": "Title", "type": "text"},
                        {"key": "description", "label": "Description", "type": "textarea"},
                        {"key": "image", "label": "Image", "type": "image"},
                        {"key": "type", "label": "Type", "type": "text"},
                    ],
                },
            ]
        },
        "content": {
            "title": "Медитации",
            "description": "Форматы практики для восстановления и внутреннего баланса.",
            "items": [
                {
                    "title": "Глубокое расслабление",
                    "description": "Снятие напряжения и возвращение в спокойное состояние.",
                    "image": "/images/m1.jpg",
                    "type": "image",
                },
                {
                    "title": "Восстановление ресурса",
                    "description": "Практика дыхания и тишины для внутренней опоры.",
                    "image": "/images/m3.jpg",
                    "type": "image",
                },
            ],
        },
    },
    {
        "key": "prices",
        "title": "Prices",
        "order": 4,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text"},
                {
                    "key": "items",
                    "label": "Items",
                    "type": "repeater",
                    "fields": [
                        {"key": "title", "label": "Title", "type": "text"},
                        {"key": "price", "label": "Price", "type": "text"},
                        {"key": "duration", "label": "Duration", "type": "text"},
                        {"key": "description", "label": "Description", "type": "textarea"},
                    ],
                },
            ]
        },
        "content": {
            "title": "Форматы услуг",
            "items": [
                {
                    "title": "Индивидуальная игра Лила",
                    "price": "18 000 ₽",
                    "duration": "4 часа",
                    "description": "Личная встреча с глубоким разбором запроса.",
                },
                {
                    "title": "Групповая медитация",
                    "price": "по запросу",
                    "duration": "1 час",
                    "description": "Спокойная практика в группе в удобном темпе.",
                },
            ],
        },
    },
    {
        "key": "gallery",
        "title": "Gallery",
        "order": 5,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text"},
                {
                    "key": "items",
                    "label": "Items",
                    "type": "repeater",
                    "fields": [
                        {"key": "src", "label": "Source", "type": "image"},
                        {"key": "alt", "label": "Alt", "type": "text"},
                        {"key": "title", "label": "Title", "type": "text"},
                    ],
                },
            ]
        },
        "content": {
            "title": "Галерея",
            "items": [
                {"src": "/images/DSC08101.JPG", "alt": "Практика", "title": "Пространство встречи"},
                {"src": "/images/IMG_5131.JPG", "alt": "Детали", "title": "Детали пространства"},
            ],
        },
    },
    {
        "key": "reviews",
        "title": "Reviews",
        "order": 6,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text"},
                {
                    "key": "items",
                    "label": "Items",
                    "type": "repeater",
                    "fields": [
                        {"key": "name", "label": "Name", "type": "text"},
                        {"key": "date", "label": "Date", "type": "text"},
                        {"key": "avatar", "label": "Avatar", "type": "image"},
                        {"key": "text", "label": "Text", "type": "textarea"},
                    ],
                },
            ]
        },
        "content": {
            "title": "Отзывы участников",
            "items": [
                {
                    "name": "Участница игры",
                    "date": "Отзыв из Telegram",
                    "avatar": "/images/IMG_1245.JPG",
                    "text": "Очень бережный формат, после игры появилось больше ясности и спокойствия.",
                },
                {
                    "name": "Участница игры",
                    "date": "Отзыв из Telegram",
                    "avatar": "/images/IMG_1246.JPG",
                    "text": "Комфортная атмосфера, глубокий процесс и практические инсайты.",
                },
            ],
        },
    },
    {
        "key": "contacts",
        "title": "Contacts",
        "order": 7,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text"},
                {"key": "phone", "label": "Phone", "type": "text"},
                {"key": "email", "label": "Email", "type": "text"},
                {"key": "telegram", "label": "Telegram", "type": "text"},
                {"key": "address", "label": "Address", "type": "textarea"},
            ]
        },
        "content": {
            "title": "Контакты и запись",
            "phone": "+7 903 198-91-88",
            "email": "test@test.ru",
            "telegram": "@leelabirdcase",
            "address": "Москва, ул. Ботаническая, 33В стр 1",
        },
    },
    {
        "key": "footer",
        "title": "Footer",
        "order": 8,
        "schema": {
            "fields": [
                {"key": "text", "label": "Text", "type": "textarea"},
                {
                    "key": "links",
                    "label": "Links",
                    "type": "repeater",
                    "fields": [
                        {"key": "label", "label": "Label", "type": "text"},
                        {"key": "href", "label": "Href", "type": "text"},
                        {"key": "target", "label": "Target", "type": "text"},
                    ],
                },
            ]
        },
        "content": {
            "text": "Игра Лила в Москве - путь к ясности через честный диалог с собой.",
            "links": [
                {"label": "Telegram", "href": "https://t.me/leelabirdcase", "target": "_blank"},
                {"label": "Записаться", "href": "#contacts", "target": "_self"},
            ],
        },
    },
]


class Command(BaseCommand):
    help = "Create or update demo meditation site with sections and test user."

    def handle(self, *args, **options):
        with transaction.atomic():
            user = self._upsert_user()
            site = self._upsert_site(user)
            created_count, updated_count = self._upsert_sections(site)

        self.stdout.write(self.style.SUCCESS("Seed completed."))
        self.stdout.write(f"User: {USER_EMAIL}")
        self.stdout.write("Password: test-test")
        self.stdout.write(f"Site: {site.slug} ({site.domain})")
        self.stdout.write(f"Sections created: {created_count}, updated: {updated_count}")

    def _upsert_user(self):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            email=USER_EMAIL,
            defaults={"username": USER_USERNAME},
        )

        changed = False
        if user.username != USER_USERNAME:
            user.username = USER_USERNAME
            changed = True

        if not user.check_password(USER_PASSWORD):
            user.set_password(USER_PASSWORD)
            changed = True

        if created or changed:
            user.save()

        return user

    def _upsert_site(self, user):
        site, created = Site.objects.get_or_create(
            slug=SITE_DATA["slug"],
            defaults={
                "name": SITE_DATA["name"],
                "domain": SITE_DATA["domain"],
                "owner": user,
                "is_active": SITE_DATA["is_active"],
            },
        )

        changed = False
        for field in ("name", "domain", "is_active"):
            value = SITE_DATA[field]
            if getattr(site, field) != value:
                setattr(site, field, value)
                changed = True

        if site.owner_id != user.id:
            site.owner = user
            changed = True

        if created or changed:
            site.save()

        return site

    def _upsert_sections(self, site):
        created_count = 0
        updated_count = 0

        for seed in SECTION_SEEDS:
            SectionSchema.objects.update_or_create(
                section_key=seed["key"],
                defaults={
                    "title": seed["title"],
                    "schema": deepcopy(seed["schema"]),
                    "description": f"Auto schema for section '{seed['key']}'",
                },
            )

            section, created = SiteSection.objects.get_or_create(
                site=site,
                key=seed["key"],
                defaults={
                    "title": seed["title"],
                    "section_type": seed["key"],
                    "order": seed["order"],
                    "is_active": True,
                    "schema": deepcopy(seed["schema"]),
                    "content": deepcopy(seed["content"]),
                },
            )

            if created:
                created_count += 1
                continue

            changed = False
            if section.title != seed["title"]:
                section.title = seed["title"]
                changed = True
            if section.section_type != seed["key"]:
                section.section_type = seed["key"]
                changed = True
            if section.order != seed["order"]:
                section.order = seed["order"]
                changed = True
            if not section.is_active:
                section.is_active = True
                changed = True
            if section.schema != seed["schema"]:
                section.schema = deepcopy(seed["schema"])
                changed = True
            if section.content != seed["content"]:
                section.content = deepcopy(seed["content"])
                changed = True

            if changed:
                section.save()
                updated_count += 1

        return created_count, updated_count
