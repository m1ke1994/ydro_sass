from copy import deepcopy
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ClientProfile
from apps.sites.models import SectionSchema, Site, SiteSection

SECTION_SEEDS = [
    {
        "key": "hero",
        "title": "Hero",
        "order": 1,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "textarea", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {"key": "button_text", "label": "Текст кнопки", "type": "text", "default": ""},
                {"key": "button_link", "label": "Ссылка кнопки", "type": "text", "default": ""},
                {"key": "image", "label": "Фоновое изображение", "type": "image", "default": ""},
                {"key": "background_video", "label": "Фоновое видео", "type": "video", "default": ""},
                {"key": "order", "label": "Порядок", "type": "number", "default": 1},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "A Meditation",
            "subtitle": "Пространство практик и бережного внимания к себе",
            "description": "Медитации и игра Лила для ясности, внутренней опоры и спокойствия.",
            "button_text": "Записаться",
            "button_link": "#contacts",
            "image": "/images/Lila_Olga_2.2.poster.jpg",
            "background_video": "/images/Lila_Olga_2.2_compressed.mp4",
            "order": 1,
            "is_active": True,
        },
    },
    {
        "key": "about",
        "title": "About",
        "order": 2,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {"key": "button_text", "label": "Текст кнопки", "type": "text", "default": ""},
                {"key": "button_link", "label": "Ссылка кнопки", "type": "text", "default": ""},
                {"key": "image", "label": "Изображение", "type": "image", "default": ""},
                {"key": "order", "label": "Порядок", "type": "number", "default": 2},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "О проекте",
            "subtitle": "Бережные практики без спешки",
            "description": "Мы создаём спокойное пространство, где можно замедлиться, услышать себя и выбрать следующий шаг в жизни и работе.",
            "button_text": "Подробнее",
            "button_link": "#guide",
            "image": "/images/2025-02-26 12-35-42.JPG",
            "order": 2,
            "is_active": True,
        },
    },
    {
        "key": "guide",
        "title": "Guide",
        "order": 3,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {"key": "button_text", "label": "Текст кнопки", "type": "text", "default": ""},
                {"key": "button_link", "label": "Ссылка кнопки", "type": "text", "default": ""},
                {"key": "image", "label": "Фото", "type": "image", "default": ""},
                {"key": "order", "label": "Порядок", "type": "number", "default": 3},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "Проводник практик",
            "subtitle": "Ольга Бердникова",
            "description": "Провожу игру Лила и медитации мягко, бережно и понятно, чтобы изменения в жизни были устойчивыми и реальными.",
            "button_text": "Выбрать формат",
            "button_link": "#services",
            "image": "/images/2025-02-26 12-35-42.JPG",
            "order": 3,
            "is_active": True,
        },
    },
    {
        "key": "services",
        "title": "Services",
        "order": 4,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {"key": "button_text", "label": "Текст кнопки", "type": "text", "default": ""},
                {"key": "button_link", "label": "Ссылка кнопки", "type": "text", "default": ""},
                {"key": "image", "label": "Изображение", "type": "image", "default": ""},
                {"key": "order", "label": "Порядок", "type": "number", "default": 4},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
                {
                    "key": "tabs",
                    "label": "Вкладки форматов",
                    "type": "repeater",
                    "default": [],
                    "fields": [
                        {"key": "key", "label": "Ключ", "type": "text", "default": ""},
                        {"key": "label", "label": "Название", "type": "text", "default": ""},
                        {
                            "key": "cards",
                            "label": "Карточки",
                            "type": "repeater",
                            "default": [],
                            "fields": [
                                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                                {"key": "duration", "label": "Длительность", "type": "text", "default": ""},
                                {"key": "format", "label": "Формат", "type": "text", "default": ""},
                                {"key": "price", "label": "Цена", "type": "text", "default": ""},
                                {"key": "button_text", "label": "Кнопка", "type": "text", "default": ""},
                            ],
                        },
                    ],
                },
            ]
        },
        "content": {
            "title": "Форматы участия",
            "subtitle": "Выберите практику, которая подходит вам сейчас",
            "description": "Все форматы можно адаптировать под ваш запрос.",
            "button_text": "Записаться",
            "button_link": "#contacts",
            "image": "",
            "order": 4,
            "is_active": True,
            "tabs": [
                {
                    "key": "lila",
                    "label": "Игра Лила",
                    "cards": [
                        {
                            "title": "Индивидуальная игра Лила",
                            "description": "Личная практика для глубокого разбора запроса, поиска внутренней опоры и честного диалога с собой.",
                            "duration": "2–3 часа",
                            "format": "очно / онлайн",
                            "price": "от 5 000 ₽",
                            "button_text": "Записаться",
                        },
                        {
                            "title": "Групповая игра Лила",
                            "description": "Практика в малой группе, где каждый участник проходит свой путь через поле игры и получает поддержку пространства.",
                            "duration": "3–4 часа",
                            "format": "очно",
                            "price": "от 3 000 ₽",
                            "button_text": "Записаться",
                        },
                        {
                            "title": "Парная игра Лила",
                            "description": "Формат для двух участников, которые хотят посмотреть на общий запрос, отношения или совместное движение.",
                            "duration": "3 часа",
                            "format": "очно / онлайн",
                            "price": "от 7 000 ₽",
                            "button_text": "Записаться",
                        },
                    ],
                },
                {
                    "key": "meditations",
                    "label": "Медитации",
                    "cards": [
                        {
                            "title": "Индивидуальная медитация",
                            "description": "Персональная мягкая практика для восстановления, замедления и возвращения к внутреннему спокойствию.",
                            "duration": "60 минут",
                            "format": "очно / онлайн",
                            "price": "от 3 000 ₽",
                            "button_text": "Записаться",
                        },
                        {
                            "title": "Групповая медитация",
                            "description": "Спокойная практика в группе, которая помогает выдохнуть, отпустить напряжение и почувствовать опору.",
                            "duration": "60–90 минут",
                            "format": "очно",
                            "price": "от 1 500 ₽",
                            "button_text": "Записаться",
                        },
                        {
                            "title": "Медитация сопровождения",
                            "description": "Формат регулярных встреч для тех, кто хочет мягко встроить практику в свою жизнь и идти постепенно.",
                            "duration": "4 встречи",
                            "format": "очно / онлайн",
                            "price": "по договоренности",
                            "button_text": "Записаться",
                        },
                    ],
                },
            ],
        },
    },
    {
        "key": "reviews",
        "title": "Reviews",
        "order": 5,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {"key": "button_text", "label": "Текст кнопки", "type": "text", "default": ""},
                {"key": "button_link", "label": "Ссылка кнопки", "type": "text", "default": ""},
                {"key": "image", "label": "Изображение", "type": "image", "default": ""},
                {"key": "order", "label": "Порядок", "type": "number", "default": 5},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
                {
                    "key": "items",
                    "label": "Отзывы",
                    "type": "repeater",
                    "default": [],
                    "fields": [
                        {"key": "name", "label": "Имя", "type": "text", "default": ""},
                        {"key": "date", "label": "Дата", "type": "text", "default": ""},
                        {"key": "avatar", "label": "Аватар", "type": "image", "default": ""},
                        {"key": "text", "label": "Текст", "type": "textarea", "default": ""},
                    ],
                },
            ]
        },
        "content": {
            "title": "Отзывы участников",
            "subtitle": "Реальные впечатления",
            "description": "После практик участники отмечают больше ясности и спокойствия.",
            "button_text": "Читать отзывы",
            "button_link": "https://t.me/leelabirdcase",
            "image": "",
            "order": 5,
            "is_active": True,
            "items": [
                {
                    "name": "Участница игры",
                    "date": "Отзыв из Telegram",
                    "avatar": "/images/IMG_1245.JPG",
                    "text": "Очень бережная атмосфера и глубокий процесс. После встречи стало легче принимать решения.",
                },
                {
                    "name": "Участница медитаций",
                    "date": "Отзыв из Telegram",
                    "avatar": "/images/IMG_1246.JPG",
                    "text": "Регулярные практики помогли снизить уровень стресса и вернуть внутренний баланс.",
                },
            ],
        },
    },
    {
        "key": "contacts",
        "title": "Contacts",
        "order": 6,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {"key": "button_text", "label": "Текст кнопки", "type": "text", "default": ""},
                {"key": "button_link", "label": "Ссылка кнопки", "type": "text", "default": ""},
                {"key": "image", "label": "Изображение", "type": "image", "default": ""},
                {"key": "phone", "label": "Телефон", "type": "text", "default": ""},
                {"key": "email", "label": "Email", "type": "text", "default": ""},
                {"key": "telegram", "label": "Telegram", "type": "text", "default": ""},
                {"key": "address", "label": "Адрес", "type": "textarea", "default": ""},
                {
                    "key": "locations",
                    "label": "Локации",
                    "type": "repeater",
                    "default": [],
                    "fields": [
                        {"key": "title", "label": "Название", "type": "text", "default": ""},
                        {"key": "address", "label": "Адрес", "type": "text", "default": ""},
                        {"key": "lat", "label": "Широта", "type": "number", "default": 0},
                        {"key": "lng", "label": "Долгота", "type": "number", "default": 0},
                    ],
                },
                {"key": "order", "label": "Порядок", "type": "number", "default": 6},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "Контакты",
            "subtitle": "Свяжитесь для записи",
            "description": "Напишите или позвоните, чтобы подобрать подходящий формат практики.",
            "button_text": "Написать",
            "button_link": "mailto:admin@test.ru",
            "image": "",
            "phone": "+7 903 198-91-88",
            "email": "admin@test.ru",
            "telegram": "@leelabirdcase",
            "address": "Москва, ул. Ботаническая, 33В стр 1",
            "locations": [
                {
                    "title": "Парк Горького",
                    "address": "Москва, ул. Крымский Вал, 9",
                    "lat": 55.7298,
                    "lng": 37.6011,
                },
                {
                    "title": "Патриаршие пруды",
                    "address": "Москва, Патриаршие пруды",
                    "lat": 55.7636,
                    "lng": 37.5906,
                },
                {
                    "title": "ВДНХ",
                    "address": "Москва, проспект Мира, 119",
                    "lat": 55.8298,
                    "lng": 37.6328,
                },
                {
                    "title": "Третьяковская галерея",
                    "address": "Москва, Лаврушинский пер., 10",
                    "lat": 55.7414,
                    "lng": 37.6208,
                },
            ],
            "order": 6,
            "is_active": True,
        },
    },
    {
        "key": "footer",
        "title": "Footer",
        "order": 7,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {"key": "button_text", "label": "Текст кнопки", "type": "text", "default": ""},
                {"key": "button_link", "label": "Ссылка кнопки", "type": "text", "default": ""},
                {"key": "image", "label": "Изображение", "type": "image", "default": ""},
                {"key": "order", "label": "Порядок", "type": "number", "default": 7},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
                {"key": "text", "label": "Текст", "type": "textarea", "default": ""},
                {
                    "key": "links",
                    "label": "Ссылки",
                    "type": "repeater",
                    "default": [],
                    "fields": [
                        {"key": "label", "label": "Подпись", "type": "text", "default": ""},
                        {"key": "href", "label": "Ссылка", "type": "text", "default": ""},
                        {"key": "target", "label": "Target", "type": "text", "default": "_self"},
                    ],
                },
            ]
        },
        "content": {
            "title": "Footer",
            "subtitle": "",
            "description": "",
            "button_text": "",
            "button_link": "",
            "image": "",
            "order": 7,
            "is_active": True,
            "text": "A Meditation — практики осознанности, медитации и игра Лила для мягких изменений в жизни.",
            "links": [
                {"label": "Записаться", "href": "#contacts", "target": "_self"},
                {"label": "Telegram", "href": "https://t.me/leelabirdcase", "target": "_blank"},
            ],
        },
    },
]


class Command(BaseCommand):
    help = "Create and refresh full demo data for the public A Meditation site."

    @transaction.atomic
    def handle(self, *args, **options):
        user = self._upsert_admin_user()
        self._cleanup_legacy_users(user)
        self._upsert_profile(user)
        site = self._upsert_site(user)
        self._upsert_sections(site)

        self.stdout.write(self.style.SUCCESS("seed_demo_data completed."))
        self.stdout.write(f"site={site.slug}")
        self.stdout.write(f"admin={user.email}")

    def _upsert_admin_user(self):
        email = os.getenv("SUPERUSER_EMAIL", "admin@test.ru")
        password = os.getenv("SUPERUSER_PASSWORD", "testtest")
        username = os.getenv("SUPERUSER_USERNAME", "admin")

        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).order_by("id").first()
        if user is None:
            user = user_model.objects.filter(username=username).order_by("id").first()

        if user is None:
            user = user_model.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True,
            )
            return user

        user.username = username
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        return user

    def _cleanup_legacy_users(self, admin_user):
        user_model = get_user_model()
        user_model.objects.exclude(id=admin_user.id).delete()

    def _upsert_profile(self, user):
        ClientProfile.objects.update_or_create(
            user=user,
            defaults={
                "display_name": "Администратор",
                "phone": "+7 900 000-00-00",
            },
        )

    def _upsert_site(self, owner):
        site, _ = Site.objects.update_or_create(
            slug=os.getenv("DEMO_SITE_SLUG", "a-meditation"),
            defaults={
                "name": os.getenv("DEMO_SITE_NAME", "A Meditation"),
                "domain": os.getenv("DEMO_SITE_DOMAIN", "localhost"),
                "owner": owner,
                "is_active": True,
                "seo": {
                    "title": "A Meditation",
                    "description": "Публичный демо-сайт практик медитации и игры Лила",
                },
            },
        )
        return site

    def _upsert_sections(self, site):
        keep_keys = []
        for section_seed in SECTION_SEEDS:
            keep_keys.append(section_seed["key"])

            SectionSchema.objects.update_or_create(
                section_key=section_seed["key"],
                defaults={
                    "title": section_seed["title"],
                    "schema": deepcopy(section_seed["schema"]),
                    "description": f"Demo schema for {section_seed['key']}",
                },
            )

            SiteSection.objects.update_or_create(
                site=site,
                key=section_seed["key"],
                defaults={
                    "title": section_seed["title"],
                    "section_type": section_seed["key"],
                    "order": section_seed["order"],
                    "is_active": True,
                    "schema": deepcopy(section_seed["schema"]),
                    "content": deepcopy(section_seed["content"]),
                    "component_key": f"{section_seed['key']}-section",
                    "settings": {
                        "theme": "light",
                        "container": "xl",
                        "animation": "fade-up",
                        "demo": True,
                    },
                    "seo": {
                        "title": f"A Meditation | {section_seed['title']}",
                    },
                },
            )

        SiteSection.objects.filter(site=site).exclude(key__in=keep_keys).delete()
