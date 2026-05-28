from datetime import datetime, time, timedelta

from django.db.models import Q, Sum
from django.utils import timezone

from analytics_app.models import Event
from leads.models import Lead
from tracker.models import Event as TrackerEvent
from tracker.models import Visit


def default_period_days(days: int = 14):
    now = timezone.localtime()
    date_to = now.date()
    date_from = date_to - timedelta(days=max(1, days) - 1)
    return date_from, date_to


def period_bounds(date_from, date_to, tz=None):
    tz = tz or timezone.get_current_timezone()
    from_dt = timezone.make_aware(datetime.combine(date_from, time.min), tz)
    to_dt = timezone.make_aware(datetime.combine(date_to, time.max), tz)
    return from_dt, to_dt


def get_metrics(client, date_from, date_to):
    from_dt, to_dt = period_bounds(date_from, date_to)

    visits_qs = Visit.objects.filter(
        site__token=client.api_key,
        started_at__gte=from_dt,
        started_at__lte=to_dt,
        is_bot=False,
    )
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
    leads_qs = Lead.objects.filter(
        client=client,
        created_at__gte=from_dt,
        created_at__lte=to_dt,
    )
    notified_qs = TrackerEvent.objects.filter(
        visit__site__token=client.api_key,
        type="form_submit",
        timestamp__gte=from_dt,
        timestamp__lte=to_dt,
        payload__telegram_notified=True,
    )

    visits = visits_qs.count()
    forms = forms_qs.count()
    leads = leads_qs.count()
    notifications_sent = notified_qs.count()
    total_time_on_site_seconds = int(time_on_page_qs.aggregate(total=Sum("duration_seconds")).get("total") or 0)
    time_on_page_events = time_on_page_qs.count()
    avg_visit_duration_seconds = round(total_time_on_site_seconds / time_on_page_events, 2) if time_on_page_events else 0

    with_id_filter = Q(visitor_id__isnull=False) & ~Q(visitor_id="")
    unique_with_visitor_id = visits_qs.filter(with_id_filter).values("visitor_id").distinct().count()
    unique_without_visitor_id = visits_qs.exclude(with_id_filter).values("session_id").distinct().count()
    unique_users = unique_with_visitor_id + unique_without_visitor_id

    # Count form submits as conversions for tracker-based funnels.
    conversion_events = max(forms, leads)
    conversion = round((conversion_events / visits) * 100, 2) if visits > 0 else 0.0

    return {
        "visits": visits,
        "unique_users": unique_users,
        "forms": forms,
        "leads": leads,
        "notifications_sent": notifications_sent,
        "conversion_events": conversion_events,
        "conversion": conversion,
        "total_time_on_site_seconds": total_time_on_site_seconds,
        "avg_visit_duration_seconds": avg_visit_duration_seconds,
        "time_on_page_events": time_on_page_events,
        "from_dt": from_dt,
        "to_dt": to_dt,
    }
