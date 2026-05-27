import base64
import os
from copy import deepcopy

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ClientProfile
from apps.mediafiles.models import MediaFile
from apps.sites.models import SectionSchema, Site, SiteSection

DEMO_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+b9xQAAAAASUVORK5CYII="

SECTION_KEYS = ["hero", "about", "services", "meditations", "reviews", "contacts"]

BASE_SCHEMA = {
    "fields": [
        {"key": "title", "label": "Title", "type": "text", "required": False, "default": ""},
        {"key": "subtitle", "label": "Subtitle", "type": "text", "required": False, "default": ""},
        {"key": "description", "label": "Description", "type": "textarea", "required": False, "default": ""},
        {"key": "button_text", "label": "Button text", "type": "text", "required": False, "default": ""},
        {"key": "button_link", "label": "Button link", "type": "text", "required": False, "default": ""},
        {"key": "image", "label": "Image", "type": "image", "required": False, "default": ""},
        {"key": "order", "label": "Order", "type": "number", "required": False, "default": 0},
        {"key": "is_active", "label": "Is active", "type": "boolean", "required": False, "default": True},
    ]
}

SECTION_CONTENT = {
    "hero": {
        "title": "A Meditation",
        "subtitle": "Мягкие практики для концентрации и баланса",
        "description": "Добро пожаловать в пространство осознанности и восстановления.",
        "button_text": "Начать",
        "button_link": "#about",
    },
    "about": {
        "title": "О проекте",
        "subtitle": "Практика и поддержка",
        "description": "Секция знакомит с миссией, методами и проводниками практик.",
        "button_text": "Подробнее",
        "button_link": "#services",
    },
    "services": {
        "title": "Форматы практик",
        "subtitle": "Индивидуально и в группе",
        "description": "Подбор практик под текущий запрос и уровень подготовки.",
        "button_text": "Выбрать формат",
        "button_link": "#meditations",
    },
    "meditations": {
        "title": "Медитации",
        "subtitle": "Ежедневные и тематические",
        "description": "Набор guided-практик для фокуса, сна и внутренней устойчивости.",
        "button_text": "Смотреть каталог",
        "button_link": "#reviews",
    },
    "reviews": {
        "title": "Отзывы",
        "subtitle": "Реальные результаты",
        "description": "Участники отмечают снижение стресса и рост концентрации.",
        "button_text": "Оставить отзыв",
        "button_link": "#contacts",
    },
    "contacts": {
        "title": "Контакты",
        "subtitle": "Связаться с нами",
        "description": "Напишите нам для записи на практику или консультацию.",
        "button_text": "Написать",
        "button_link": "mailto:admin@test.ru",
    },
}


class Command(BaseCommand):
    help = "Seed complete demo data for yadro platform."

    @transaction.atomic
    def handle(self, *args, **options):
        admin_user = self._upsert_admin_user()
        self._upsert_profile(admin_user)

        site = self._upsert_site(admin_user)
        media = self._upsert_demo_media(site)
        self._upsert_sections(site, media)

        self.stdout.write(self.style.SUCCESS("seed_demo_data completed."))
        self.stdout.write(f"Admin login/email: {admin_user.email}")
        self.stdout.write("Admin password: configured via SUPERUSER_PASSWORD (default: testtest)")
        self.stdout.write(f"Site slug: {site.slug}")

    def _upsert_admin_user(self):
        user_model = get_user_model()
        email = os.getenv("SUPERUSER_EMAIL", "admin@test.ru")
        password = os.getenv("SUPERUSER_PASSWORD", "testtest")
        username = os.getenv("SUPERUSER_USERNAME", "admin")

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
        else:
            changed_fields = []
            if user.username != username:
                user.username = username
                changed_fields.append("username")
            if user.email != email:
                user.email = email
                changed_fields.append("email")
            if not user.is_staff:
                user.is_staff = True
                changed_fields.append("is_staff")
            if not user.is_superuser:
                user.is_superuser = True
                changed_fields.append("is_superuser")
            if not user.check_password(password):
                user.set_password(password)
                changed_fields.append("password")
            if changed_fields:
                user.save()

        return user

    def _upsert_profile(self, user):
        ClientProfile.objects.update_or_create(
            user=user,
            defaults={
                "display_name": "Администратор",
                "phone": "+7 900 000-00-00",
            },
        )

    def _upsert_site(self, owner):
        site_defaults = {
            "name": os.getenv("DEMO_SITE_NAME", "A Meditation"),
            "domain": os.getenv("DEMO_SITE_DOMAIN", "localhost"),
            "owner": owner,
            "is_active": True,
            "seo": {
                "title": "A Meditation",
                "description": "Demo сайт медитационной платформы",
                "keywords": ["meditation", "mindfulness", "wellness"],
            },
        }

        site, _ = Site.objects.update_or_create(
            slug=os.getenv("DEMO_SITE_SLUG", "a-meditation"),
            defaults=site_defaults,
        )
        return site

    def _upsert_demo_media(self, site):
        media = MediaFile.objects.filter(site=site, title="Demo Image").order_by("id").first()
        if media is None:
            media = MediaFile(site=site, title="Demo Image", alt="Demo", description="Demo seed image")
            media.file.save(
                "demo-image.png",
                ContentFile(base64.b64decode(DEMO_IMAGE_BASE64)),
                save=True,
            )
        elif not media.file:
            media.file.save(
                "demo-image.png",
                ContentFile(base64.b64decode(DEMO_IMAGE_BASE64)),
                save=True,
            )

        return media

    def _upsert_sections(self, site, media):
        image_url = media.file.url if media and media.file else ""

        for index, key in enumerate(SECTION_KEYS, start=1):
            schema = deepcopy(BASE_SCHEMA)

            SectionSchema.objects.update_or_create(
                section_key=key,
                defaults={
                    "title": key.title(),
                    "schema": schema,
                    "description": f"Demo schema for {key}",
                },
            )

            content = {
                **SECTION_CONTENT[key],
                "image": image_url,
                "order": index,
                "is_active": True,
            }

            SiteSection.objects.update_or_create(
                site=site,
                key=key,
                defaults={
                    "title": key.title(),
                    "section_type": key,
                    "order": index,
                    "is_active": True,
                    "schema": schema,
                    "content": content,
                    "component_key": f"{key}-section",
                    "settings": {
                        "theme": "light",
                        "container": "xl",
                        "animation": "fade-up",
                        "demo": True,
                    },
                    "seo": {
                        "title": f"A Meditation | {key.title()}",
                        "description": SECTION_CONTENT[key]["description"],
                    },
                },
            )
