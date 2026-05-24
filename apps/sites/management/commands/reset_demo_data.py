from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import ClientProfile
from apps.mediafiles.models import MediaFile
from apps.sites.models import Site

DEMO_USERNAME = "test@test.ru"
DEMO_SITE_SLUG = "meditation"


class Command(BaseCommand):
    help = "Remove demo meditation data (site, media, profile, user)."

    @transaction.atomic
    def handle(self, *args, **options):
        sites = Site.objects.filter(slug=DEMO_SITE_SLUG)
        site_ids = list(sites.values_list("id", flat=True))

        media_files = MediaFile.objects.filter(site_id__in=site_ids)
        media_count = media_files.count()
        media_files.delete()

        sites_count = sites.count()
        sites.delete()

        user_model = get_user_model()
        user = user_model.objects.filter(username=DEMO_USERNAME).first()
        profile_count = 0
        user_count = 0

        if user is not None:
            profile_count = ClientProfile.objects.filter(user=user).count()
            ClientProfile.objects.filter(user=user).delete()
            user.delete()
            user_count = 1

        self.stdout.write(self.style.SUCCESS("reset_demo_data completed."))
        self.stdout.write(f"media_deleted={media_count}")
        self.stdout.write(f"sites_deleted={sites_count}")
        self.stdout.write(f"profiles_deleted={profile_count}")
        self.stdout.write(f"users_deleted={user_count}")

