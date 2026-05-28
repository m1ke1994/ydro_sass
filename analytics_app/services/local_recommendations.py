from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

MAX_ITEMS = 6
MIN_ITEMS = 3
MIN_USERS = 12
MIN_VISITS = 30

PRIORITY_WEIGHT = {"high": 0, "medium": 1, "low": 2}
INTERNAL_PATH_PREFIXES = ("/app/dashboard", "/api", "/admin", "/auth", "/login", "/register")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_pathname(value: Any) -> str:
    raw = _normalize_text(value)
    if not raw:
        return ""
    try:
        if raw.lower().startswith(("http://", "https://")):
            return _normalize_text(urlparse(raw).path) or "/"
    except Exception:
        return ""
    path = raw.split("?", 1)[0].split("#", 1)[0].strip()
    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"


def _is_internal_path(pathname: str) -> bool:
    lowered = _normalize_text(pathname).lower()
    if not lowered:
        return True
    return lowered.startswith(INTERNAL_PATH_PREFIXES)


def _short_path(pathname: str) -> str:
    value = _normalize_pathname(pathname) or "/"
    if len(value) <= 46:
        return value
    return f"{value[:43].rstrip()}..."


def _format_paths(rows: list[dict[str, Any]], max_items: int = 2) -> str:
    return ", ".join(f"«{_short_path(row['pathname'])}»" for row in rows[:max_items])


def _normalize_page_rows(summary_payload: dict[str, Any]) -> list[dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    sources = []
    if isinstance(summary_payload.get("conversion_by_pages"), list):
        sources.append(("conversion", summary_payload.get("conversion_by_pages") or []))
    if isinstance(summary_payload.get("engagement_pages"), list):
        sources.append(("engagement", summary_payload.get("engagement_pages") or []))

    for source_name, rows in sources:
        for row in rows:
            if not isinstance(row, dict):
                continue
            pathname = _normalize_pathname(
                row.get("pathname") or row.get("path") or row.get("url") or row.get("page_pathname") or row.get("page")
            )
            if not pathname or _is_internal_path(pathname):
                continue

            visits = _safe_int(
                row.get("visits")
                or row.get("visits_count")
                or row.get("sessions")
                or row.get("views")
                or row.get("count")
            )
            leads = _safe_int(row.get("leads") or row.get("form_submit_success") or row.get("conversions"))
            conversion_pct = _safe_float(row.get("conversion_pct") or row.get("conversion_rate_pct"))
            if conversion_pct <= 0 and visits > 0:
                conversion_pct = round((leads / visits) * 100.0, 2)

            existing = result.get(pathname, {"pathname": pathname, "visits": 0, "leads": 0, "conversion_pct": 0.0, "source": source_name})
            merged_visits = max(_safe_int(existing.get("visits")), visits)
            merged_leads = max(_safe_int(existing.get("leads")), leads)
            merged_conversion = round((merged_leads / merged_visits) * 100.0, 2) if merged_visits > 0 else max(
                _safe_float(existing.get("conversion_pct")),
                conversion_pct,
            )

            result[pathname] = {
                "pathname": pathname,
                "visits": merged_visits,
                "leads": merged_leads,
                "conversion_pct": merged_conversion,
                "source": "conversion" if existing.get("source") == "conversion" or source_name == "conversion" else source_name,
            }

    return sorted((row for row in result.values() if row["visits"] > 0), key=lambda item: (-item["visits"], item["pathname"]))


def _build_result(
    *,
    status: str,
    summary: str,
    items: list[str],
    priority: str,
    stats: dict[str, int | float],
) -> dict[str, Any]:
    return {
        "success": True,
        "source": "local",
        "fallback": False,
        "title": "Рекомендации по поведению пользователей",
        "summary": summary,
        "items": items[:MAX_ITEMS],
        "priority": priority,
        "status": status,
        "user_message": summary,
        "stats": stats,
    }


def build_behavior_recommendations(summary_payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = summary_payload if isinstance(summary_payload, dict) else {}
    ai_signals = payload.get("ai_event_signals") if isinstance(payload.get("ai_event_signals"), dict) else {}
    overview = ai_signals.get("overview") if isinstance(ai_signals.get("overview"), dict) else {}
    forms = ai_signals.get("forms") if isinstance(ai_signals.get("forms"), dict) else {}
    cta_funnel = ai_signals.get("cta_funnel") if isinstance(ai_signals.get("cta_funnel"), dict) else {}
    field_analytics = ai_signals.get("field_analytics") if isinstance(ai_signals.get("field_analytics"), dict) else {}

    page_rows = _normalize_page_rows(payload)
    visits_total = max(_safe_int(payload.get("visit_count")), sum(_safe_int(item.get("visits")) for item in page_rows))
    unique_users = max(
        _safe_int(payload.get("visitors_unique")),
        _safe_int(overview.get("unique_users_total")),
        _safe_int(ai_signals.get("scroll_depth", {}).get("unique_users_total")) if isinstance(ai_signals.get("scroll_depth"), dict) else 0,
    )
    leads_total = _safe_int(payload.get("leads_count"))
    avg_scroll_depth = max(
        _safe_float(overview.get("avg_scroll_depth")),
        _safe_float(payload.get("avg_scroll_depth")),
        _safe_float(ai_signals.get("scroll_depth", {}).get("avg_scroll_depth")) if isinstance(ai_signals.get("scroll_depth"), dict) else 0.0,
    )
    form_visible = _safe_int(forms.get("form_visible") or forms.get("form_view"))
    form_started = max(_safe_int(forms.get("form_started") or forms.get("form_start")), _safe_int(overview.get("form_started_users")))
    form_submit_attempt = _safe_int(forms.get("form_submit_attempt"))
    form_submit_success = max(_safe_int(forms.get("form_submit_success")), _safe_int(overview.get("form_submit_success_users")))
    form_submit_error = _safe_int(forms.get("form_submit_error"))
    cta_rows = cta_funnel.get("rows") if isinstance(cta_funnel.get("rows"), list) else []

    pages_with_traffic = len(page_rows)
    stats = {
        "visits_total": visits_total,
        "unique_users": unique_users,
        "leads_total": leads_total,
        "pages_with_traffic": pages_with_traffic,
        "form_started": form_started,
        "form_submit_success": form_submit_success,
        "avg_scroll_depth": round(avg_scroll_depth, 2),
    }

    has_enough_data = unique_users >= MIN_USERS or visits_total >= MIN_VISITS or form_started >= 6 or form_submit_success >= 2
    if not has_enough_data:
        return _build_result(
            status="insufficient",
            summary="Пока недостаточно данных для точных рекомендаций. Нужны дополнительные визиты и взаимодействия.",
            items=[],
            priority="low",
            stats=stats,
        )

    recommendations: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    def push(*, key: str, priority: str, text: str, score: int = 0) -> None:
        message = _normalize_text(text)
        if not message or key in seen_keys:
            return
        seen_keys.add(key)
        recommendations.append(
            {
                "key": key,
                "priority": priority if priority in PRIORITY_WEIGHT else "medium",
                "score": score,
                "text": message,
            }
        )

    high_traffic_threshold = max(20, round(max(visits_total, sum(item["visits"] for item in page_rows)) * 0.12))
    high_traffic_pages = [row for row in page_rows if row["visits"] >= high_traffic_threshold]
    zero_lead_pages = [row for row in high_traffic_pages if row["leads"] <= 0]
    low_conversion_pages = [
        row for row in high_traffic_pages if row["leads"] <= 1 and _safe_float(row["conversion_pct"]) < 1.0
    ]
    best_page = None
    best_candidates = [row for row in page_rows if row["visits"] >= 10 and row["leads"] >= 2 and _safe_float(row["conversion_pct"]) > 0]
    if best_candidates:
        best_page = sorted(best_candidates, key=lambda item: (-_safe_float(item["conversion_pct"]), -item["leads"], -item["visits"]))[0]

    if zero_lead_pages:
        push(
            key="zero-lead-pages",
            priority="high",
            score=len(zero_lead_pages),
            text=(
                f"На страницах {_format_paths(zero_lead_pages)} есть трафик без заявок. "
                "Усильте первый экран, оффер и заметную кнопку действия (CTA) рядом с ключевым контентом."
            ),
        )

    home_page = next((row for row in page_rows if row["pathname"] == "/"), None)
    if home_page and home_page["visits"] >= max(15, high_traffic_threshold) and _safe_float(home_page["conversion_pct"]) < 1.0:
        push(
            key="home-page",
            priority="high" if home_page["leads"] <= 0 else "medium",
            score=home_page["visits"],
            text="Главная страница получает трафик, но почти не конвертирует. Усильте первый экран, блок доверия и сценарий перехода к заявке.",
        )

    if low_conversion_pages:
        push(
            key="low-conversion-pages",
            priority="medium",
            score=len(low_conversion_pages),
            text=f"Сделайте путь до заявки короче на страницах {_format_paths(low_conversion_pages)}: уберите лишние шаги и оставьте один основной сценарий действия.",
        )

    if form_visible > 0:
        form_start_rate = round((form_started / form_visible) * 100.0, 2) if form_visible > 0 else 0.0
        if form_start_rate < 22:
            push(
                key="form-visibility",
                priority="medium",
                score=int(form_visible),
                text=(
                    "Переход к началу формы слабый. Сделайте форму заметнее в первом экране "
                    "и добавьте короткий оффер рядом с кнопкой действия (CTA)."
                ),
            )

    if form_started > 0:
        form_completion_rate = round((form_submit_success / form_started) * 100.0, 2) if form_started > 0 else 0.0
        if form_completion_rate < 45:
            push(
                key="form-completion",
                priority="high" if form_submit_success <= max(1, form_started // 4) else "medium",
                score=form_started,
                text="Если пользователи начинают, но не завершают форму, сократите число полей, уберите лишние шаги и оставьте только самое важное.",
            )

    if form_submit_attempt > 0:
        form_error_rate = round((form_submit_error / form_submit_attempt) * 100.0, 2) if form_submit_attempt > 0 else 0.0
        if form_error_rate >= 12:
            push(
                key="form-errors",
                priority="high" if form_error_rate >= 20 else "medium",
                score=form_submit_error,
                text="Проверьте валидацию формы и тексты ошибок: пользователю должно быть сразу понятно, как исправить ввод и отправить заявку.",
            )

    top_drop_off = field_analytics.get("top_drop_off_field") if isinstance(field_analytics.get("top_drop_off_field"), dict) else {}
    top_drop_off_count = _safe_int(top_drop_off.get("count"))
    if top_drop_off_count >= 3:
        push(
            key="field-drop-off",
            priority="medium",
            score=top_drop_off_count,
            text=f"Упростите поле «{_normalize_text(top_drop_off.get('field_name')) or 'поле'}»: на нём чаще всего останавливаются пользователи при заполнении формы.",
        )

    if avg_scroll_depth > 0 and avg_scroll_depth < 45:
        push(
            key="scroll-depth",
            priority="medium",
            score=int(round(100 - avg_scroll_depth)),
            text="Глубина просмотра слабая. Улучшите структуру страницы, подачу ключевых блоков и сделайте целевое действие заметнее выше по экрану.",
        )

    if best_page and (zero_lead_pages or low_conversion_pages):
        push(
            key="best-page-pattern",
            priority="medium",
            score=int(best_page["leads"]),
            text=(
                f"Страница {_short_path(best_page['pathname'])} конвертирует лучше других. "
                "Используйте её структуру, оффер и кнопку действия (CTA) как шаблон для слабых страниц."
            ),
        )

    weak_cta = None
    for row in cta_rows:
        if not isinstance(row, dict):
            continue
        shows = _safe_int(row.get("shows"))
        ctr = _safe_float(row.get("ctr_pct"))
        if shows >= 40 and 0 < ctr < 1.2:
            weak_cta = row
            break
    if weak_cta:
        push(
            key="weak-cta",
            priority="medium",
            score=_safe_int(weak_cta.get("shows")),
            text=(
                "На части кнопок низкий CTR. Перепроверьте текст кнопки действия (CTA): "
                "добавьте конкретную пользу и ожидаемый результат после клика."
            ),
        )

    if len(recommendations) < MIN_ITEMS:
        push(
            key="trust-near-form",
            priority="low",
            score=1,
            text="Добавьте рядом с формой более явные элементы доверия: преимущества, кейсы, гарантии и быстрый способ связи.",
        )
    if len(recommendations) < MIN_ITEMS:
        push(
            key="primary-cta",
            priority="low",
            score=1,
            text=(
                "На страницах с трафиком оставьте один главный сценарий до заявки: "
                "одну основную кнопку действия (CTA), короткий оффер и минимум отвлекающих блоков."
            ),
        )
    if len(recommendations) < MIN_ITEMS:
        push(
            key="page-review",
            priority="low",
            score=1,
            text="Регулярно сравнивайте страницы с трафиком и страницы с заявками, чтобы быстрее находить слабые места в пути пользователя.",
        )

    recommendations.sort(
        key=lambda item: (
            PRIORITY_WEIGHT.get(item["priority"], 3),
            -int(item["score"] or 0),
            item["text"],
        )
    )
    items = [item["text"] for item in recommendations[:MAX_ITEMS]]

    if zero_lead_pages or (form_started > 0 and form_submit_success < max(2, form_started // 2)):
        summary = "Есть заметные потери в пути пользователя. Сначала исправьте страницы с трафиком без заявок и самый слабый шаг формы."
        priority = "high"
        status = "issues"
    elif items:
        summary = "Есть точки роста в поведении пользователей. Начните с страниц и шагов, где путь до заявки обрывается чаще всего."
        priority = "medium"
        status = "issues"
    else:
        summary = "Серьёзных провалов в поведении пользователей не видно. Сейчас можно сосредоточиться на точечных улучшениях."
        priority = "low"
        status = "clean"

    return _build_result(
        status=status,
        summary=summary,
        items=items,
        priority=priority,
        stats=stats,
    )
