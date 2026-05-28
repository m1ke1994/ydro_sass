from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import Any
from urllib.parse import urlparse

from analytics_app.models import PageView as AnalyticsPageView
from tracker.models import Event as TrackerEvent
from tracker.models import Visit

SCROLL_DEPTH_THRESHOLDS = (25, 50, 75, 100)
DEVICE_CATEGORIES = ("desktop", "mobile", "tablet", "unknown")
SOURCE_CATEGORIES = ("organic", "paid", "social", "direct", "referral", "email", "unknown")

FORM_STAGE_ALIASES = {
    "form_visible": ("form_visible", "form_view"),
    "form_started": ("form_started", "form_start"),
    "form_first_field_completed": ("form_first_field_completed", "form_first_field_filled"),
    "form_submit_attempt": ("form_submit_attempt",),
    "form_submit_success": ("form_submit_success",),
    "form_submit_error": ("form_submit_error",),
}

FIELD_EVENT_TYPES = (
    "field_focus",
    "field_blur",
    "field_input_started",
    "field_completed",
    "field_error",
    "field_revisit",
)

CTA_EVENT_TYPES = (
    "cta_visible",
    "cta_click",
    "cta_target_reached",
    "cta_converted",
)

SECTION_EVENT_TYPES = (
    "section_visible",
    "section_view",
    "section_time_spent",
    "section_exit_after_view",
    "section_interaction_after_view",
    "section_conversion_after_view",
)

MICRO_CONVERSION_EVENT_TYPES = (
    "phone_click",
    "email_click",
    "telegram_click",
    "whatsapp_click",
    "map_open",
    "faq_expand",
    "gallery_open",
    "video_play",
    "tariff_expand",
    "contact_copy",
)

MICRO_CONVERSION_LABELS = {
    "phone_click": "Клик по телефону",
    "email_click": "Клик по email",
    "telegram_click": "Переход в Telegram",
    "whatsapp_click": "Переход в WhatsApp",
    "map_open": "Открыли карту",
    "faq_expand": "Открыли ответ в FAQ",
    "gallery_open": "Открыли галерею",
    "video_play": "Запустили видео",
    "tariff_expand": "Открыли тариф",
    "contact_copy": "Скопировали контакт",
}

AI_EVENT_TYPES: tuple[str, ...] = tuple(
    sorted(
        set(
            {"scroll_depth"}
            | set(CTA_EVENT_TYPES)
            | set(SECTION_EVENT_TYPES)
            | set(FIELD_EVENT_TYPES)
            | set(MICRO_CONVERSION_EVENT_TYPES)
            | {item for values in FORM_STAGE_ALIASES.values() for item in values}
        )
    )
)

SEARCH_HINTS = ("google", "bing", "yandex", "duckduckgo", "yahoo", "baidu")
SOCIAL_HINTS = (
    "facebook",
    "instagram",
    "vk",
    "vkontakte",
    "ok.ru",
    "tiktok",
    "linkedin",
    "pinterest",
    "youtube",
    "telegram",
    "twitter",
    "x.com",
)
PAID_HINTS = ("cpc", "ppc", "paid", "display", "banner", "retarget", "ad", "ads")
EMAIL_HINTS = ("email", "mail", "newsletter")


def _normalize_event_type(event_type: str) -> str:
    normalized = (event_type or "").strip().lower()
    if not normalized:
        return ""
    for canonical, aliases in FORM_STAGE_ALIASES.items():
        if normalized in aliases:
            return canonical
    if normalized == "section_view":
        return "section_visible"
    return normalized


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _pct(current: float, base: float) -> float:
    if base <= 0:
        return 0.0
    return round((float(current) / float(base)) * 100.0, 2)


def _normalize_scroll_depth(depth: int) -> int:
    return max(0, min(100, _safe_int(depth, default=0)))


def _normalize_scroll_threshold(depth: int) -> int:
    for threshold in reversed(SCROLL_DEPTH_THRESHOLDS):
        if depth >= threshold:
            return threshold
    return 0


def _normalize_device_type(device_type: str | None) -> str:
    normalized = (device_type or "").strip().lower()
    if normalized in ("desktop", "mobile", "tablet"):
        return normalized
    return "unknown"


def _normalize_source_category(
    *,
    utm_source: str | None = None,
    utm_medium: str | None = None,
    referrer: str | None = None,
    source_raw: str | None = None,
) -> str:
    source = (utm_source or source_raw or "").strip().lower()
    medium = (utm_medium or "").strip().lower()
    ref = (referrer or "").strip().lower()

    ref_host = ""
    if ref:
        try:
            ref_host = (urlparse(ref).netloc or "").strip().lower()
        except Exception:
            ref_host = ""

    if source in ("direct", "(direct)"):
        source = ""
    if medium in ("none", "(none)"):
        medium = ""

    if any(item in medium for item in EMAIL_HINTS) or any(item in source for item in EMAIL_HINTS):
        return "email"

    if any(item in medium for item in PAID_HINTS) or any(item in source for item in ("adwords", "gads", "vk_ads", "mytarget", "facebook_ads", "instagram_ads")):
        return "paid"

    social_probe = " ".join((source, medium, ref_host))
    if any(item in social_probe for item in SOCIAL_HINTS):
        return "social"

    if "organic" in medium or any(item in " ".join((source, ref_host)) for item in SEARCH_HINTS):
        return "organic"

    if medium == "referral":
        return "referral"

    if not source and not medium:
        if not ref_host:
            return "direct"
        return "referral"

    return "unknown"


def _user_key(visitor_id: str | None, session_id: str | None) -> str:
    visitor = (visitor_id or "").strip()
    if visitor:
        return f"visitor:{visitor}"
    session = (session_id or "").strip()
    if session:
        return f"session:{session}"
    return ""


def _path_from_page_url(page_url: str | None, fallback_path: str | None = None) -> str:
    if page_url:
        try:
            parsed = urlparse(page_url)
            if parsed.path:
                return parsed.path
        except Exception:
            pass
    if fallback_path:
        return str(fallback_path).strip() or "/"
    return "/"


def _empty_segment_stats() -> dict[str, Any]:
    return {
        "sessions": set(),
        "users": set(),
        "scroll_events": 0,
        "scroll_by_session": {},
        "cta_visible": 0,
        "cta_clicks": 0,
        "form_start_users": set(),
        "form_submit_success_users": set(),
    }


def _build_session_source_map(client, from_dt, to_dt) -> dict[str, dict[str, Any]]:
    rows = (
        AnalyticsPageView.objects.filter(client=client, created_at__gte=from_dt, created_at__lte=to_dt)
        .values("session_id", "utm_source", "utm_medium", "utm_campaign", "referrer", "created_at")
        .order_by("session_id", "created_at")
    )

    session_source_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        session_id = (row.get("session_id") or "").strip()
        if not session_id or session_id in session_source_map:
            continue
        category = _normalize_source_category(
            utm_source=row.get("utm_source"),
            utm_medium=row.get("utm_medium"),
            referrer=row.get("referrer"),
        )
        session_source_map[session_id] = {
            "category": category,
            "source_raw": (row.get("utm_source") or "").strip().lower() or None,
            "utm_source": row.get("utm_source") or None,
            "utm_medium": row.get("utm_medium") or None,
            "utm_campaign": row.get("utm_campaign") or None,
        }
    return session_source_map


def _resolve_source_category(
    payload: dict[str, Any],
    session_id: str,
    visit_referrer: str | None,
    session_source_map: dict[str, dict[str, Any]],
) -> str:
    payload = payload or {}
    explicit_source = str(payload.get("source") or payload.get("source_category") or "").strip().lower()
    if explicit_source in SOURCE_CATEGORIES:
        return explicit_source

    category = _normalize_source_category(
        utm_source=payload.get("utm_source"),
        utm_medium=payload.get("utm_medium"),
        referrer=payload.get("referrer") or visit_referrer,
        source_raw=payload.get("source_raw") or explicit_source,
    )
    if category != "unknown":
        return category

    if session_id and session_id in session_source_map:
        return session_source_map[session_id]["category"]

    return _normalize_source_category(referrer=visit_referrer)


def _resolve_cta_id(payload: dict[str, Any]) -> str:
    payload = payload or {}
    return (
        str(payload.get("cta_id") or payload.get("cta_key") or payload.get("entity_id") or "").strip().lower()
        or "cta"
    )[:120]


def _resolve_section_id(payload: dict[str, Any]) -> str:
    payload = payload or {}
    return (
        str(payload.get("section_id") or payload.get("section_key") or payload.get("entity_id") or "").strip().lower()
        or "section"
    )[:64]


def _resolve_field_parts(payload: dict[str, Any]) -> tuple[str, str, str, str]:
    payload = payload or {}
    form_id = (
        str(payload.get("form_id") or payload.get("form_key") or payload.get("form_name") or payload.get("id") or "")
        .strip()[:120]
        or "form"
    )
    field_name = (
        str(
            payload.get("field_name")
            or payload.get("field_label")
            or payload.get("name")
            or payload.get("field_id")
            or payload.get("field_key")
            or payload.get("entity_id")
            or "field"
        )
        .strip()[:64]
        or "field"
    )
    field_type = str(payload.get("field_type") or "").strip()[:32] or "unknown"
    key = f"{form_id}|{field_name}|{field_type}".strip("|")
    return key, form_id, field_name, field_type


def _mean(values: list[int | float]) -> float:
    if not values:
        return 0.0
    return round(float(sum(values)) / float(len(values)), 2)


def _collect_period_anomaly_metrics(client, from_dt, to_dt) -> dict[str, Any]:
    rows = (
        TrackerEvent.objects.filter(
            visit__site__token=client.api_key,
            visit__is_bot=False,
            timestamp__gte=from_dt,
            timestamp__lte=to_dt,
            type__in=AI_EVENT_TYPES,
        )
        .values("type", "payload", "visit__session_id")
        .order_by("timestamp", "id")
    )

    cta_clicks = 0
    form_starts = 0
    form_submit_success = 0
    form_submit_error = 0
    scroll_by_session: dict[str, int] = {}
    section_views: Counter[str] = Counter()

    for row in rows:
        event_type = str(row.get("type") or "").strip()
        canonical_type = _normalize_event_type(event_type)
        payload = row.get("payload") or {}
        if not isinstance(payload, dict):
            payload = {}

        if canonical_type == "cta_click":
            cta_clicks += 1
        elif canonical_type == "form_started":
            form_starts += 1
        elif canonical_type == "form_submit_success":
            form_submit_success += 1
        elif canonical_type == "form_submit_error":
            form_submit_error += 1
        elif canonical_type == "section_visible":
            section_key = _resolve_section_id(payload)
            section_views[section_key] += 1

        if canonical_type == "scroll_depth":
            session_id = (row.get("visit__session_id") or "").strip()
            if not session_id:
                continue
            depth = _normalize_scroll_depth(
                _safe_int(payload.get("depth") or payload.get("current_depth") or payload.get("max_depth"), default=0)
            )
            prev_depth = scroll_by_session.get(session_id, 0)
            if depth > prev_depth:
                scroll_by_session[session_id] = depth

    return {
        "cta_clicks": cta_clicks,
        "form_started": form_starts,
        "form_submit_success": form_submit_success,
        "form_submit_error": form_submit_error,
        "avg_scroll_depth": _mean(list(scroll_by_session.values())),
        "section_views": section_views,
    }


def _build_anomalies_payload(client, from_dt, to_dt) -> dict[str, Any]:
    duration = to_dt - from_dt
    prev_to = from_dt - timedelta(seconds=1)
    prev_from = prev_to - duration

    current_metrics = _collect_period_anomaly_metrics(client=client, from_dt=from_dt, to_dt=to_dt)
    previous_metrics = _collect_period_anomaly_metrics(client=client, from_dt=prev_from, to_dt=prev_to)

    key_section_candidates = Counter()
    key_section_candidates.update(current_metrics["section_views"])
    key_section_candidates.update(previous_metrics["section_views"])
    key_sections = [item[0] for item in key_section_candidates.most_common(3)]

    current_key_sections = sum(current_metrics["section_views"].get(key, 0) for key in key_sections)
    previous_key_sections = sum(previous_metrics["section_views"].get(key, 0) for key in key_sections)

    specs = [
        (
            "cta_clicks",
            "Клики по важным кнопкам",
            "down",
            float(current_metrics["cta_clicks"]),
            float(previous_metrics["cta_clicks"]),
        ),
        (
            "form_started",
            "Начали заполнять форму",
            "down",
            float(current_metrics["form_started"]),
            float(previous_metrics["form_started"]),
        ),
        (
            "form_submit_success",
            "Успешные отправки формы",
            "down",
            float(current_metrics["form_submit_success"]),
            float(previous_metrics["form_submit_success"]),
        ),
        (
            "form_submit_error",
            "Ошибки отправки формы",
            "up",
            float(current_metrics["form_submit_error"]),
            float(previous_metrics["form_submit_error"]),
        ),
        (
            "avg_scroll_depth",
            "Средняя глубина просмотра",
            "down",
            float(current_metrics["avg_scroll_depth"]),
            float(previous_metrics["avg_scroll_depth"]),
        ),
        (
            "key_section_views",
            "Просмотры ключевых блоков",
            "down",
            float(current_key_sections),
            float(previous_key_sections),
        ),
    ]

    rows = []
    anomaly_threshold_pct = 25.0
    for metric, label, direction, current_value, previous_value in specs:
        if previous_value <= 0:
            insufficient = True
            change_pct = 0.0
            status = "insufficient"
            is_anomaly = False
        else:
            insufficient = False
            change_pct = round(((current_value - previous_value) / previous_value) * 100.0, 2)
            is_anomaly = (direction == "down" and change_pct <= -anomaly_threshold_pct) or (
                direction == "up" and change_pct >= anomaly_threshold_pct
            )
            if is_anomaly:
                status = "anomaly"
            elif change_pct > 0:
                status = "growth"
            elif change_pct < 0:
                status = "decline"
            else:
                status = "stable"

        rows.append(
            {
                "metric": metric,
                "label": label,
                "current_value": round(current_value, 2),
                "previous_value": round(previous_value, 2),
                "change_pct": change_pct,
                "status": status,
                "is_anomaly": is_anomaly,
                "insufficient_data": insufficient,
            }
        )

    has_data = any(not row["insufficient_data"] for row in rows)
    insufficient_reason = None
    if not has_data:
        insufficient_reason = "Недостаточно данных для сравнения с предыдущим периодом."

    return {
        "has_data": has_data,
        "has_comparable_data": has_data,
        "insufficient_data": not has_data,
        "insufficient_data_reason": insufficient_reason,
        "display_mode": "full" if has_data else "compact",
        "rows": rows,
        "key_sections": key_sections,
        "period": {
            "current_from": from_dt.date(),
            "current_to": to_dt.date(),
            "previous_from": prev_from.date(),
            "previous_to": prev_to.date(),
        },
    }

def build_ai_event_signals_payload(client, from_dt, to_dt) -> dict[str, Any]:
    session_source_map = _build_session_source_map(client=client, from_dt=from_dt, to_dt=to_dt)

    tracker_rows = (
        TrackerEvent.objects.filter(
            visit__site__token=client.api_key,
            visit__is_bot=False,
            timestamp__gte=from_dt,
            timestamp__lte=to_dt,
            type__in=AI_EVENT_TYPES,
        )
        .values(
            "id",
            "type",
            "payload",
            "timestamp",
            "visit__session_id",
            "visit__visitor_id",
            "visit__device_type",
            "visit__referrer",
        )
        .order_by("timestamp", "id")
    )

    canonical_counts: Counter[str] = Counter()
    scroll_event_threshold_counts = {str(item): 0 for item in SCROLL_DEPTH_THRESHOLDS}
    scroll_max_by_user: dict[str, int] = {}
    form_funnel_users = {key: set() for key in FORM_STAGE_ALIASES.keys()}
    ai_users_in_analysis: set[str] = set()

    field_stats: dict[str, dict[str, Any]] = {}
    first_field_by_session: dict[str, tuple[Any, str]] = {}
    last_field_by_session: dict[str, tuple[Any, str]] = {}
    form_started_sessions: set[str] = set()
    form_success_sessions: set[str] = set()

    cta_stats: dict[str, dict[str, Any]] = {}
    section_stats: dict[str, dict[str, Any]] = {}

    micro_stats: dict[str, dict[str, Any]] = {}
    micro_conversion_users: set[str] = set()
    cta_click_users: set[str] = set()

    device_stats: dict[str, dict[str, Any]] = {key: _empty_segment_stats() for key in DEVICE_CATEGORIES}
    source_stats: dict[str, dict[str, Any]] = {key: _empty_segment_stats() for key in SOURCE_CATEGORIES}

    for row in tracker_rows:
        raw_type = str(row.get("type") or "").strip()
        canonical_type = _normalize_event_type(raw_type)
        payload = row.get("payload") or {}
        if not isinstance(payload, dict):
            payload = {}

        session_id = (row.get("visit__session_id") or "").strip()
        visitor_id = (row.get("visit__visitor_id") or "").strip()
        user_key = _user_key(visitor_id=visitor_id, session_id=session_id)
        device_type = _normalize_device_type(row.get("visit__device_type"))
        source_category = _resolve_source_category(
            payload=payload,
            session_id=session_id,
            visit_referrer=row.get("visit__referrer"),
            session_source_map=session_source_map,
        )

        device_bucket = device_stats.setdefault(device_type, _empty_segment_stats())
        source_bucket = source_stats.setdefault(source_category, _empty_segment_stats())

        canonical_counts[canonical_type] += 1
        if user_key:
            ai_users_in_analysis.add(user_key)

        if canonical_type in form_funnel_users and user_key:
            form_funnel_users[canonical_type].add(user_key)

        if canonical_type == "form_started":
            if session_id:
                form_started_sessions.add(session_id)
            if user_key:
                device_bucket["form_start_users"].add(user_key)
                source_bucket["form_start_users"].add(user_key)

        if canonical_type == "form_submit_success":
            if session_id:
                form_success_sessions.add(session_id)
            if user_key:
                device_bucket["form_submit_success_users"].add(user_key)
                source_bucket["form_submit_success_users"].add(user_key)

        if canonical_type == "scroll_depth":
            depth = _normalize_scroll_depth(
                _safe_int(payload.get("depth") or payload.get("current_depth") or payload.get("max_depth"), default=0)
            )
            threshold = _normalize_scroll_threshold(depth)
            if threshold:
                scroll_event_threshold_counts[str(threshold)] += 1
            if user_key:
                prev_user_depth = _safe_int(scroll_max_by_user.get(user_key), default=0)
                if depth > prev_user_depth:
                    scroll_max_by_user[user_key] = depth

            device_bucket["scroll_events"] += 1
            source_bucket["scroll_events"] += 1
            if session_id:
                if depth > _safe_int(device_bucket["scroll_by_session"].get(session_id), default=0):
                    device_bucket["scroll_by_session"][session_id] = depth
                if depth > _safe_int(source_bucket["scroll_by_session"].get(session_id), default=0):
                    source_bucket["scroll_by_session"][session_id] = depth

        if canonical_type == "cta_visible":
            device_bucket["cta_visible"] += 1
            source_bucket["cta_visible"] += 1
        elif canonical_type == "cta_click":
            device_bucket["cta_clicks"] += 1
            source_bucket["cta_clicks"] += 1
            if user_key:
                cta_click_users.add(user_key)

        if raw_type in FIELD_EVENT_TYPES:
            field_key, form_id, field_name, field_type = _resolve_field_parts(payload)
            if field_key:
                if field_key not in field_stats:
                    field_stats[field_key] = {
                        "field_key": field_key,
                        "form_id": form_id or "form",
                        "field_name": field_name,
                        "field_type": field_type,
                        "input_started_users": set(),
                        "completed_users": set(),
                        "error_users": set(),
                        "error_events": 0,
                        "revisit_users": set(),
                        "revisit_events": 0,
                        "drop_off_count": 0,
                    }
                stat = field_stats[field_key]

                if raw_type == "field_input_started" and user_key:
                    stat["input_started_users"].add(user_key)
                if raw_type == "field_completed" and user_key:
                    stat["completed_users"].add(user_key)
                if raw_type == "field_error":
                    stat["error_events"] += 1
                    if user_key:
                        stat["error_users"].add(user_key)
                if raw_type == "field_revisit":
                    stat["revisit_events"] += 1
                    if user_key:
                        stat["revisit_users"].add(user_key)

                if raw_type == "field_input_started" and session_id:
                    current = first_field_by_session.get(session_id)
                    if not current or row["timestamp"] < current[0]:
                        first_field_by_session[session_id] = (row["timestamp"], field_key)
                if session_id:
                    last_field_by_session[session_id] = (row["timestamp"], field_key)

        if raw_type in CTA_EVENT_TYPES:
            cta_id = _resolve_cta_id(payload)
            cta_text = str(payload.get("cta_text") or payload.get("text") or "").strip()[:120]
            cta_type = str(payload.get("cta_type") or "").strip()[:48] or "generic"
            target_type = str(payload.get("target_type") or "").strip()[:32] or "unknown"
            if cta_id not in cta_stats:
                cta_stats[cta_id] = {
                    "cta_id": cta_id,
                    "cta_text": cta_text,
                    "cta_type": cta_type,
                    "target_type": target_type,
                    "visible_users": set(),
                    "click_users": set(),
                    "target_users": set(),
                    "conversion_users": set(),
                }
            cta_row = cta_stats[cta_id]
            if cta_text:
                cta_row["cta_text"] = cta_text
            if cta_type:
                cta_row["cta_type"] = cta_type
            if target_type and target_type != "unknown":
                cta_row["target_type"] = target_type
            if user_key:
                if raw_type == "cta_visible":
                    cta_row["visible_users"].add(user_key)
                elif raw_type == "cta_click":
                    cta_row["click_users"].add(user_key)
                elif raw_type == "cta_target_reached":
                    cta_row["target_users"].add(user_key)
                elif raw_type == "cta_converted":
                    cta_row["conversion_users"].add(user_key)

        if raw_type in SECTION_EVENT_TYPES:
            section_id = _resolve_section_id(payload)
            section_name = str(payload.get("section_name") or section_id).strip()[:120] or section_id
            if section_id not in section_stats:
                section_stats[section_id] = {
                    "section_id": section_id,
                    "section_name": section_name,
                    "view_users": set(),
                    "time_total_seconds": 0,
                    "time_events": 0,
                    "cta_after_users": set(),
                    "form_start_after_users": set(),
                    "conversion_users": set(),
                    "exit_users": set(),
                }
            section_row = section_stats[section_id]
            if section_name:
                section_row["section_name"] = section_name

            if canonical_type == "section_visible" and user_key:
                section_row["view_users"].add(user_key)
            if raw_type == "section_time_spent":
                duration = _safe_int(payload.get("visible_duration_seconds") or payload.get("visible_duration"), default=0)
                if duration > 0:
                    section_row["time_total_seconds"] += duration
                    section_row["time_events"] += 1
            if raw_type == "section_interaction_after_view" and user_key:
                interaction_type = str(payload.get("interaction_type") or "").strip().lower()
                if interaction_type == "cta_click" or bool(payload.get("had_cta_click_after")):
                    section_row["cta_after_users"].add(user_key)
                if interaction_type == "form_started" or bool(payload.get("had_form_start_after")):
                    section_row["form_start_after_users"].add(user_key)
            if raw_type == "section_conversion_after_view" and user_key:
                section_row["conversion_users"].add(user_key)
            if raw_type == "section_exit_after_view" and user_key:
                section_row["exit_users"].add(user_key)

        if raw_type in MICRO_CONVERSION_EVENT_TYPES:
            if raw_type not in micro_stats:
                micro_stats[raw_type] = {
                    "event": raw_type,
                    "count": 0,
                    "users": set(),
                    "pages": Counter(),
                    "sections": Counter(),
                }
            micro_row = micro_stats[raw_type]
            micro_row["count"] += 1
            if user_key:
                micro_row["users"].add(user_key)
                micro_conversion_users.add(user_key)
            page_path = _path_from_page_url(payload.get("page_url"), payload.get("path"))
            micro_row["pages"][page_path] += 1
            section_key = _resolve_section_id(payload) if payload.get("section_id") or payload.get("section_key") else ""
            if section_key:
                micro_row["sections"][section_key] += 1

    for session_id in form_started_sessions:
        if session_id in form_success_sessions:
            continue
        last_field = last_field_by_session.get(session_id)
        if not last_field:
            continue
        field_key = last_field[1]
        if field_key in field_stats:
            field_stats[field_key]["drop_off_count"] += 1

    first_field_counter = Counter()
    for _, field_key in first_field_by_session.values():
        first_field_counter[field_key] += 1

    visits_rows = Visit.objects.filter(
        site__token=client.api_key,
        started_at__gte=from_dt,
        started_at__lte=to_dt,
        is_bot=False,
    ).values("session_id", "visitor_id", "device_type", "referrer")

    for row in visits_rows:
        session_id = (row.get("session_id") or "").strip()
        visitor_id = (row.get("visitor_id") or "").strip()
        user_key = _user_key(visitor_id=visitor_id, session_id=session_id)
        device_type = _normalize_device_type(row.get("device_type"))
        source_category = _resolve_source_category(
            payload={},
            session_id=session_id,
            visit_referrer=row.get("referrer"),
            session_source_map=session_source_map,
        )
        if session_id:
            device_stats[device_type]["sessions"].add(session_id)
            source_stats[source_category]["sessions"].add(session_id)
        if user_key:
            device_stats[device_type]["users"].add(user_key)
            source_stats[source_category]["users"].add(user_key)

    form_stage_order = [
        ("form_visible", "Form visible"),
        ("form_started", "Form started"),
        ("form_first_field_completed", "First field completed"),
        ("form_submit_attempt", "Form submit attempt"),
        ("form_submit_success", "Form submit success"),
        ("form_submit_error", "Form submit error"),
    ]
    first_stage_users = len(form_funnel_users["form_visible"])
    form_funnel_rows = []
    for idx, (stage_key, stage_label) in enumerate(form_stage_order):
        users_count = len(form_funnel_users[stage_key])
        next_users = 0
        if idx < len(form_stage_order) - 1:
            next_users = len(form_funnel_users[form_stage_order[idx + 1][0]])
        form_funnel_rows.append(
            {
                "stage": stage_key,
                "label": stage_label,
                "users": users_count,
                "next_step_rate_pct": _pct(next_users, users_count) if idx < len(form_stage_order) - 1 else 0.0,
                "from_first_step_pct": _pct(users_count, first_stage_users),
            }
        )
    form_funnel_min_users = 3
    form_funnel_has_data = first_stage_users >= form_funnel_min_users

    field_rows = []
    field_error_users: set[str] = set()
    for row in field_stats.values():
        started = len(row["input_started_users"])
        completed = len(row["completed_users"])
        field_error_users.update(row["error_users"])
        field_rows.append(
            {
                "field_key": row["field_key"],
                "form_id": row["form_id"],
                "field_name": row["field_name"],
                "field_type": row["field_type"],
                "started": started,
                "completed": completed,
                "errors": int(row["error_events"]),
                "revisits": int(row["revisit_events"]),
                "drop_off": int(row["drop_off_count"]),
                "completion_rate_pct": _pct(completed, started),
            }
        )
    field_rows.sort(key=lambda item: (item["started"], item["errors"], item["revisits"]), reverse=True)

    field_summary = {
        "form_started_users": len(form_funnel_users["form_started"]),
        "first_field_completed_users": len(form_funnel_users["form_first_field_completed"]),
        "field_error_users": len(field_error_users),
    }

    top_drop_off = None
    if field_rows:
        candidate = max(field_rows, key=lambda item: item["drop_off"])
        if candidate["drop_off"] > 0:
            top_drop_off = {
                "field_key": candidate["field_key"],
                "field_name": candidate["field_name"],
                "form_id": candidate["form_id"],
                "count": candidate["drop_off"],
            }

    top_error = None
    if field_rows:
        candidate = max(field_rows, key=lambda item: item["errors"])
        if candidate["errors"] > 0:
            top_error = {
                "field_key": candidate["field_key"],
                "field_name": candidate["field_name"],
                "form_id": candidate["form_id"],
                "count": candidate["errors"],
            }

    top_revisit = None
    if field_rows:
        candidate = max(field_rows, key=lambda item: item["revisits"])
        if candidate["revisits"] > 0:
            top_revisit = {
                "field_key": candidate["field_key"],
                "field_name": candidate["field_name"],
                "form_id": candidate["form_id"],
                "count": candidate["revisits"],
            }

    first_field_rows = []
    for field_key, count in first_field_counter.most_common():
        field_meta = field_stats.get(field_key)
        if not field_meta:
            continue
        first_field_rows.append(
            {
                "field_key": field_key,
                "form_id": field_meta["form_id"],
                "field_name": field_meta["field_name"],
                "field_type": field_meta["field_type"],
                "count": int(count),
            }
        )

    cta_rows = []
    for item in cta_stats.values():
        shows = len(item["visible_users"])
        clicks = len(item["click_users"])
        target_reached = len(item["target_users"])
        conversions = len(item["conversion_users"])
        cta_rows.append(
            {
                "cta_id": item["cta_id"],
                "cta_text": item["cta_text"],
                "cta_type": item["cta_type"],
                "target_type": item["target_type"],
                "shows": shows,
                "clicks": clicks,
                "target_reached": target_reached,
                "conversions": conversions,
                "ctr_pct": _pct(clicks, shows),
                "click_to_conversion_rate_pct": _pct(conversions, clicks),
            }
        )
    cta_rows.sort(key=lambda item: (item["conversions"], item["clicks"], item["shows"]), reverse=True)

    section_rows = []
    for item in section_stats.values():
        views = len(item["view_users"])
        cta_after = len(item["cta_after_users"])
        form_start_after = len(item["form_start_after_users"])
        conversions_after = len(item["conversion_users"])
        exit_after = len(item["exit_users"])
        avg_time = 0.0
        if item["time_events"] > 0:
            avg_time = round(float(item["time_total_seconds"]) / float(item["time_events"]), 2)
        section_rows.append(
            {
                "section_id": item["section_id"],
                "section_name": item["section_name"],
                "views": views,
                "avg_time_spent_seconds": avg_time,
                "cta_after_section": cta_after,
                "form_start_after_section": form_start_after,
                "conversions_after_section": conversions_after,
                "exit_after_section": exit_after,
                "exit_after_section_rate_pct": _pct(exit_after, views),
            }
        )
    section_rows.sort(key=lambda item: (item["views"], item["avg_time_spent_seconds"]), reverse=True)

    device_rows = []
    for device in DEVICE_CATEGORIES:
        item = device_stats[device]
        form_started = len(item["form_start_users"])
        form_submit_success = len(item["form_submit_success_users"])
        avg_scroll_depth = _mean(list(item["scroll_by_session"].values()))
        device_rows.append(
            {
                "device": device,
                "sessions": len(item["sessions"]),
                "users": len(item["users"]),
                "scroll_events": int(item["scroll_events"]),
                "cta_clicks": int(item["cta_clicks"]),
                "form_starts": form_started,
                "form_submit_success": form_submit_success,
                "form_conversion_rate_pct": _pct(form_submit_success, form_started),
                "avg_scroll_depth": avg_scroll_depth,
            }
        )

    source_rows = []
    for source in SOURCE_CATEGORIES:
        item = source_stats[source]
        form_started = len(item["form_start_users"])
        form_submit_success = len(item["form_submit_success_users"])
        source_rows.append(
            {
                "source": source,
                "sessions": len(item["sessions"]),
                "users": len(item["users"]),
                "avg_scroll_depth": _mean(list(item["scroll_by_session"].values())),
                "cta_ctr_pct": _pct(item["cta_clicks"], item["cta_visible"]),
                "form_starts": form_started,
                "form_submit_success": form_submit_success,
                "conversion_rate_pct": _pct(form_submit_success, form_started),
            }
        )

    total_device_users = sum(row["users"] for row in device_rows)
    total_device_sessions = sum(row["sessions"] for row in device_rows)
    for row in device_rows:
        row["users_share_pct"] = _pct(row["users"], total_device_users)
        row["sessions_share_pct"] = _pct(row["sessions"], total_device_sessions)

    total_source_users = sum(row["users"] for row in source_rows)
    total_source_sessions = sum(row["sessions"] for row in source_rows)
    for row in source_rows:
        row["users_share_pct"] = _pct(row["users"], total_source_users)
        row["sessions_share_pct"] = _pct(row["sessions"], total_source_sessions)

    scroll_threshold_users = {str(item): 0 for item in SCROLL_DEPTH_THRESHOLDS}
    for depth in scroll_max_by_user.values():
        for threshold in SCROLL_DEPTH_THRESHOLDS:
            if depth >= threshold:
                scroll_threshold_users[str(threshold)] += 1
    scroll_unique_users_total = len(scroll_max_by_user)
    scroll_threshold_rates_pct = {
        key: _pct(value, scroll_unique_users_total) for key, value in scroll_threshold_users.items()
    }

    micro_rows = []
    for event_name in MICRO_CONVERSION_EVENT_TYPES:
        item = micro_stats.get(event_name)
        if not item:
            continue
        top_page = item["pages"].most_common(1)[0][0] if item["pages"] else None
        top_section = item["sections"].most_common(1)[0][0] if item["sections"] else None
        micro_rows.append(
            {
                "event": event_name,
                "label": MICRO_CONVERSION_LABELS.get(event_name, event_name),
                "count": int(item["count"]),
                "unique_users": len(item["users"]),
                "page": top_page,
                "section": top_section,
            }
        )
    micro_rows.sort(key=lambda item: item["count"], reverse=True)

    anomalies = _build_anomalies_payload(client=client, from_dt=from_dt, to_dt=to_dt)

    form_visible_count = canonical_counts["form_visible"]
    form_started_count = canonical_counts["form_started"]
    first_field_completed_count = canonical_counts["form_first_field_completed"]
    form_submit_attempt_count = canonical_counts["form_submit_attempt"]
    form_submit_success_count = canonical_counts["form_submit_success"]
    form_submit_error_count = canonical_counts["form_submit_error"]
    section_visible_count = canonical_counts["section_visible"]
    cta_click_count = canonical_counts["cta_click"]
    ai_unique_users_total = len(ai_users_in_analysis)

    return {
        "overview": {
            "unique_users_total": ai_unique_users_total,
            "avg_scroll_depth": _mean(list(scroll_max_by_user.values())),
            "form_started_users": len(form_funnel_users["form_started"]),
            "form_submit_success_users": len(form_funnel_users["form_submit_success"]),
            "cta_click_users": len(cta_click_users),
            "micro_conversion_users": len(micro_conversion_users),
        },
        "scroll_depth": {
            "events_total": int(canonical_counts["scroll_depth"]),
            "thresholds": scroll_threshold_users,
            "threshold_event_counts": scroll_event_threshold_counts,
            "unique_users_total": scroll_unique_users_total,
            "avg_scroll_depth": _mean(list(scroll_max_by_user.values())),
            "threshold_users": scroll_threshold_users,
            "threshold_rates_pct": scroll_threshold_rates_pct,
        },
        "forms": {
            "form_view": int(form_visible_count),
            "form_start": int(form_started_count),
            "form_first_field_filled": int(first_field_completed_count),
            "form_submit_attempt": int(form_submit_attempt_count),
            "form_submit_success": int(form_submit_success_count),
            "form_submit_error": int(form_submit_error_count),
            "form_visible": int(form_visible_count),
            "form_started": int(form_started_count),
            "form_first_field_completed": int(first_field_completed_count),
        },
        "section_views": {
            "events_total": int(section_visible_count),
        },
        "cta_clicks": {
            "events_total": int(cta_click_count),
        },
        "form_funnel": {
            "has_data": form_funnel_has_data,
            "insufficient_data": not form_funnel_has_data,
            "min_users_required": form_funnel_min_users,
            "insufficient_data_reason": (
                f"Пока недостаточно данных: нужно минимум {form_funnel_min_users} уникальных пользователя, "
                "которые увидели форму."
            )
            if not form_funnel_has_data
            else "",
            "rows": form_funnel_rows,
        },
        "field_analytics": {
            "has_data": bool(field_rows),
            "insufficient_data": len(field_rows) == 0,
            "insufficient_data_reason": (
                "Пока нет событий по полям формы (начало ввода, завершение, ошибки, возвраты)."
                if len(field_rows) == 0
                else ""
            ),
            "rows": field_rows,
            "summary": field_summary,
            "first_field_starts": first_field_rows,
            "top_drop_off_field": top_drop_off,
            "top_error_field": top_error,
            "top_revisit_field": top_revisit,
        },
        "cta_funnel": {
            "has_data": bool(cta_rows),
            "insufficient_data": len(cta_rows) == 0,
            "insufficient_data_reason": (
                "Пока нет достаточного числа событий показа и кликов по кнопкам."
                if len(cta_rows) == 0
                else ""
            ),
            "rows": cta_rows,
        },
        "section_analytics": {
            "has_data": bool(section_rows),
            "insufficient_data": len(section_rows) == 0,
            "insufficient_data_reason": (
                "Пока нет событий просмотра секций и взаимодействий после просмотра."
                if len(section_rows) == 0
                else ""
            ),
            "rows": section_rows,
        },
        "device_segmentation": {
            "has_data": any(row["sessions"] > 0 for row in device_rows),
            "insufficient_data": not any(row["sessions"] > 0 for row in device_rows),
            "insufficient_data_reason": (
                "Пока нет визитов для сегментации по устройствам."
                if not any(row["sessions"] > 0 for row in device_rows)
                else ""
            ),
            "rows": device_rows,
        },
        "source_segmentation": {
            "has_data": any(row["sessions"] > 0 for row in source_rows),
            "insufficient_data": not any(row["sessions"] > 0 for row in source_rows),
            "insufficient_data_reason": (
                "Пока нет визитов с определяемым источником трафика."
                if not any(row["sessions"] > 0 for row in source_rows)
                else ""
            ),
            "rows": source_rows,
        },
        "micro_conversions": {
            "has_data": bool(micro_rows),
            "insufficient_data": len(micro_rows) == 0,
            "insufficient_data_reason": (
                "Пока нет полезных действий: кликов по контактам, карте, FAQ или медиа."
                if len(micro_rows) == 0
                else ""
            ),
            "rows": micro_rows,
        },
        "anomalies": anomalies,
    }
