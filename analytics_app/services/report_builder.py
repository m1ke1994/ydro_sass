from urllib.parse import urlparse

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate

from analytics_app.models import ClickEvent, Event, PageView
from analytics_app.services.device_stats import get_device_distribution
from analytics_app.services.metrics import get_metrics
from leads.models import Lead
from leads.serializers import LeadSerializer
from tracker.models import Visit


def _count_map(queryset, date_field, value_field="id", distinct=False):
    rows = (
        queryset.annotate(day=TruncDate(date_field))
        .values("day")
        .annotate(count=Count(value_field, distinct=distinct))
        .order_by("day")
    )
    return {row["day"]: int(row["count"] or 0) for row in rows}


def build_full_report(client, date_from, date_to):
    metrics = get_metrics(client=client, date_from=date_from, date_to=date_to)
    from_dt = metrics["from_dt"]
    to_dt = metrics["to_dt"]

    visits_qs = Visit.objects.filter(site__token=client.api_key, started_at__gte=from_dt, started_at__lte=to_dt, is_bot=False)
    page_views_qs = PageView.objects.filter(client=client, created_at__gte=from_dt, created_at__lte=to_dt)
    forms_qs = Event.objects.filter(
        client=client,
        event_type=Event.EventType.FORM_SUBMIT,
        created_at__gte=from_dt,
        created_at__lte=to_dt,
    ).exclude(element_id="fetch_json")
    time_on_page_qs = Event.objects.filter(
        client=client,
        event_type=Event.EventType.TIME_ON_PAGE,
        created_at__gte=from_dt,
        created_at__lte=to_dt,
        duration_seconds__gt=0,
    )
    leads_qs = Lead.objects.filter(client=client, created_at__gte=from_dt, created_at__lte=to_dt)

    unique_filter = Q(visitor_id__isnull=False) & ~Q(visitor_id="")
    visits_by_day = _count_map(visits_qs, "started_at")
    forms_by_day = _count_map(forms_qs, "created_at")
    leads_by_day = _count_map(leads_qs, "created_at")
    unique_with_id_by_day = _count_map(visits_qs.filter(unique_filter), "started_at", value_field="visitor_id", distinct=True)
    unique_without_id_by_day = _count_map(visits_qs.exclude(unique_filter), "started_at", value_field="session_id", distinct=True)

    all_days = sorted(set(visits_by_day) | set(forms_by_day) | set(leads_by_day) | set(unique_with_id_by_day) | set(unique_without_id_by_day))
    daily_stats = []
    for day in all_days:
        visits = visits_by_day.get(day, 0)
        unique = unique_with_id_by_day.get(day, 0) + unique_without_id_by_day.get(day, 0)
        forms = forms_by_day.get(day, 0)
        leads = leads_by_day.get(day, 0)
        conversion_events = max(forms, leads)
        daily_stats.append(
            {
                "day": day,
                "visits": visits,
                "unique_users": unique,
                "forms": forms,
                "leads": leads,
                "conversion": round((conversion_events / visits) * 100, 2) if visits else 0.0,
            }
        )

    page_conversion = []
    page_rows = (
        page_views_qs.values("pathname")
        .annotate(visits=Count("id"), leads=Sum("attributed_leads"))
        .order_by("-leads", "-visits")
    )
    for row in page_rows:
        visits = int(row["visits"] or 0)
        leads = int(row["leads"] or 0)
        page_conversion.append(
            {
                "pathname": row.get("pathname") or "/",
                "visits": visits,
                "leads": leads,
                "conversion_pct": round((leads / visits) * 100, 2) if visits else 0.0,
            }
        )

    total_clicks = ClickEvent.objects.filter(client=client, created_at__gte=from_dt, created_at__lte=to_dt).count()
    top_clicks = []
    click_rows = (
        ClickEvent.objects.filter(client=client, created_at__gte=from_dt, created_at__lte=to_dt)
        .values("page_pathname", "element_text", "element_id", "element_class")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    for row in click_rows:
        top_clicks.append(
            {
                "page_pathname": row.get("page_pathname") or "/",
                "element_text": row.get("element_text") or "",
                "element_id": row.get("element_id") or "",
                "element_class": row.get("element_class") or "",
                "count": int(row.get("count") or 0),
                "percent_of_total": round((int(row.get("count") or 0) / total_clicks) * 100, 2) if total_clicks else 0.0,
            }
        )

    source_stats = {}
    for item in page_views_qs.values("utm_source", "referrer", "attributed_leads"):
        source = (item.get("utm_source") or "").strip().lower()
        if not source:
            referrer = (item.get("referrer") or "").strip()
            source = (urlparse(referrer).netloc or "direct").lower() if referrer else "direct"
        if source not in source_stats:
            source_stats[source] = {"visits": 0, "leads": 0}
        source_stats[source]["visits"] += 1
        source_stats[source]["leads"] += int(item.get("attributed_leads") or 0)

    total_source_visits = sum(row["visits"] for row in source_stats.values())
    sources = []
    for source, source_row in sorted(source_stats.items(), key=lambda pair: pair[1]["visits"], reverse=True):
        visits = source_row["visits"]
        leads = source_row["leads"]
        sources.append(
            {
                "source": source,
                "visits": visits,
                "leads": leads,
                "conversion_pct": round((leads / visits) * 100, 2) if visits else 0.0,
                "percent_of_total": round((visits / total_source_visits) * 100, 2) if total_source_visits else 0.0,
            }
        )

    latest_leads_qs = Lead.objects.filter(client=client, created_at__gte=from_dt, created_at__lte=to_dt).order_by("-created_at")[:50]
    leads = LeadSerializer(latest_leads_qs, many=True).data
    device_distribution = get_device_distribution(client=client, date_from=date_from, date_to=date_to)
    total_device_visits = max(device_distribution["total_visits"], 1)
    device_rows = [
        {
            "name": name,
            "count": int(count),
            "percent": round((int(count) / total_device_visits) * 100, 2),
        }
        for name, count in device_distribution["devices"].items()
    ]
    os_rows = [
        {
            "name": name,
            "count": int(count),
            "percent": round((int(count) / total_device_visits) * 100, 2),
        }
        for name, count in sorted(device_distribution["os"].items(), key=lambda pair: pair[1], reverse=True)
    ]
    browser_rows = [
        {
            "name": name,
            "count": int(count),
            "percent": round((int(count) / total_device_visits) * 100, 2),
        }
        for name, count in sorted(device_distribution["browsers"].items(), key=lambda pair: pair[1], reverse=True)
    ]

    total_time_on_site_seconds = int(time_on_page_qs.aggregate(total=Sum("duration_seconds")).get("total") or 0)
    time_on_page_events = time_on_page_qs.count()
    avg_visit_duration_seconds = round(total_time_on_site_seconds / time_on_page_events, 2) if time_on_page_events else 0
    engagement_map = {}
    for item in time_on_page_qs.values("page_url", "duration_seconds"):
        pathname = urlparse(item.get("page_url") or "").path or "/"
        if pathname not in engagement_map:
            engagement_map[pathname] = {"total_duration_seconds": 0, "visits_count": 0}
        engagement_map[pathname]["total_duration_seconds"] += int(item.get("duration_seconds") or 0)
        engagement_map[pathname]["visits_count"] += 1

    engagement_pages = []
    for pathname, row in engagement_map.items():
        visits_count = int(row["visits_count"] or 0)
        total_duration_seconds = int(row["total_duration_seconds"] or 0)
        engagement_pages.append(
            {
                "pathname": pathname or "/",
                "avg_duration_seconds": round(total_duration_seconds / visits_count, 2) if visits_count else 0,
                "total_duration_seconds": total_duration_seconds,
                "visits_count": visits_count,
            }
        )
    engagement_pages.sort(
        key=lambda row: (
            int(row.get("total_duration_seconds") or 0),
            int(row.get("visits_count") or 0),
        ),
        reverse=True,
    )

    return {
        "summary": {
            "visits": metrics["visits"],
            "unique_users": metrics["unique_users"],
            "forms": metrics["forms"],
            "leads": metrics["leads"],
            "notifications_sent": metrics["notifications_sent"],
            "conversion": metrics["conversion"],
            "total_time_on_site_seconds": total_time_on_site_seconds,
            "avg_visit_duration_seconds": avg_visit_duration_seconds,
        },
        "daily_stats": daily_stats,
        "top_clicks": top_clicks,
        "page_conversion": page_conversion,
        "sources": sources,
        "leads": leads,
        "engagement": {
            "total_time_on_site_seconds": total_time_on_site_seconds,
            "avg_visit_duration_seconds": avg_visit_duration_seconds,
            "pages": engagement_pages,
        },
        "devices_distribution": {
            "devices": device_rows,
            "os": os_rows,
            "browsers": browser_rows,
            "raw": {
                "devices": device_distribution["devices"],
                "os": device_distribution["os"],
                "browsers": device_distribution["browsers"],
            },
        },
        "period": {"date_from": date_from, "date_to": date_to},
    }
