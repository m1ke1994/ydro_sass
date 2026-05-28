from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from seo_audit.services.messages import get_issue_title

MAX_ITEMS = 8
MIN_ITEMS = 4

SPEED_ISSUE_TYPES = {
    "slow_response",
    "large_page_size",
    "slow_ttfb",
    "large_html_size",
    "too_many_js",
    "too_many_css",
    "too_many_images",
    "heavy_js_payload",
    "heavy_css_payload",
    "heavy_images_payload",
    "heavy_page_payload",
}
INDEXING_ISSUE_TYPES = {
    "missing_robots_txt",
    "robots_disallow_all",
    "robots_missing_sitemap",
    "missing_sitemap",
    "bad_sitemap_status",
    "sitemap_mismatch",
    "missing_canonical",
    "invalid_canonical",
    "canonical_conflict",
    "page_noindex",
    "page_nofollow",
    "blocked_by_robots",
    "sitemap_page_missing",
    "missing_meta_robots",
}
TITLE_ISSUE_TYPES = {
    "missing_title",
    "duplicate_title",
    "bad_title_length",
    "title_too_short",
    "title_too_long",
}
DESCRIPTION_ISSUE_TYPES = {
    "missing_description",
    "description_too_short",
    "description_too_long",
}
H1_ISSUE_TYPES = {"missing_h1", "multiple_h1", "long_h1", "heading_hierarchy_gap"}
ALT_ISSUE_TYPES = {"image_missing_alt", "image_empty_alt"}
CANONICAL_ISSUE_TYPES = {"missing_canonical", "invalid_canonical", "canonical_conflict"}
ROBOTS_ISSUE_TYPES = {"missing_robots_txt", "robots_disallow_all", "blocked_by_robots", "page_noindex", "page_nofollow"}
SITEMAP_ISSUE_TYPES = {"missing_sitemap", "bad_sitemap_status", "sitemap_mismatch", "sitemap_page_missing", "robots_missing_sitemap"}

SEVERITY_WEIGHT = {"high": 5, "medium": 3, "low": 1}
PRIORITY_WEIGHT = {"high": 0, "medium": 1, "low": 2}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_severity(value: Any) -> str:
    severity = _normalize_text(value).lower()
    if severity in {"high", "medium", "low"}:
        return severity
    return "medium"


def _normalize_issue_rows(audit_payload: dict[str, Any]) -> list[dict[str, str]]:
    rows = audit_payload.get("errors")
    if not isinstance(rows, list):
        grouped = audit_payload.get("grouped_errors") or {}
        rows = []
        if isinstance(grouped, dict):
            for key in ("high", "medium", "low"):
                if isinstance(grouped.get(key), list):
                    rows.extend(grouped.get(key) or [])

    normalized: list[dict[str, str]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        issue_type = _normalize_text(row.get("issue_type")).lower()
        issue_title = _normalize_text(row.get("issue_title") or row.get("title")) or get_issue_title(issue_type)
        page_url = _normalize_text(row.get("page_url") or row.get("url"))
        normalized.append(
            {
                "issue_type": issue_type,
                "issue_title": issue_title,
                "severity": _normalize_severity(row.get("severity")),
                "page_url": page_url,
            }
        )
    return normalized


def _normalize_page_rows(audit_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = audit_payload.get("pages")
    if not isinstance(rows, list):
        return []

    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "url": _normalize_text(row.get("url")),
                "performance_score": _safe_int(row.get("performance_score")),
                "ttfb_ms": _safe_int(row.get("ttfb_ms")),
                "speed_status": _normalize_text(row.get("speed_status")).lower(),
                "indexability_status": _normalize_text(row.get("indexability_status")).lower(),
            }
        )
    return normalized


def _build_result(
    *,
    status: str,
    summary: str,
    items: list[str],
    priority: str,
    stats: dict[str, int],
) -> dict[str, Any]:
    return {
        "success": True,
        "source": "local",
        "fallback": False,
        "title": "Рекомендации по SEO",
        "summary": summary,
        "items": items[:MAX_ITEMS],
        "priority": priority,
        "status": status,
        "user_message": summary,
        "stats": stats,
    }


def build_seo_recommendations(audit_payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = audit_payload if isinstance(audit_payload, dict) else {}
    issues = _normalize_issue_rows(payload)
    pages = _normalize_page_rows(payload)

    breakdown = payload.get("breakdown") if isinstance(payload.get("breakdown"), dict) else {}
    high_issues = _safe_int(breakdown.get("high_issues"), sum(1 for item in issues if item["severity"] == "high"))
    medium_issues = _safe_int(
        breakdown.get("medium_issues"),
        sum(1 for item in issues if item["severity"] == "medium"),
    )
    low_issues = _safe_int(breakdown.get("low_issues"), sum(1 for item in issues if item["severity"] == "low"))
    pages_count = max(
        _safe_int(payload.get("pages_count")),
        len(pages),
        len({item["page_url"] for item in issues if item["page_url"]}),
    )
    pages_with_speed_issues = max(
        _safe_int(payload.get("pages_with_speed_issues")),
        len([page for page in pages if page["speed_status"] in {"warning", "critical"}]),
    )
    pages_with_indexing_issues = max(
        _safe_int(payload.get("pages_with_indexing_issues")),
        len([page for page in pages if page["indexability_status"] in {"blocked", "conflict", "noindex"}]),
    )

    stats = {
        "pages_count": pages_count,
        "high_issues": high_issues,
        "medium_issues": medium_issues,
        "low_issues": low_issues,
        "pages_with_speed_issues": pages_with_speed_issues,
        "pages_with_indexing_issues": pages_with_indexing_issues,
    }

    if pages_count <= 0 and not issues:
        return _build_result(
            status="insufficient",
            summary="Пока недостаточно данных для точных рекомендаций по SEO-аудиту.",
            items=[],
            priority="low",
            stats=stats,
        )

    issue_type_counts: Counter[str] = Counter()
    issue_pages: dict[str, set[str]] = defaultdict(set)
    page_scores: dict[str, int] = defaultdict(int)
    page_issue_counts: dict[str, int] = defaultdict(int)
    for item in issues:
        issue_type = item["issue_type"]
        page_url = item["page_url"]
        severity = item["severity"]
        if issue_type:
            issue_type_counts[issue_type] += 1
            if page_url:
                issue_pages[issue_type].add(page_url)
        if page_url:
            page_scores[page_url] += SEVERITY_WEIGHT.get(severity, 1)
            page_issue_counts[page_url] += 1

    worst_page = ""
    if page_scores:
        worst_page = max(page_scores, key=lambda url: (page_scores[url], page_issue_counts[url], url))

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

    total_issues = high_issues + medium_issues + low_issues
    if high_issues > 0:
        start_text = "Сначала устраните критичные ошибки"
        if worst_page:
            start_text = f"{start_text} и начните со страницы {worst_page}"
        push(
            key="critical-first",
            priority="high",
            score=high_issues * 10,
            text=f"{start_text}. Это даст самый быстрый эффект по техническому SEO.",
        )
    elif total_issues > 0 and worst_page:
        push(
            key="worst-page",
            priority="medium" if medium_issues > 0 else "low",
            score=page_scores.get(worst_page, 0),
            text=f"Начните исправления со страницы {worst_page}: на ней сейчас больше всего замечаний.",
        )

    title_issue_count = sum(issue_type_counts[item] for item in TITLE_ISSUE_TYPES)
    missing_or_duplicate_title = issue_type_counts["missing_title"] + issue_type_counts["duplicate_title"]
    if missing_or_duplicate_title > 0:
        push(
            key="titles-missing-duplicate",
            priority="high" if issue_type_counts["missing_title"] > 0 else "medium",
            score=missing_or_duplicate_title,
            text="На части страниц нет уникального заголовка в поиске (title). Добавьте разные title для каждой важной страницы.",
        )
    elif title_issue_count > 0:
        push(
            key="titles-length",
            priority="medium",
            score=title_issue_count,
            text="Проверьте длину title: слишком короткие и слишком длинные заголовки хуже работают в поисковой выдаче.",
        )

    description_issue_count = sum(issue_type_counts[item] for item in DESCRIPTION_ISSUE_TYPES)
    if description_issue_count > 0:
        push(
            key="descriptions",
            priority="medium",
            score=description_issue_count,
            text="Заполните понятные описания страниц для поиска (meta description), где они пустые, слишком короткие или слишком длинные.",
        )

    h1_issue_count = sum(issue_type_counts[item] for item in H1_ISSUE_TYPES)
    if h1_issue_count > 0:
        push(
            key="h1",
            priority="medium",
            score=h1_issue_count,
            text="Проверьте главный заголовок страницы (H1): он должен быть один и чётко описывать, о чём страница.",
        )

    alt_issue_count = sum(issue_type_counts[item] for item in ALT_ISSUE_TYPES)
    if alt_issue_count > 0:
        push(
            key="alt",
            priority="medium" if alt_issue_count >= 3 else "low",
            score=alt_issue_count,
            text="У некоторых изображений нет текстового описания (alt). Добавьте короткие понятные описания для важных изображений.",
        )

    indexing_issue_count = sum(issue_type_counts[item] for item in INDEXING_ISSUE_TYPES)
    canonical_issue_count = sum(issue_type_counts[item] for item in CANONICAL_ISSUE_TYPES)
    robots_issue_count = sum(issue_type_counts[item] for item in ROBOTS_ISSUE_TYPES)
    if indexing_issue_count > 0 or pages_with_indexing_issues > 0:
        push(
            key="indexing",
            priority="high" if robots_issue_count > 0 or canonical_issue_count > 0 else "medium",
            score=indexing_issue_count + pages_with_indexing_issues,
            text="Проверьте правила индексации и основной адрес страницы (canonical): из-за ошибок часть страниц может не попадать в поиск.",
        )

    sitemap_issue_count = sum(issue_type_counts[item] for item in SITEMAP_ISSUE_TYPES)
    if sitemap_issue_count > 0 or not bool(payload.get("has_sitemap_xml")):
        push(
            key="sitemap",
            priority="high" if sitemap_issue_count > 0 else "medium",
            score=sitemap_issue_count + int(not bool(payload.get("has_sitemap_xml"))),
            text="Обновите и проверьте sitemap.xml, чтобы в неё попадали все индексируемые страницы.",
        )

    speed_issue_count = sum(issue_type_counts[item] for item in SPEED_ISSUE_TYPES)
    avg_ttfb_ms = _safe_int(payload.get("avg_ttfb_ms"))
    avg_performance_score = _safe_int(payload.get("avg_performance_score"))
    has_speed_problem = (
        speed_issue_count > 0
        or pages_with_speed_issues > 0
        or avg_ttfb_ms >= 800
        or (avg_performance_score > 0 and avg_performance_score < 65)
    )
    if has_speed_problem:
        speed_text = (
            "Упростите загрузку страниц: сожмите тяжёлые изображения и уменьшите количество блокирующих скриптов и стилей."
        )
        if issue_type_counts["slow_ttfb"] > 0 or avg_ttfb_ms >= 1000:
            speed_text = (
                "Сервер отвечает слишком медленно (высокий TTFB). Ускорьте ответ сервера, уменьшите блокирующие скрипты и оптимизируйте тяжёлые изображения."
            )
        push(
            key="speed",
            priority="high" if issue_type_counts["slow_ttfb"] > 0 or pages_with_speed_issues >= 3 else "medium",
            score=speed_issue_count + pages_with_speed_issues,
            text=speed_text,
        )

    repeated_issue_type = ""
    repeated_issue_pages = 0
    for issue_type, affected_pages in issue_pages.items():
        pages_total = len(affected_pages)
        if pages_total < 2:
            continue
        if not repeated_issue_type or pages_total > repeated_issue_pages:
            repeated_issue_type = issue_type
            repeated_issue_pages = pages_total
    if repeated_issue_type:
        issue_title = get_issue_title(repeated_issue_type).rstrip(".")
        push(
            key="repeated",
            priority="medium" if repeated_issue_pages >= 3 else "low",
            score=repeated_issue_pages,
            text=f"Исправьте повторяющуюся проблему «{issue_title}» сразу на группе страниц: это быстро сократит общее число ошибок.",
        )

    if len(recommendations) < MIN_ITEMS and worst_page and total_issues > 0:
        push(
            key="batch-fix",
            priority="low",
            score=page_scores.get(worst_page, 0),
            text=f"Соберите правки пакетно для страницы {worst_page} и аналогичных шаблонов, чтобы быстрее закрыть типовые ошибки.",
        )
    if len(recommendations) < MIN_ITEMS and total_issues > 0:
        push(
            key="rerun-audit",
            priority="low",
            score=1,
            text="После внедрения правок перезапустите аудит и сравните результаты, чтобы проверить снижение числа ошибок.",
        )

    recommendations.sort(
        key=lambda item: (
            PRIORITY_WEIGHT.get(item["priority"], 3),
            -int(item["score"] or 0),
            item["text"],
        )
    )
    items = [item["text"] for item in recommendations[:MAX_ITEMS]]

    if total_issues <= 0:
        return _build_result(
            status="clean",
            summary="Серьёзных проблем не обнаружено. Сейчас можно сосредоточиться на точечных улучшениях.",
            items=[
                "Поддерживайте текущую структуру мета-тегов и проверяйте новые страницы сразу после публикации.",
                "Следите за скоростью ключевых страниц после обновлений контента, скриптов и изображений.",
            ],
            priority="low",
            stats=stats,
        )

    if high_issues <= 0 and medium_issues <= 0:
        summary = "Серьёзных проблем не обнаружено. Сейчас можно сосредоточиться на точечных улучшениях."
        priority = "low"
        status = "clean"
    elif high_issues > 0:
        summary = "В аудите есть критичные проблемы. Сначала закройте страницы и группы ошибок, которые сильнее всего мешают индексации и скорости."
        priority = "high"
        status = "issues"
    else:
        summary = "Есть проблемы среднего приоритета, которые сдерживают рост SEO. Начните с повторяющихся ошибок на важных страницах."
        priority = "medium"
        status = "issues"

    return _build_result(
        status=status,
        summary=summary,
        items=items,
        priority=priority,
        stats=stats,
    )
