import logging
from urllib.parse import parse_qs, urljoin, urlparse

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from user_agents import parse as parse_user_agent

from analytics_app.models import ClickEvent as AnalyticsClickEvent
from analytics_app.models import Event as AnalyticsEvent
from analytics_app.models import PageView as AnalyticsPageView
from apps.sites.models import Site as CoreSite
from clients.models import Client
from tracker.models import Event, PageView, Site, Visit
from tracker.serializers import (
    PageViewSerializer,
    TrackEventSerializer,
    VisitEndSerializer,
    VisitStartSerializer,
)
from tracker.services.bot_filter import detect_bot_visit

logger = logging.getLogger(__name__)


def _client_ip(request):
    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    return forwarded or request.META.get("REMOTE_ADDR")


def _extract_visit_context(request):
    user_agent_string = request.META.get("HTTP_USER_AGENT", "") or ""
    ip = _client_ip(request)
    try:
        ua = parse_user_agent(user_agent_string)
        if ua.is_mobile:
            device_type = "mobile"
        elif ua.is_tablet:
            device_type = "tablet"
        else:
            device_type = "desktop"
        os_family = ua.os.family or None
        browser_name = ua.browser.family or None
        browser_family = ua.browser.family or None
        is_ios_browser = (ua.os.family or "") == "iOS"
    except Exception:
        device_type = None
        os_family = None
        browser_name = None
        browser_family = None
        is_ios_browser = False

    return {
        "ip_address": ip,
        "user_agent": user_agent_string,
        "device_type": device_type,
        "os": os_family,
        "browser": browser_name,
        "browser_family": browser_family,
        "is_ios_browser": is_ios_browser,
    }


def _site_by_token(token: str):
    site = Site.objects.filter(token=token, is_active=True).first()
    if site:
        return site

    # Compatibility path: promote legacy client api_key to Site token once.
    legacy_client = Client.objects.filter(api_key=token, is_active=True).first()
    if legacy_client:
        return Site.objects.create(token=token, domain=legacy_client.name, is_active=True)

    # Yadro site compatibility path: use public site api_key as tracker token.
    core_site = CoreSite.objects.filter(api_key=token, is_active=True).first()
    if core_site:
        tracker_site = Site.objects.filter(token=token).first()
        domain_value = core_site.domain or core_site.slug or core_site.name
        if tracker_site is None:
            return Site.objects.create(token=token, domain=domain_value, is_active=True)

        update_fields = []
        if not tracker_site.is_active:
            tracker_site.is_active = True
            update_fields.append("is_active")
        if domain_value and tracker_site.domain != domain_value:
            tracker_site.domain = domain_value
            update_fields.append("domain")
        if update_fields:
            tracker_site.save(update_fields=update_fields)
        return tracker_site
    return None


def _client_by_token(token: str):
    client = Client.objects.filter(api_key=token, is_active=True).first()
    if client is not None:
        return client

    core_site = CoreSite.objects.select_related("owner").filter(api_key=token, is_active=True).first()
    if core_site is None:
        return None

    owner = getattr(core_site, "owner", None)
    site_client = getattr(owner, "client", None)
    if site_client is not None and site_client.is_active:
        return site_client
    return None


def _safe_url(value: str, fallback: str = "https://tracker.local/") -> str:
    raw = (value or "").strip()
    if not raw:
        return fallback
    parsed = urlparse(raw)
    if parsed.scheme and parsed.netloc:
        return raw
    return fallback


def _query_param(query_dict, key):
    value = (query_dict.get(key) or [""])[0]
    value = (value or "").strip()
    return value or None


def _pageview_payload_from_url(url: str):
    parsed = urlparse(url)
    query = parse_qs(parsed.query or "")
    return {
        "pathname": parsed.path or "/",
        "query_string": parsed.query or None,
        "utm_source": _query_param(query, "utm_source"),
        "utm_medium": _query_param(query, "utm_medium"),
        "utm_campaign": _query_param(query, "utm_campaign"),
        "utm_term": _query_param(query, "utm_term"),
        "utm_content": _query_param(query, "utm_content"),
    }


def _compose_page_url(page: str, origin: str, fallback: str = "https://tracker.local/") -> str:
    raw_page = (page or "").strip()
    if raw_page:
        parsed = urlparse(raw_page)
        if parsed.scheme and parsed.netloc:
            return raw_page
    base = _safe_url(origin, fallback=fallback)
    if not raw_page:
        return base
    return urljoin(base, raw_page)


class TrackBaseAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_site(self, token):
        site = _site_by_token(token)
        if not site:
            logger.warning("Track request rejected: invalid token token=%s", (token[:6] + "***") if token else "***")
            raise PermissionDenied("Invalid token.")
        return site

    def get_or_create_visit(self, site, session_id, request, started_at=None, referrer="", visitor_id="", tracked_url=None, bot_source=""):
        context = _extract_visit_context(request)
        bot_check = detect_bot_visit(
            site_id=site.id,
            ip_address=context.get("ip_address"),
            user_agent=context.get("user_agent"),
            tracked_url=tracked_url,
        )
        if bot_check.is_bot:
            logger.debug(
                "track.bot_detected source=%s site_id=%s session_id=%s ip=%s user_agent=%s reasons=%s request_count_5s=%s unique_urls_10s=%s url=%s",
                bot_source or "unknown",
                site.id,
                session_id,
                context.get("ip_address"),
                (context.get("user_agent") or "")[:512],
                ",".join(bot_check.reasons),
                bot_check.request_count_5s,
                bot_check.unique_urls_10s,
                (tracked_url or "")[:512],
            )
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
            for field_name, field_value in context.items():
                if field_value is None:
                    continue
                current = getattr(visit, field_name)
                if current != field_value:
                    setattr(visit, field_name, field_value)
                    updates.append(field_name)
            if bot_check.is_bot and not visit.is_bot:
                visit.is_bot = True
                updates.append("is_bot")
            if updates:
                visit.save(update_fields=updates)
            return visit
        return Visit.objects.create(
            site=site,
            visitor_id=visitor_id or "",
            session_id=session_id,
            ip_address=context["ip_address"],
            is_bot=bot_check.is_bot,
            user_agent=context["user_agent"],
            device_type=context["device_type"],
            os=context["os"],
            browser=context["browser"],
            browser_family=context["browser_family"],
            is_ios_browser=context["is_ios_browser"],
            referrer=referrer or "",
            started_at=started_at or timezone.now(),
        )

    def handle_exception(self, exc):
        logger.exception("track.api exception path=%s method=%s", self.request.path, self.request.method)
        return super().handle_exception(exc)


class VisitStartView(TrackBaseAPIView):
    def post(self, request):
        logger.info("track.visit_start request origin=%s body=%s", request.headers.get("Origin"), dict(request.data))
        serializer = VisitStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        visit = self.get_or_create_visit(
            site=site,
            session_id=serializer.validated_data["session_id"],
            request=request,
            started_at=serializer.get_started_at(),
            referrer=serializer.validated_data.get("referrer") or "",
            visitor_id=serializer.validated_data.get("visitor_id") or "",
            tracked_url=(request.data.get("url") or ""),
            bot_source="visit_start",
        )
        client = _client_by_token(serializer.validated_data["token"])
        if client:
            try:
                event_url = _safe_url(
                    request.data.get("url") or request.headers.get("Origin") or serializer.validated_data.get("referrer")
                )
                AnalyticsEvent.objects.create(
                    client=client,
                    visitor_id=serializer.validated_data.get("visitor_id") or "",
                    event_type=AnalyticsEvent.EventType.VISIT,
                    page_url=event_url,
                )
            except Exception:
                logger.exception(
                    "track.visit_start failed to mirror analytics event site_id=%s client_id=%s",
                    site.id,
                    client.id,
                )
        logger.info(
            "track.visit_start created visit_id=%s site_id=%s visitor_id=%s session_id=%s",
            visit.id,
            site.id,
            visit.visitor_id,
            visit.session_id,
        )
        return Response({"ok": True, "visit_id": visit.id}, status=status.HTTP_201_CREATED)


class PageViewCreateView(TrackBaseAPIView):
    def post(self, request):
        logger.info("track.pageview request origin=%s body=%s", request.headers.get("Origin"), dict(request.data))
        serializer = PageViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        visit = self.get_or_create_visit(
            site,
            serializer.validated_data["session_id"],
            request,
            visitor_id=serializer.validated_data.get("visitor_id") or "",
            tracked_url=serializer.validated_data["url"],
            bot_source="pageview",
        )
        pageview = PageView.objects.create(
            visit=visit,
            url=serializer.validated_data["url"],
            title=serializer.validated_data.get("title", ""),
            timestamp=serializer.get_timestamp(),
        )
        client = _client_by_token(serializer.validated_data["token"])
        if client:
            try:
                safe_url = _safe_url(serializer.validated_data["url"])
                payload = _pageview_payload_from_url(safe_url)
                AnalyticsPageView.objects.create(
                    client=client,
                    visitor_id=serializer.validated_data.get("visitor_id") or "",
                    session_id=serializer.validated_data["session_id"],
                    url=safe_url,
                    pathname=payload["pathname"],
                    query_string=payload["query_string"],
                    referrer=visit.referrer or None,
                    utm_source=payload["utm_source"],
                    utm_medium=payload["utm_medium"],
                    utm_campaign=payload["utm_campaign"],
                    utm_term=payload["utm_term"],
                    utm_content=payload["utm_content"],
                )
            except Exception:
                logger.exception(
                    "track.pageview failed to mirror analytics pageview visit_id=%s client_id=%s",
                    visit.id,
                    client.id,
                )
        logger.info(
            "track.pageview created pageview_id=%s visit_id=%s visitor_id=%s session_id=%s",
            pageview.id,
            visit.id,
            visit.visitor_id,
            visit.session_id,
        )
        return Response({"ok": True, "pageview_id": pageview.id}, status=status.HTTP_201_CREATED)


class EventCreateView(TrackBaseAPIView):
    def post(self, request):
        logger.info("track.event request origin=%s body=%s", request.headers.get("Origin"), dict(request.data))
        serializer = TrackEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        payload = serializer.validated_data.get("payload") or {}
        visit = self.get_or_create_visit(
            site,
            serializer.validated_data["session_id"],
            request,
            visitor_id=serializer.validated_data.get("visitor_id") or "",
            tracked_url=(payload.get("url") or payload.get("page_url") or ""),
            bot_source="event",
        )
        event_type = serializer.validated_data["type"]
        duration_seconds = 0
        if event_type == "time_on_page":
            try:
                duration_seconds = int(payload.get("duration_seconds") or 0)
            except (TypeError, ValueError):
                duration_seconds = 0
            if duration_seconds <= 0:
                logger.info(
                    "track.event ignored invalid time_on_page duration visit_id=%s session_id=%s payload=%s",
                    visit.id,
                    serializer.validated_data["session_id"],
                    payload,
                )
                return Response({"ok": True, "ignored": True}, status=status.HTTP_200_OK)

        event = Event.objects.create(
            visit=visit,
            type=event_type,
            payload=payload,
            timestamp=serializer.get_timestamp(),
        )
        client = _client_by_token(serializer.validated_data["token"])
        if client:
            try:
                if event_type == "form_submit":
                    latest_page_view = (
                        AnalyticsPageView.objects.filter(
                            client=client,
                            session_id=serializer.validated_data["session_id"],
                        )
                        .order_by("-created_at")
                        .first()
                    )
                    AnalyticsEvent.objects.create(
                        client=client,
                        visitor_id=serializer.validated_data.get("visitor_id") or "",
                        event_type=AnalyticsEvent.EventType.FORM_SUBMIT,
                        element_id=(payload.get("id") or "")[:255],
                        page_url=_safe_url(
                            payload.get("url")
                            or payload.get("page_url")
                            or (latest_page_view.url if latest_page_view else "")
                            or request.headers.get("Origin")
                        ),
                    )
                elif event_type == "click":
                    latest_page_view = (
                        AnalyticsPageView.objects.filter(
                            client=client,
                            session_id=serializer.validated_data["session_id"],
                        )
                        .order_by("-created_at")
                        .first()
                    )
                    AnalyticsClickEvent.objects.create(
                        client=client,
                        visitor_id=serializer.validated_data.get("visitor_id") or "",
                        session_id=serializer.validated_data["session_id"],
                        page_pathname=((payload.get("path") or "").strip() or (latest_page_view.pathname if latest_page_view else "/")),
                        element_text=((payload.get("text") or "")[:100]),
                        element_id=((payload.get("id") or "")[:255]),
                        element_class=((payload.get("class") or "")[:255]),
                    )
                elif event_type == "time_on_page":
                    latest_page_view = (
                        AnalyticsPageView.objects.filter(
                            client=client,
                            session_id=serializer.validated_data["session_id"],
                        )
                        .order_by("-created_at")
                        .first()
                    )
                    page = ((payload.get("page") or payload.get("path") or "").strip() or "/")
                    page_url = _compose_page_url(
                        page=page,
                        origin=(
                            payload.get("url")
                            or payload.get("page_url")
                            or (latest_page_view.url if latest_page_view else "")
                            or request.headers.get("Origin")
                        ),
                    )
                    AnalyticsEvent.objects.create(
                        client=client,
                        visitor_id=serializer.validated_data.get("visitor_id") or "",
                        event_type=AnalyticsEvent.EventType.TIME_ON_PAGE,
                        element_id=page[:255],
                        page_url=page_url,
                        duration_seconds=duration_seconds,
                    )
                elif event_type == "scroll_depth":
                    latest_page_view = (
                        AnalyticsPageView.objects.filter(
                            client=client,
                            session_id=serializer.validated_data["session_id"],
                        )
                        .order_by("-created_at")
                        .first()
                    )
                    depth_value = 0
                    try:
                        depth_value = int(payload.get("depth") or payload.get("current_depth") or 0)
                    except (TypeError, ValueError):
                        depth_value = 0
                    depth_value = max(0, min(depth_value, 100))
                    if latest_page_view and depth_value > latest_page_view.max_scroll_depth:
                        latest_page_view.max_scroll_depth = depth_value
                        latest_page_view.save(update_fields=["max_scroll_depth", "updated_at"])
            except Exception:
                logger.exception(
                    "track.event failed to mirror analytics event type=%s visit_id=%s client_id=%s",
                    serializer.validated_data["type"],
                    visit.id,
                    client.id,
                )

        logger.info(
            "track.event created event_id=%s visit_id=%s type=%s visitor_id=%s session_id=%s",
            event.id,
            visit.id,
            event.type,
            visit.visitor_id,
            visit.session_id,
        )
        return Response({"ok": True, "event_id": event.id}, status=status.HTTP_201_CREATED)


class VisitEndView(TrackBaseAPIView):
    def post(self, request):
        logger.info("track.visit_end request origin=%s body=%s", request.headers.get("Origin"), dict(request.data))
        serializer = VisitEndSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        site = self.get_site(serializer.validated_data["token"])
        visit = (
            Visit.objects.filter(site=site, session_id=serializer.validated_data["session_id"])
            .order_by("-started_at")
            .first()
        )
        if not visit:
            visit = self.get_or_create_visit(
                site,
                serializer.validated_data["session_id"],
                request,
                visitor_id=serializer.validated_data.get("visitor_id") or "",
            )
        elif (serializer.validated_data.get("visitor_id") or "") and visit.visitor_id != serializer.validated_data.get("visitor_id"):
            visit.visitor_id = serializer.validated_data.get("visitor_id") or ""
            visit.save(update_fields=["visitor_id"])

        ended_at = serializer.get_ended_at()
        duration = serializer.validated_data.get("duration")
        if duration is None:
            duration = max(0, int((ended_at - visit.started_at).total_seconds()))
        visit.ended_at = ended_at
        visit.duration = duration
        visit.save(update_fields=["ended_at", "duration"])
        logger.info("track.visit_end updated visit_id=%s duration=%s", visit.id, visit.duration)
        return Response({"ok": True, "visit_id": visit.id, "duration": visit.duration}, status=status.HTTP_200_OK)


class TrackStatsView(TrackBaseAPIView):
    def get(self, request):
        token = request.query_params.get("token", "")
        if not token:
            return Response(
                {
                    "sites_total": Site.objects.count(),
                    "visits_total": Visit.objects.filter(is_bot=False).count(),
                    "pageviews_total": PageView.objects.count(),
                    "events_total": Event.objects.count(),
                },
                status=status.HTTP_200_OK,
            )

        site = self.get_site(token)
        visits = Visit.objects.filter(site=site, is_bot=False)
        return Response(
            {
                "site_id": site.id,
                "site_domain": site.domain,
                "visits_total": visits.count(),
                "pageviews_total": PageView.objects.filter(visit__site=site).count(),
                "events_total": Event.objects.filter(visit__site=site).count(),
            },
            status=status.HTTP_200_OK,
        )
