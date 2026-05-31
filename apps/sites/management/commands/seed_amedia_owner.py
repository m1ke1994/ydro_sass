from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.sites.models import Site
from clients.models import Client

TARGET_EMAIL = "amedia@test.ru"
TARGET_PASSWORD = "test-test"
TARGET_USERNAME = "amedia@test.ru"
TARGET_SITE_NAME = "A Meditation / Амедиа"
TARGET_SITE_SLUG = "a-meditation"


class Command(BaseCommand):
    help = "Create or update amedia owner user and link the user to A Meditation site."

    @transaction.atomic
    def handle(self, *args, **options):
        user = self._upsert_user()
        client = self._upsert_client(user=user)
        site = self._upsert_site(user=user)
        reassigned_count = self._ensure_single_site_access(user=user, target_site=site)

        self.stdout.write(self.style.SUCCESS("seed_amedia_owner completed."))
        self.stdout.write(f"user_email={user.email}")
        self.stdout.write("password=test-test")
        self.stdout.write(f"client_id={client.id}")
        self.stdout.write(f"site_id={site.id} site_slug={site.slug} site_name={site.name}")
        self.stdout.write(f"reassigned_other_sites={reassigned_count}")

    def _upsert_user(self):
        user_model = get_user_model()
        user = user_model.objects.filter(email=TARGET_EMAIL).first()
        if user is None:
            user = user_model.objects.filter(username=TARGET_USERNAME).first()

        if user is None:
            user = user_model.objects.create_user(
                username=TARGET_USERNAME,
                email=TARGET_EMAIL,
                password=TARGET_PASSWORD,
            )

        changed = False
        if user.email != TARGET_EMAIL:
            user.email = TARGET_EMAIL
            changed = True
        if user.username != TARGET_USERNAME:
            user.username = TARGET_USERNAME
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if user.is_staff:
            user.is_staff = False
            changed = True
        if user.is_superuser:
            user.is_superuser = False
            changed = True
        if not user.check_password(TARGET_PASSWORD):
            user.set_password(TARGET_PASSWORD)
            changed = True

        if changed:
            user.save()
        return user

    def _upsert_client(self, user):
        client, _ = Client.objects.get_or_create(
            owner=user,
            defaults={
                "name": TARGET_SITE_NAME,
                "is_active": True,
            },
        )

        changed = False
        if client.name != TARGET_SITE_NAME:
            client.name = TARGET_SITE_NAME
            changed = True
        if not client.is_active:
            client.is_active = True
            changed = True

        if changed:
            client.save(update_fields=["name", "is_active"])
        return client

    def _upsert_site(self, user):
        site = Site.objects.filter(name__iexact=TARGET_SITE_NAME).first()
        if site is None:
            site = Site.objects.filter(slug=TARGET_SITE_SLUG).first()

        if site is None:
            site = Site.objects.create(
                name=TARGET_SITE_NAME,
                slug=TARGET_SITE_SLUG,
                domain="localhost",
                owner=user,
                is_active=True,
            )
            return site

        changed = False
        if site.name != TARGET_SITE_NAME:
            site.name = TARGET_SITE_NAME
            changed = True
        if site.owner_id != user.id:
            site.owner = user
            changed = True
        if not site.is_active:
            site.is_active = True
            changed = True

        if changed:
            site.save(update_fields=["name", "owner", "is_active", "updated_at"])
        return site

    def _ensure_single_site_access(self, user, target_site):
        other_sites = Site.objects.filter(owner=user).exclude(id=target_site.id)
        if not other_sites.exists():
            return 0

        fallback_owner = (
            get_user_model().objects.filter(is_superuser=True).exclude(id=user.id).order_by("id").first()
        )
        if fallback_owner is None:
            raise CommandError(
                "Cannot enforce single-site access for amedia owner: no fallback superuser found for reassign."
            )

        reassigned_count = other_sites.update(owner=fallback_owner)
        return int(reassigned_count)
