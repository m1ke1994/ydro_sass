from django.conf import settings
from django.utils.html import escape


def tracker_script_url() -> str:
    base_url = getattr(settings, "PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    return f"{base_url}/tracker.js"


def build_tracker_script_tag(api_key: str) -> str:
    return f'<script src="{escape(tracker_script_url())}" data-site-key="{escape(api_key)}"></script>'
