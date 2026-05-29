import logging
from datetime import datetime

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClientUser
from analytics_app.models import Event
from analytics_app.serializers import PublicAnalyticsEventSerializer, PublicEventCreateSerializer
from analytics_app.services.ai_recommendations import build_ai_event_signals_payload
from analytics_app.services.device_stats import get_device_distribution
from analytics_app.services.local_recommendations import build_behavior_recommendations
from analytics_app.services.metrics import default_period_days, get_metrics, period_bounds
from analytics_app.services.report_builder import build_full_report
from clients.models import Client
from clients.permissions import HasValidApiKey
from tracker.models import Visit
from subscriptions.permissions import HasActiveSubscription

logger = logging.getLogger(__name__)


def get_conversion_ai_recommendations(*, client_id, date_from, date_to, force_refresh=False):
    """
    Compatibility wrapper for legacy mini_bitrix tests and integrations.
    Returns local behavior recommendations payload in the previous service shape.
    """
    client = Client.objects.get(id=client_id)
    report = build_full_report(client=client, date_from=date_from, date_to=date_to)
    summary = report["summary"]
    payload = {
        "visit_count": summary["visits"],
        "visitors_unique": summary["unique_users"],
        "form_submit_count": summary["forms"],
        "leads_count": summary["leads"],
        "conversion": summary["conversion"],
        "top_sources": [{"source": row["source"], "count": row["visits"]} for row in report["sources"][:5]],
        "latest_leads": report["leads"][:10],
        "source_performance": [
            {
                "source": row["source"],
                "visits": row["visits"],
                "leads": row["leads"],
                "conversion_pct": row["conversion_pct"],
            }
            for row in report["sources"]
        ],
        "conversion_by_pages": report["page_conversion"],
        "top_clicks": report["top_clicks"][:10],
    }
    recommendations = build_behavior_recommendations(payload)
    recommendations.setdefault("source", "local")
    recommendations.setdefault("success", True)
    return recommendations


def _default_period_days(days=14):
    return default_period_days(days=days)


def _parse_date(value, fallback):
    if not value:
        return fallback
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return fallback


def _period_range(request, days=14):
    default_from, default_to = _default_period_days(days=days)
    date_from = _parse_date(request.query_params.get("date_from"), default_from)
    date_to = _parse_date(request.query_params.get("date_to"), default_to)
    if date_from > date_to:
        date_from, date_to = date_to, date_from
    from_dt, to_dt = period_bounds(date_from, date_to, timezone.get_current_timezone())
    return date_from, date_to, from_dt, to_dt


def _build_ai_event_signals_payload(client, from_dt, to_dt):
    return build_ai_event_signals_payload(client=client, from_dt=from_dt, to_dt=to_dt)


def _build_summary_payload(client, from_dt, to_dt):
    report = build_full_report(client=client, date_from=from_dt.date(), date_to=to_dt.date())
    summary = report["summary"]
    daily_stats = report["daily_stats"]
    engagement = report.get("engagement") or {}

    visits_by_day = [{"day": row["day"], "count": row["visits"]} for row in daily_stats]
    unique_by_day = [{"day": row["day"], "count": row["unique_users"]} for row in daily_stats]
    forms_by_day = [{"day": row["day"], "count": row["forms"]} for row in daily_stats]
    leads_by_day = [{"day": row["day"], "count": row["leads"]} for row in daily_stats]

    source_performance = [
        {
            "source": row["source"],
            "visits": row["visits"],
            "leads": row["leads"],
            "conversion_pct": row["conversion_pct"],
        }
        for row in report["sources"]
    ]
    top_sources = [{"source": row["source"], "count": row["visits"]} for row in report["sources"][:5]]
    ai_event_signals = _build_ai_event_signals_payload(client=client, from_dt=from_dt, to_dt=to_dt)

    payload = {
        "visit_count": summary["visits"],
        "visitors_unique": summary["unique_users"],
        "form_submit_count": summary["forms"],
        "leads_count": summary["leads"],
        "notifications_sent_count": summary.get("notifications_sent", 0),
        "conversion": summary["conversion"],
        "visits_by_day": visits_by_day,
        "unique_by_day": unique_by_day,
        "forms_by_day": forms_by_day,
        "leads_by_day": leads_by_day,
        "latest_leads": report["leads"][:10],
        "avg_time_on_site": summary.get("avg_visit_duration_seconds", 0),
        "avg_visit_duration_seconds": summary.get("avg_visit_duration_seconds", 0),
        "total_time_on_site_seconds": summary.get("total_time_on_site_seconds", 0),
        "avg_session_duration": 0,
        "avg_scroll_depth": 0,
        "total_sessions": 0,
        "avg_page_views_per_session": 0,
        "top_sources": top_sources,
        "source_performance": source_performance,
        "conversion_by_pages": report["page_conversion"],
        "top_clicks": report["top_clicks"][:10],
        "total_clicks": sum(item["count"] for item in report["top_clicks"]),
        "engagement_pages": engagement.get("pages", []),
        "ai_event_signals": ai_event_signals,
    }
    payload["recommendations"] = build_behavior_recommendations(payload)
    return payload


class PublicEventCreateView(CreateAPIView):
    serializer_class = PublicEventCreateSerializer
    permission_classes = [HasValidApiKey]
    throttle_scope = "public_event"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["client"] = self.request.client
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            event = serializer.save()
        except Exception:
            logger.exception("Failed to create public event")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if event.event_type == Event.EventType.VISIT:
            logger.info(
                "Visit event stored: client_id=%s event_id=%s visitor_id=%s page_url=%s",
                request.client.id,
                event.id,
                event.visitor_id,
                event.page_url,
            )
        return Response({"id": event.id}, status=status.HTTP_201_CREATED)


class PublicVisitTrackView(APIView):
    permission_classes = [HasValidApiKey]
    throttle_scope = "public_event"

    def post(self, request, *args, **kwargs):
        payload = {
            "event_type": Event.EventType.VISIT,
            "page_url": request.data.get("page_url"),
            "element_id": request.data.get("element_id"),
            "visitor_id": request.data.get("visitor_id"),
        }
        serializer = PublicEventCreateSerializer(data=payload, context={"client": request.client})
        serializer.is_valid(raise_exception=True)
        try:
            event = serializer.save()
        except Exception:
            logger.exception("Failed to create visit event")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.info(
            "Visit track endpoint stored event: client_id=%s event_id=%s visitor_id=%s page_url=%s",
            request.client.id,
            event.id,
            event.visitor_id,
            event.page_url,
        )
        return Response({"id": event.id, "event_type": event.event_type}, status=status.HTTP_200_OK)


class PublicAnalyticsEventCreateView(CreateAPIView):
    serializer_class = PublicAnalyticsEventSerializer
    permission_classes = [HasValidApiKey]
    throttle_scope = "public_analytics_event"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["client"] = self.request.client
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = serializer.save()
        except Exception:
            logger.exception("Failed to create analytics event")
            return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.info(
            "analytics.event stored: client_id=%s type=%s visitor_id=%s session_id=%s result=%s",
            request.client.id,
            request.data.get("event_type"),
            request.data.get("visitor_id"),
            request.data.get("session_id"),
            result,
        )
        return Response(result, status=status.HTTP_201_CREATED)


class AnalyticsSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser, HasActiveSubscription]

    def get(self, request):
        client = request.client
        date_from, date_to, from_dt, to_dt = _period_range(request, days=14)
        payload = _build_summary_payload(client=client, from_dt=from_dt, to_dt=to_dt)
        payload["period"] = {"date_from": date_from, "date_to": date_to}
        logger.info(
            "analytics.summary: client_id=%s from=%s to=%s visits=%s unique=%s leads=%s",
            client.id,
            date_from,
            date_to,
            payload["visit_count"],
            payload["visitors_unique"],
            payload["leads_count"],
        )
        return Response(payload)


class AnalyticsAiRecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser, HasActiveSubscription]

    def get(self, request):
        date_from, date_to, from_dt, to_dt = _period_range(request, days=14)
        force_refresh = str(request.query_params.get("refresh", "")).lower() in {"1", "true", "yes", "on"}
        payload = get_conversion_ai_recommendations(
            client_id=request.client.id,
            date_from=date_from,
            date_to=date_to,
            force_refresh=force_refresh,
        )
        payload["period"] = {"date_from": date_from, "date_to": date_to}
        return Response(payload)


class AnalyticsOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser, HasActiveSubscription]

    def get(self, request):
        client = request.client
        date_from, date_to, _, _ = _period_range(request, days=14)
        metrics = get_metrics(client, date_from, date_to)
        response = {
            "period": {"date_from": date_from, "date_to": date_to},
            "visits_total": metrics["visits"],
            "visitors_unique": metrics["unique_users"],
            "forms_total": metrics["forms"],
            "leads_total": metrics["leads"],
            "notifications_sent_total": metrics["notifications_sent"],
            "conversion": metrics["conversion"],
            "total_time_on_site_seconds": metrics["total_time_on_site_seconds"],
            "avg_visit_duration_seconds": metrics["avg_visit_duration_seconds"],
        }
        logger.info(
            "analytics.overview: client_id=%s from=%s to=%s payload=%s",
            client.id,
            date_from,
            date_to,
            response,
        )
        return Response(response)


class AnalyticsEngagementView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser, HasActiveSubscription]

    def get(self, request):
        client = request.client
        date_from, date_to, _, _ = _period_range(request, days=14)
        report = build_full_report(client=client, date_from=date_from, date_to=date_to)
        engagement = report.get("engagement") or {}
        response = {
            "period": {"date_from": date_from, "date_to": date_to},
            "avg_time_on_page_seconds": engagement.get("avg_visit_duration_seconds", 0),
            "total_time_on_site_seconds": engagement.get("total_time_on_site_seconds", 0),
            "pages": engagement.get("pages", []),
        }
        logger.info(
            "analytics.engagement: client_id=%s from=%s to=%s total_time=%s pages=%s",
            client.id,
            date_from,
            date_to,
            response["total_time_on_site_seconds"],
            len(response["pages"]),
        )
        return Response(response)


class AnalyticsUniqueDailyView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser, HasActiveSubscription]

    def get(self, request):
        client = request.client
        date_from, date_to, from_dt, to_dt = _period_range(request, days=14)
        unique_filter = Q(visitor_id__isnull=False) & ~Q(visitor_id="")
        visits_qs = Visit.objects.filter(site__token=client.api_key, started_at__gte=from_dt, started_at__lte=to_dt, is_bot=False)
        rows_with_id = list(
            visits_qs.filter(unique_filter)
            .annotate(day=TruncDate("started_at"))
            .values("day")
            .annotate(count=Count("visitor_id", distinct=True))
            .order_by("day")
        )
        rows_without_id = list(
            visits_qs.exclude(unique_filter)
            .annotate(day=TruncDate("started_at"))
            .values("day")
            .annotate(count=Count("session_id", distinct=True))
            .order_by("day")
        )
        merged_rows = {}
        for row in rows_with_id + rows_without_id:
            day = row.get("day")
            merged_rows[day] = merged_rows.get(day, 0) + int(row.get("count") or 0)
        rows = [{"day": day, "count": count} for day, count in sorted(merged_rows.items())]

        metrics = get_metrics(client, date_from, date_to)
        total_unique = metrics["unique_users"]
        logger.info(
            "analytics.unique_daily: client_id=%s from=%s to=%s total_unique=%s days=%s",
            client.id,
            date_from,
            date_to,
            total_unique,
            len(rows),
        )
        return Response(
            {
                "period": {"date_from": date_from, "date_to": date_to},
                "total_unique": total_unique,
                "daily": rows,
            }
        )


class AnalyticsDevicesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClientUser, HasActiveSubscription]

    def get(self, request):
        client = request.client
        date_from, date_to, _, _ = _period_range(request, days=14)
        payload = get_device_distribution(client=client, date_from=date_from, date_to=date_to)
        response = {
            "period": {"date_from": date_from, "date_to": date_to},
            "devices": payload["devices"],
            "browsers": payload["browsers"],
            "os": payload["os"],
        }
        logger.info(
            "analytics.devices: client_id=%s from=%s to=%s payload=%s",
            client.id,
            date_from,
            date_to,
            response,
        )
        return Response(response)
