from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.sites.models import Site
from clients.models import Client


class Command(BaseCommand):
    help = "Create/update user and assign ownership for a site."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="User email")
        parser.add_argument("--password", required=True, help="User password")
        parser.add_argument("--username", required=False, help="Username (defaults to email)")
        parser.add_argument("--site-slug", required=False, help="Site slug")
        parser.add_argument("--site-name", required=False, help="Site name")

    @transaction.atomic
    def handle(self, *args, **options):
        email = str(options["email"]).strip().lower()
        password = str(options["password"]).strip()
        username = str(options.get("username") or email).strip()
        site_slug = str(options.get("site_slug") or "").strip()
        site_name = str(options.get("site_name") or "").strip()

        if not site_slug and not site_name:
            raise CommandError("Use --site-slug or --site-name to select the site.")

        user_model = get_user_model()
        user = user_model.objects.filter(email=email).first() or user_model.objects.filter(username=username).first()
        if user is None:
            user = user_model.objects.create_user(username=username, email=email, password=password)
        else:
            user.email = email
            user.username = username
            user.is_active = True
            if not user.check_password(password):
                user.set_password(password)
            user.save()

        site = None
        if site_slug:
            site = Site.objects.filter(slug=site_slug).first()
        if site is None and site_name:
            site = Site.objects.filter(name__iexact=site_name).first()
        if site is None:
            raise CommandError("Site not found by --site-slug/--site-name.")

        if site.owner_id != user.id:
            site.owner = user
            site.is_active = True
            site.save(update_fields=["owner", "is_active", "updated_at"])

        client, _ = Client.objects.get_or_create(
            owner=user,
            defaults={"name": site.name, "is_active": True},
        )
        updates = []
        if client.name != site.name:
            client.name = site.name
            updates.append("name")
        if not client.is_active:
            client.is_active = True
            updates.append("is_active")
        if updates:
            client.save(update_fields=updates)

        self.stdout.write(self.style.SUCCESS("assign_site_owner completed"))
        self.stdout.write(f"user_email={user.email}")
        self.stdout.write(f"site_id={site.id} site_slug={site.slug} site_name={site.name}")
        self.stdout.write(f"client_id={client.id}")
