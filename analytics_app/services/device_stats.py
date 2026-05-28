from django.db.models import Count

from analytics_app.services.metrics import period_bounds
from tracker.models import Visit


def get_device_distribution(client, date_from, date_to):
    from_dt, to_dt = period_bounds(date_from, date_to)
    visits_qs = Visit.objects.filter(site__token=client.api_key, started_at__gte=from_dt, started_at__lte=to_dt, is_bot=False)

    device_rows = (
        visits_qs.values("device_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    os_rows = (
        visits_qs.values("os")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    browser_rows = (
        visits_qs.values("browser_family")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    devices = {"mobile": 0, "desktop": 0, "tablet": 0}
    for row in device_rows:
        key = (row.get("device_type") or "").strip().lower()
        if key in devices:
            devices[key] = int(row.get("count") or 0)

    os_distribution = {}
    for row in os_rows:
        key = row.get("os") or "Unknown"
        os_distribution[key] = int(row.get("count") or 0)

    browsers = {}
    for row in browser_rows:
        key = row.get("browser_family") or "Unknown"
        browsers[key] = int(row.get("count") or 0)

    total_visits = visits_qs.count()

    return {
        "devices": devices,
        "browsers": browsers,
        "os": os_distribution,
        "total_visits": total_visits,
    }
