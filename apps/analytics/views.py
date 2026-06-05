from urllib.parse import urlparse

from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.sites.models import Site, SiteLead
from apps.sites.tracker_utils import build_tracker_script_tag
from tracker.models import Event as TrackerEvent
from tracker.models import PageView as TrackerPageView
from tracker.models import Site as TrackerSite
from tracker.models import Visit as TrackerVisit

from .models import PageView, TrackingEvent, Visit
from .serializers import PageViewSerializer, TrackEventSerializer, VisitEndSerializer, VisitStartSerializer


def _client_ip(request):
    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    return forwarded or (request.META.get("REMOTE_ADDR") or "")


def _pathname_from_url(value: str) -> str:
    try:
        parsed = urlparse(value or "")
        return parsed.path or "/"
    except Exception:
        return "/"


class TrackBaseAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_site(self, token: str) -> Site | None:
        return Site.objects.filter(api_key=token, is_active=True).first()

    def get_or_create_visit(self, site: Site, session_id: str, request, visitor_id: str = "", referrer: str = "") -> Visit:
        visit = (
            Visit.objects.filter(site=site, session_id=session_id)
            .order_by("-started_at")
            .first()
        )

        if visit:
            updates = []
            if visitor_id and visit.visitor_id != visitor_id:
                visit.visitor_id = visitor_id
                updates.append("visitor_id")
            if referrer and not visit.referrer:
                visit.referrer = referrer
                updates.append("referrer")
            if updates:
                visit.save(update_fields=updates)
            return visit

        return Visit.objects.create(
            site=site,
            visitor_id=visitor_id or "",
            session_id=session_id,
            ip_address=_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
            referrer=referrer or "",
        )


class VisitStartView(TrackBaseAPIView):
    def post(self, request):
        serializer = VisitStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        if site is None:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        visit = self.get_or_create_visit(
            site=site,
            session_id=serializer.validated_data["session_id"],
            request=request,
            visitor_id=serializer.validated_data.get("visitor_id") or "",
            referrer=serializer.validated_data.get("referrer") or "",
        )

        if visit.started_at != serializer.get_started_at():
            visit.started_at = serializer.get_started_at()
            visit.save(update_fields=["started_at"])

        return Response({"ok": True, "visit_id": visit.id}, status=status.HTTP_201_CREATED)


class PageViewCreateView(TrackBaseAPIView):
    def post(self, request):
        serializer = PageViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        if site is None:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        visit = self.get_or_create_visit(
            site=site,
            session_id=serializer.validated_data["session_id"],
            request=request,
            visitor_id=serializer.validated_data.get("visitor_id") or "",
        )

        pageview = PageView.objects.create(
            visit=visit,
            url=serializer.validated_data["url"],
            pathname=_pathname_from_url(serializer.validated_data["url"]),
            title=serializer.validated_data.get("title", ""),
            timestamp=serializer.get_timestamp(),
        )
        return Response({"ok": True, "pageview_id": pageview.id}, status=status.HTTP_201_CREATED)


class EventCreateView(TrackBaseAPIView):
    def post(self, request):
        serializer = TrackEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        if site is None:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        visit = self.get_or_create_visit(
            site=site,
            session_id=serializer.validated_data["session_id"],
            request=request,
            visitor_id=serializer.validated_data.get("visitor_id") or "",
        )

        event = TrackingEvent.objects.create(
            visit=visit,
            type=serializer.validated_data["type"],
            payload=serializer.validated_data.get("payload") or {},
            timestamp=serializer.get_timestamp(),
        )
        return Response({"ok": True, "event_id": event.id}, status=status.HTTP_201_CREATED)


class VisitEndView(TrackBaseAPIView):
    def post(self, request):
        serializer = VisitEndSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        if site is None:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

        visit = (
            Visit.objects.filter(site=site, session_id=serializer.validated_data["session_id"])
            .order_by("-started_at")
            .first()
        )
        if visit is None:
            visit = self.get_or_create_visit(
                site=site,
                session_id=serializer.validated_data["session_id"],
                request=request,
                visitor_id=serializer.validated_data.get("visitor_id") or "",
            )

        ended_at = serializer.get_ended_at()
        duration = serializer.validated_data.get("duration")
        if duration is None:
            duration = max(0, int((ended_at - visit.started_at).total_seconds()))
        visit.ended_at = ended_at
        visit.duration = duration
        visit.save(update_fields=["ended_at", "duration"])
        return Response({"ok": True, "visit_id": visit.id, "duration": visit.duration}, status=status.HTTP_200_OK)


class AdminSiteAnalyticsSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_site(self, request, site_id):
        queryset = Site.objects.all()
        if not request.user.is_superuser:
            queryset = queryset.filter(owner=request.user)
        return queryset.filter(id=site_id).first()

    def get(self, request, site_id: int):
        site = self._get_site(request, site_id)
        if site is None:
            return Response({"detail": "Site was not found."}, status=status.HTTP_404_NOT_FOUND)

        days = int(request.query_params.get("days", 14) or 14)
        days = min(max(days, 1), 365)
        from_dt = timezone.now() - timezone.timedelta(days=days)

        tracker_site = TrackerSite.objects.filter(token=site.api_key, is_active=True).first()
        if tracker_site is not None:
            visits = TrackerVisit.objects.filter(site=tracker_site, started_at__gte=from_dt, is_bot=False)
            pageviews = TrackerPageView.objects.filter(visit__site=tracker_site, timestamp__gte=from_dt)
            events = TrackerEvent.objects.filter(visit__site=tracker_site, timestamp__gte=from_dt)
            top_pages = list(
                pageviews.values("url")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )
            for page in top_pages:
                page["pathname"] = _pathname_from_url(page.pop("url", ""))
            sources = list(
                visits.values("referrer")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )
            devices = dict(visits.values_list("device_type").annotate(count=Count("id")))
            browsers = dict(visits.values_list("browser_family").annotate(count=Count("id")))
            os_rows = dict(visits.values_list("os").annotate(count=Count("id")))
        else:
            visits = Visit.objects.filter(site=site, started_at__gte=from_dt)
            pageviews = PageView.objects.filter(visit__site=site, timestamp__gte=from_dt)
            events = TrackingEvent.objects.filter(visit__site=site, timestamp__gte=from_dt)
            top_pages = list(
                pageviews.values("pathname")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )
            sources = list(
                visits.values("referrer")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )
            devices = {}
            browsers = {}
            os_rows = {}
        leads = SiteLead.objects.filter(site=site, created_at__gte=from_dt)

        visits_count = visits.count()
        unique_visitors = visits.exclude(visitor_id="").values("visitor_id").distinct().count()
        if unique_visitors == 0:
            unique_visitors = visits.values("session_id").distinct().count()
        leads_count = leads.count()
        conversion = round((leads_count / visits_count) * 100, 2) if visits_count else 0

        visits_daily = list(
            visits.annotate(day=TruncDate("started_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        leads_daily = list(
            leads.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        avg_duration = round(visits.aggregate(value=Avg("duration"))["value"] or 0)

        return Response(
            {
                "period_days": days,
                "visit_count": visits_count,
                "visitors_unique": unique_visitors,
                "pageviews_count": pageviews.count(),
                "events_count": events.count(),
                "leads_count": leads_count,
                "conversion": conversion,
                "visits_by_day": visits_daily,
                "leads_by_day": leads_daily,
                "top_pages": top_pages,
                "sources": sources,
                "devices": devices,
                "browsers": browsers,
                "os": os_rows,
                "avg_duration": avg_duration,
                "tracker": {
                    "api_key": site.api_key,
                    "script_tag": build_tracker_script_tag(site.api_key),
                },
            }
        )


def tracker_js_view(_request):
    script = r"""
(function() {
  const script = document.currentScript;
  const token = script && script.dataset ? (script.dataset.apiKey || '') : '';
  if (!token) return;
  const base = new URL(script.src).origin;
  const sessionKey = 'yadro_tracker_session';
  const visitorKey = 'yadro_tracker_visitor';
  const sessionId = sessionStorage.getItem(sessionKey) || (Date.now() + '-' + Math.random().toString(16).slice(2));
  const visitorId = localStorage.getItem(visitorKey) || (Date.now() + '-' + Math.random().toString(16).slice(2));
  sessionStorage.setItem(sessionKey, sessionId);
  localStorage.setItem(visitorKey, visitorId);
  const post = (path, payload) => fetch(base + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    keepalive: true
  }).catch(() => {});
  post('/api/track/visit-start/', { token, session_id: sessionId, visitor_id: visitorId, referrer: document.referrer || '' });
  post('/api/track/pageview/', { token, session_id: sessionId, visitor_id: visitorId, url: window.location.href, title: document.title || '' });
  document.addEventListener('click', function(e) {
    const node = e.target && e.target.closest ? e.target.closest('a,button,[role="button"]') : null;
    if (!node) return;
    post('/api/track/event/', { token, session_id: sessionId, visitor_id: visitorId, type: 'click', payload: { text: (node.innerText || '').trim().slice(0,120), id: node.id || '', class: node.className || '', path: window.location.pathname } });
  }, true);
  const started = Date.now();
  const onClose = () => {
    const duration = Math.max(0, Math.floor((Date.now() - started) / 1000));
    post('/api/track/event/', { token, session_id: sessionId, visitor_id: visitorId, type: 'time_on_page', payload: { path: window.location.pathname, duration_seconds: duration } });
    post('/api/track/visit-end/', { token, session_id: sessionId, visitor_id: visitorId, duration });
  };
  window.addEventListener('beforeunload', onClose);
  window.addEventListener('pagehide', onClose);
})();
"""
    return HttpResponse(script, content_type="application/javascript; charset=utf-8")
