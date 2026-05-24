from copy import deepcopy

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ClientProfile
from apps.sites.models import Site, SiteSection

USER_USERNAME = "meditation_owner"
USER_EMAIL = "meditation@example.com"
USER_PASSWORD = "test-test"

SITE_NAME = "Meditation"
SITE_SLUG = "meditation"
SITE_DOMAIN = "meditation.local"

SECTION_SEEDS = [
    {
        "name": "Hero",
        "slug": "hero",
        "section_type": "hero",
        "component_key": "hero-centered",
        "order": 1,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text", "required": True, "default": ""},
                {"key": "subtitle", "label": "Subtitle", "type": "textarea", "required": False, "default": ""},
                {"key": "button_text", "label": "Button text", "type": "text", "required": False, "default": ""},
                {
                    "key": "background_image",
                    "label": "Background image",
                    "type": "image",
                    "required": False,
                    "default": "",
                },
                {
                    "key": "background_video",
                    "label": "Background video",
                    "type": "video",
                    "required": False,
                    "default": "",
                },
            ]
        },
        "content": {
            "title": "Meditation studio",
            "subtitle": "Практики осознанности и мягкие трансформации.",
            "button_text": "Записаться",
            "background_image": "",
            "background_video": "",
        },
        "settings": {
            "theme": "dark",
            "spacing": "large",
            "animation": "fade-up",
            "background": "image",
            "container": "xl",
            "visible": True,
            "custom_classes": "",
        },
        "seo": {
            "title": "Meditation - Hero",
            "description": "Первый экран публичного сайта Meditation",
            "keywords": "meditation, hero",
        },
    },
    {
        "name": "About",
        "slug": "about",
        "section_type": "about",
        "component_key": "about-simple",
        "order": 2,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text", "required": True, "default": ""},
                {"key": "text", "label": "Text", "type": "textarea", "required": False, "default": ""},
            ]
        },
        "content": {
            "title": "О проекте",
            "text": "Meditation помогает настроиться на внутреннюю тишину и устойчивость.",
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
        "seo": {
            "title": "Meditation - About",
            "description": "Раздел о проекте Meditation",
            "keywords": "meditation, about",
        },
    },
    {
        "name": "Services",
        "slug": "services",
        "section_type": "services",
        "component_key": "services-grid",
        "order": 3,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text", "required": True, "default": ""},
                {
                    "key": "items",
                    "label": "Items",
                    "type": "repeater",
                    "required": False,
                    "default": [],
                    "fields": [
                        {"key": "title", "label": "Title", "type": "text", "required": True, "default": ""},
                        {
                            "key": "description",
                            "label": "Description",
                            "type": "textarea",
                            "required": False,
                            "default": "",
                        },
                        {"key": "price", "label": "Price", "type": "text", "required": False, "default": ""},
                    ],
                },
            ]
        },
        "content": {
            "title": "Услуги",
            "items": [
                {
                    "title": "Индивидуальная сессия",
                    "description": "Практика под ваш запрос.",
                    "price": "от 5000 ₽",
                },
                {
                    "title": "Групповая медитация",
                    "description": "Регулярные занятия в мини-группах.",
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
        "seo": {
            "title": "Meditation - Services",
            "description": "Раздел услуг сайта Meditation",
            "keywords": "meditation, services",
        },
    },
    {
        "name": "Gallery",
        "slug": "gallery",
        "section_type": "gallery",
        "component_key": "gallery-grid",
        "order": 4,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text", "required": False, "default": ""},
                {
                    "key": "items",
                    "label": "Items",
                    "type": "repeater",
                    "required": False,
                    "default": [],
                    "fields": [
                        {"key": "image", "label": "Image", "type": "image", "required": False, "default": ""},
                        {"key": "caption", "label": "Caption", "type": "text", "required": False, "default": ""},
                    ],
                },
            ]
        },
        "content": {"title": "Галерея", "items": []},
        "settings": {
            "theme": "light",
            "spacing": "medium",
            "animation": "fade-up",
            "background": "none",
            "container": "xl",
            "visible": True,
            "custom_classes": "",
        },
        "seo": {
            "title": "Meditation - Gallery",
            "description": "Галерея сайта Meditation",
            "keywords": "meditation, gallery",
        },
    },
    {
        "name": "Reviews",
        "slug": "reviews",
        "section_type": "reviews",
        "component_key": "reviews-slider",
        "order": 5,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text", "required": False, "default": ""},
                {
                    "key": "items",
                    "label": "Items",
                    "type": "repeater",
                    "required": False,
                    "default": [],
                    "fields": [
                        {"key": "author", "label": "Author", "type": "text", "required": False, "default": ""},
                        {"key": "text", "label": "Text", "type": "textarea", "required": False, "default": ""},
                        {"key": "rating", "label": "Rating", "type": "number", "required": False, "default": 5},
                    ],
                },
            ]
        },
        "content": {"title": "Отзывы", "items": []},
        "settings": {
            "theme": "light",
            "spacing": "medium",
            "animation": "fade-up",
            "background": "none",
            "container": "lg",
            "visible": True,
            "custom_classes": "",
        },
        "seo": {
            "title": "Meditation - Reviews",
            "description": "Отзывы клиентов Meditation",
            "keywords": "meditation, reviews",
        },
    },
    {
        "name": "Contacts",
        "slug": "contacts",
        "section_type": "contacts",
        "component_key": "contacts-simple",
        "order": 6,
        "schema": {
            "fields": [
                {"key": "title", "label": "Title", "type": "text", "required": False, "default": ""},
                {"key": "phone", "label": "Phone", "type": "text", "required": False, "default": ""},
                {"key": "email", "label": "Email", "type": "text", "required": False, "default": ""},
                {"key": "telegram", "label": "Telegram", "type": "text", "required": False, "default": ""},
                {"key": "address", "label": "Address", "type": "textarea", "required": False, "default": ""},
            ]
        },
        "content": {
            "title": "Контакты",
            "phone": "+7 (999) 000-00-00",
            "email": "hello@meditation.local",
            "telegram": "@meditation",
            "address": "Москва",
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
        "seo": {
            "title": "Meditation - Contacts",
            "description": "Контакты Meditation",
            "keywords": "meditation, contacts",
        },
    },
]


class Command(BaseCommand):
    help = "Import or update the demo Meditation site with owner-scoped sections."

    @transaction.atomic
    def handle(self, *args, **options):
        user = self._upsert_user()
        self._upsert_profile(user)
        site = self._upsert_site(user)
        deleted_sections = self._reset_site_sections(site)
        created_sections = self._create_sections(site)

        self.stdout.write(self.style.SUCCESS("import_static_site_demo completed."))
        self.stdout.write(f"user={user.username}")
        self.stdout.write(f"site={site.slug}")
        self.stdout.write(f"sections_deleted={deleted_sections}")
        self.stdout.write(f"sections_created={created_sections}")

    def _upsert_user(self):
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
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

        if changed:
            user.save(update_fields=["email", "password"])

        return user

    def _upsert_profile(self, user):
        profile, _ = ClientProfile.objects.get_or_create(
            user=user,
            defaults={"display_name": "Владелец сайта Meditation", "phone": ""},
        )

        changed = False
        if profile.display_name != "Владелец сайта Meditation":
            profile.display_name = "Владелец сайта Meditation"
            changed = True

        if profile.phone is None:
            profile.phone = ""
            changed = True

        if changed:
            profile.save(update_fields=["display_name", "phone", "updated_at"])

    def _upsert_site(self, user):
        site, _ = Site.objects.get_or_create(
            slug=SITE_SLUG,
            defaults={
                "name": SITE_NAME,
                "domain": SITE_DOMAIN,
                "owner": user,
                "is_active": True,
                "seo": {
                    "title": "Meditation",
                    "description": "Demo site for MVP flow",
                    "keywords": "meditation, mvp",
                },
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

        if changed:
            site.save()

        return site

    def _reset_site_sections(self, site):
        queryset = SiteSection.objects.filter(site=site)
        count = queryset.count()
        queryset.delete()
        return count

    def _create_sections(self, site):
        created = 0
        for seed in SECTION_SEEDS:
            SiteSection.objects.create(
                site=site,
                name=seed["name"],
                slug=seed["slug"],
                section_type=seed["section_type"],
                component_key=seed["component_key"],
                order=seed["order"],
                schema=deepcopy(seed["schema"]),
                content=deepcopy(seed["content"]),
                settings=deepcopy(seed["settings"]),
                seo=deepcopy(seed["seo"]),
                is_active=True,
            )
            created += 1
        return created
