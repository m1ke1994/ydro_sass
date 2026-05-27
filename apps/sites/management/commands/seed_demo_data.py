from copy import deepcopy
import mimetypes
import os
from pathlib import Path
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ClientProfile
from apps.mediafiles.models import MediaFile
from apps.sites.models import SectionSchema, Site, SiteSection

MEDIA_KEY_HINTS = ("image", "video", "avatar", "poster", "photo", "background")
SECTION_MEDIA_FOLDER_ALIAS = {
    "services": "formats",
}

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
                {"key": "tag", "label": "Метка", "type": "text", "default": ""},
                {"key": "order", "label": "Порядок", "type": "number", "default": 1},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "A Meditation",
            "subtitle": "Пространство практик и бережного внимания к себе",
            "description": "Практика, где игра становится проводником к ясности, спокойствию и внутренним ответам.",
            "button_text": "Записаться на игру",
            "button_link": "#contacts",
            "image": "/images/Lila_Olga_2.2.poster.jpg",
            "background_video": "/images/Lila_Olga_2.2_compressed.mp4",
            "tag": "ЛИЛА МОСКВА",
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
                {"key": "image", "label": "Изображение", "type": "image", "default": ""},
                {"key": "order", "label": "Порядок", "type": "number", "default": 2},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "О проекте",
            "subtitle": "Бережные практики без спешки",
            "description": "Мы создаем спокойное пространство, где можно замедлиться, услышать себя и выбрать следующий шаг.",
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
                {"key": "tag", "label": "Метка", "type": "text", "default": ""},
                {"key": "image", "label": "Фото", "type": "image", "default": ""},
                {"key": "order", "label": "Порядок", "type": "number", "default": 3},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "Проводник практик",
            "subtitle": "Ольга Бердникова",
            "description": "Практик осознанности, медитации и Игры Лила.",
            "tag": "Проводник игры Лила",
            "image": "/images/2025-02-26 12-35-42.JPG",
            "order": 3,
            "is_active": True,
        },
    },
    {
        "key": "meditations",
        "title": "Meditations",
        "order": 4,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {
                    "key": "items",
                    "label": "Практики",
                    "type": "repeater",
                    "default": [],
                    "fields": [
                        {"key": "number", "label": "Номер", "type": "text", "default": ""},
                        {"key": "title", "label": "Название", "type": "text", "default": ""},
                        {"key": "text", "label": "Описание", "type": "textarea", "default": ""},
                        {"key": "image", "label": "Изображение", "type": "image", "default": ""},
                        {"key": "type", "label": "Тип", "type": "select", "default": "image", "options": ["image", "video"]},
                    ],
                },
                {"key": "order", "label": "Порядок", "type": "number", "default": 4},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "Медитации",
            "subtitle": "Практики тишины",
            "description": "Пространство тишины, бережного внимания и внутренней опоры.",
            "items": [
                {
                    "number": "01",
                    "title": "Глубокое расслабление",
                    "text": "Мягкая практика для снятия напряжения.",
                    "image": "/images/m1.jpg",
                    "type": "image",
                },
                {
                    "number": "02",
                    "title": "Восстановление ресурса",
                    "text": "Тишина и дыхание для внутреннего восстановления.",
                    "image": "/images/Lila_Olga_2.2_compressed.mp4",
                    "type": "video",
                },
                {
                    "number": "03",
                    "title": "Контакт с собой",
                    "text": "Практика возвращения к ощущениям и ясности.",
                    "image": "/images/m3.jpg",
                    "type": "image",
                },
                {
                    "number": "04",
                    "title": "Внутренняя настройка",
                    "text": "Мягкая настройка на важный период жизни.",
                    "image": "/images/m4.jpg",
                    "type": "image",
                },
            ],
            "order": 4,
            "is_active": True,
        },
    },
    {
        "key": "gallery",
        "title": "Gallery",
        "order": 5,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {
                    "key": "items",
                    "label": "Галерея",
                    "type": "repeater",
                    "default": [],
                    "fields": [
                        {"key": "src", "label": "Изображение", "type": "image", "default": ""},
                        {"key": "alt", "label": "Alt", "type": "text", "default": ""},
                        {"key": "title", "label": "Название", "type": "text", "default": ""},
                    ],
                },
                {"key": "order", "label": "Порядок", "type": "number", "default": 5},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "Галерея",
            "subtitle": "Визуальная история",
            "items": [
                {"src": "/images/DSC08101.JPG", "alt": "Атмосфера практики", "title": "Пространство встречи"},
                {"src": "/images/2025-02-26 13-06-17.JPG", "alt": "Тихая практика", "title": "Тихая практика"},
                {"src": "/images/IMG_5131.JPG", "alt": "Детали пространства", "title": "Детали пространства"},
                {"src": "/images/Lila_Olga_2.2.poster.jpg", "alt": "Глубокое состояние", "title": "Глубокое состояние"},
            ],
            "order": 5,
            "is_active": True,
        },
    },
    {
        "key": "services",
        "title": "Services",
        "order": 6,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {"key": "button_text", "label": "Текст кнопки", "type": "text", "default": ""},
                {"key": "button_link", "label": "Ссылка кнопки", "type": "text", "default": ""},
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
                {"key": "order", "label": "Порядок", "type": "number", "default": 6},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "Форматы участия",
            "subtitle": "Выберите практику, которая подходит вам сейчас",
            "description": "Все форматы можно адаптировать под ваш запрос.",
            "button_text": "Записаться",
            "button_link": "#contacts",
            "tabs": [
                {
                    "key": "lila",
                    "label": "Игра Лила",
                    "cards": [
                        {
                            "title": "Индивидуальная игра Лила",
                            "description": "Личная практика для глубокого разбора запроса и поиска внутренней опоры.",
                            "duration": "2-3 часа",
                            "format": "очно / онлайн",
                            "price": "от 5 000 ₽",
                            "button_text": "Записаться",
                        },
                        {
                            "title": "Групповая игра Лила",
                            "description": "Практика в малой группе, где каждый участник проходит свой путь через поле игры.",
                            "duration": "3-4 часа",
                            "format": "очно",
                            "price": "от 3 000 ₽",
                            "button_text": "Записаться",
                        },
                        {
                            "title": "Парная игра Лила",
                            "description": "Формат для двух участников с общим запросом и сопровождением проводника.",
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
                            "description": "Персональная практика для восстановления, тишины и контакта с собой.",
                            "duration": "60 минут",
                            "format": "очно / онлайн",
                            "price": "от 3 000 ₽",
                            "button_text": "Записаться",
                        },
                        {
                            "title": "Групповая медитация",
                            "description": "Мягкая практика в группе для замедления и внутренней опоры.",
                            "duration": "60-90 минут",
                            "format": "очно",
                            "price": "от 1 500 ₽",
                            "button_text": "Записаться",
                        },
                        {
                            "title": "Медитация сопровождения",
                            "description": "Формат регулярных встреч для постепенного и бережного пути.",
                            "duration": "4 встречи",
                            "format": "очно / онлайн",
                            "price": "по договоренности",
                            "button_text": "Записаться",
                        },
                    ],
                },
            ],
            "order": 6,
            "is_active": True,
        },
    },
    {
        "key": "reviews",
        "title": "Reviews",
        "order": 7,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
                {"key": "button_text", "label": "Текст кнопки", "type": "text", "default": ""},
                {"key": "button_link", "label": "Ссылка кнопки", "type": "text", "default": ""},
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
                {"key": "order", "label": "Порядок", "type": "number", "default": 7},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "Отзывы участников",
            "subtitle": "Реальные впечатления",
            "description": "Истории людей, которые прошли практику и поделились своим опытом.",
            "button_text": "Читать больше отзывов",
            "button_link": "https://t.me/leelabirdcase",
            "items": [
                {
                    "name": "Участница игры",
                    "date": "Отзыв из Telegram",
                    "avatar": "/images/IMG_1245.JPG",
                    "text": "Очень бережная атмосфера и глубокий процесс. После встречи стало легче принимать решения.",
                },
                {
                    "name": "Участница игры",
                    "date": "Отзыв из Telegram",
                    "avatar": "/images/IMG_1246.JPG",
                    "text": "Комфортная игра, личные инсайты и спокойное пространство для честного диалога.",
                },
                {
                    "name": "Участница игры",
                    "date": "Отзыв из Telegram",
                    "avatar": "/images/IMG_1249.JPG",
                    "text": "Игра помогла подсветить глубинные вещи и наметить уверенное движение вперед.",
                },
                {
                    "name": "Участница игры",
                    "date": "Отзыв из Telegram",
                    "avatar": "/images/IMG_1988.JPG",
                    "text": "Спокойно, бережно и честно. Появилась ясность и внутренняя опора.",
                },
            ],
            "order": 7,
            "is_active": True,
        },
    },
    {
        "key": "contacts",
        "title": "Contacts",
        "order": 8,
        "schema": {
            "fields": [
                {"key": "title", "label": "Заголовок", "type": "text", "default": ""},
                {"key": "subtitle", "label": "Подзаголовок", "type": "text", "default": ""},
                {"key": "description", "label": "Описание", "type": "textarea", "default": ""},
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
                {"key": "order", "label": "Порядок", "type": "number", "default": 8},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "title": "Контакты",
            "subtitle": "Свяжитесь для записи",
            "description": "Напишите или позвоните, чтобы подобрать удобный формат практики.",
            "phone": "+7 903 198-91-88",
            "email": "admin@test.ru",
            "telegram": "@leelabirdcase",
            "address": "Москва, ул. Ботаническая, 33В стр 1",
            "locations": [
                {"title": "Парк Горького", "address": "Москва, ул. Крымский Вал, 9", "lat": 55.7298, "lng": 37.6011},
                {"title": "Патриаршие пруды", "address": "Москва, Патриаршие пруды", "lat": 55.7636, "lng": 37.5906},
                {"title": "ВДНХ", "address": "Москва, проспект Мира, 119", "lat": 55.8298, "lng": 37.6328},
                {"title": "Третьяковская галерея", "address": "Москва, Лаврушинский пер., 10", "lat": 55.7414, "lng": 37.6208},
            ],
            "order": 8,
            "is_active": True,
        },
    },
    {
        "key": "footer",
        "title": "Footer",
        "order": 9,
        "schema": {
            "fields": [
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
                {"key": "order", "label": "Порядок", "type": "number", "default": 9},
                {"key": "is_active", "label": "Активно", "type": "boolean", "default": True},
            ]
        },
        "content": {
            "text": "A Meditation — практики осознанности, медитации и игра Лила для мягких изменений в жизни.",
            "links": [
                {"label": "Записаться", "href": "#contacts", "target": "_self"},
                {"label": "Telegram", "href": "https://t.me/leelabirdcase", "target": "_blank"},
            ],
            "order": 9,
            "is_active": True,
        },
    },
]


class Command(BaseCommand):
    help = "Create and refresh full demo data for the public A Meditation site with media in Django MEDIA."

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

    def _public_assets_dir(self):
        configured = os.getenv("DEMO_PUBLIC_SITE_DIR", "").strip()
        if configured:
            return Path(configured)

        backend_root = Path(__file__).resolve().parents[4]
        embedded_dir = backend_root / "demo_public"
        if embedded_dir.exists():
            return embedded_dir
        sibling_dir = backend_root.parent / "a-meditation" / "frontend" / "public"
        return sibling_dir

    def _resolve_source_asset(self, asset_path):
        if not isinstance(asset_path, str) or not asset_path.startswith("/"):
            return None

        public_dir = self._public_assets_dir()
        candidate = (public_dir / asset_path.lstrip("/")).resolve()
        if candidate.exists() and candidate.is_file():
            return candidate

        parent = candidate.parent
        if not parent.exists():
            return None

        lowered = candidate.name.lower()
        for sibling in parent.iterdir():
            if sibling.is_file() and sibling.name.lower() == lowered:
                return sibling

        return None

    def _is_media_field(self, field_schema):
        field_type = str(field_schema.get("type") or "").lower()
        field_key = str(field_schema.get("key") or "").lower()
        if field_type in {"image", "video"}:
            return True
        return any(marker in field_key for marker in MEDIA_KEY_HINTS)

    def _copy_asset_to_media(self, site, section_key, field_key, asset_path):
        source = self._resolve_source_asset(asset_path)
        if source is None:
            return asset_path

        section_folder = SECTION_MEDIA_FOLDER_ALIAS.get(section_key, section_key)
        media_root = Path(settings.MEDIA_ROOT)
        target_dir = media_root / "sites" / site.slug / section_folder
        target_dir.mkdir(parents=True, exist_ok=True)

        target = target_dir / source.name
        if not target.exists() or source.stat().st_size != target.stat().st_size:
            shutil.copy2(source, target)

        relative_name = target.relative_to(media_root).as_posix()
        media_path = f"{settings.MEDIA_URL.rstrip('/')}/{relative_name}"

        mime_type = mimetypes.guess_type(source.name)[0] or ""
        file_type = "video" if mime_type.startswith("video/") else "image"

        MediaFile.objects.update_or_create(
            site=site,
            section_key=section_key,
            field_key=field_key,
            original_name=source.name,
            defaults={
                "file": relative_name,
                "title": source.stem,
                "alt": source.stem,
                "description": f"{section_key}:{field_key}",
                "file_type": file_type,
                "mime_type": mime_type,
                "size": source.stat().st_size,
            },
        )

        return media_path

    def _hydrate_section_media(self, site, section_key, schema, content):
        hydrated = deepcopy(content)

        def walk(fields, payload, path_prefix=""):
            if not isinstance(payload, dict):
                return

            for field in fields:
                if not isinstance(field, dict):
                    continue

                key = field.get("key")
                if not key or key not in payload:
                    continue

                value = payload.get(key)
                full_path = f"{path_prefix}.{key}" if path_prefix else str(key)

                if self._is_media_field(field) and isinstance(value, str) and value.startswith("/"):
                    payload[key] = self._copy_asset_to_media(site, section_key, full_path, value)
                    continue

                if field.get("type") == "repeater" and isinstance(value, list):
                    nested_fields = field.get("fields") or []
                    for idx, row in enumerate(value):
                        row_prefix = f"{full_path}.{idx}"
                        if isinstance(row, dict):
                            walk(nested_fields, row, row_prefix)

        walk(schema.get("fields") or [], hydrated)
        return hydrated

    def _upsert_sections(self, site):
        keep_keys = []
        for section_seed in SECTION_SEEDS:
            keep_keys.append(section_seed["key"])

            schema = deepcopy(section_seed["schema"])
            content = self._hydrate_section_media(site, section_seed["key"], schema, section_seed["content"])

            SectionSchema.objects.update_or_create(
                section_key=section_seed["key"],
                defaults={
                    "title": section_seed["title"],
                    "schema": schema,
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
                    "schema": schema,
                    "content": content,
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
