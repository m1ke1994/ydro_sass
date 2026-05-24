from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deprecated. Use seed_meditation_site instead."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("import_static_site_demo is deprecated. Running seed_meditation_site..."))
        call_command("seed_meditation_site")
