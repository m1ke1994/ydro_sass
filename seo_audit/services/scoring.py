# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict

from seo_audit.models import SEOIssue, SEOPage, SiteSEOAudit
from seo_audit.services.messages import (
    get_commercial_business_status,
    get_commercial_explanation,
    get_commercial_recommendations,
    get_conversion_path_label,
    get_commercial_status_label,
    get_issue_group_meta,
    get_issue_title,
    get_priority_label,
)

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

CRITICAL_SCORE_ISSUE_TYPES = {
    "network_error",
    "bad_status",
    "robots_disallow_all",
    "missing_robots_txt",
    "missing_sitemap",
    "bad_sitemap_status",
    "blocked_by_robots",
    "slow_ttfb",
    "heavy_page_payload",
}

SCORE_COMPONENT_WEIGHTS = {
    "technical_accessibility": 0.32,
    "indexability": 0.24,
    "meta_structure": 0.20,
    "performance": 0.16,
    "issues_health": 0.08,
}


def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(float(value)))))


def _safe_ratio(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return max(0.0, float(part) / float(total))


def _average_int(values: list[int]) -> int:
    if not values:
        return 0
    return int(round(sum(values) / len(values)))


def _build_audit_score_snapshot(audit: SiteSEOAudit) -> dict[str, object]:
    pages = list(
        SEOPage.objects.filter(audit=audit).values(
            "id",
            "status_code",
            "ttfb_ms",
            "performance_score",
            "speed_status",
            "indexability_status",
            "blocked_by_robots",
            "in_sitemap",
            "title",
            "description",
            "h1",
            "h1_count",
            "word_count",
            "canonical_url",
        )
    )
    issues = list(SEOIssue.objects.filter(page__audit=audit).values("severity", "issue_type", "page_id"))

    severity_counts = {
        SEOIssue.Severity.HIGH: 0,
        SEOIssue.Severity.MEDIUM: 0,
        SEOIssue.Severity.LOW: 0,
    }
    issue_type_counts: dict[str, int] = defaultdict(int)
    issue_page_ids_by_type: dict[str, set[int]] = defaultdict(set)
    speed_issue_page_ids: set[int] = set()
    indexing_issue_page_ids: set[int] = set()

    for issue in issues:
        severity = str(issue.get("severity") or "").strip().lower()
        issue_type = str(issue.get("issue_type") or "").strip().lower()
        page_id = int(issue.get("page_id") or 0)
        if severity in severity_counts:
            severity_counts[severity] += 1
        if issue_type:
            issue_type_counts[issue_type] += 1
            if page_id > 0:
                issue_page_ids_by_type[issue_type].add(page_id)
            if issue_type in SPEED_ISSUE_TYPES and page_id > 0:
                speed_issue_page_ids.add(page_id)
            if issue_type in INDEXING_ISSUE_TYPES and page_id > 0:
                indexing_issue_page_ids.add(page_id)

    pages_count = len(pages)
    status_200_pages = [item for item in pages if int(item.get("status_code") or 0) == 200]
    status_200_ids = {int(item.get("id") or 0) for item in status_200_pages}
    status_200_count = len(status_200_pages)

    network_error_pages = sum(
        1
        for item in pages
        if int(item.get("status_code") or 0) == 0 or int(item.get("id") or 0) in issue_page_ids_by_type["network_error"]
    )
    non_200_pages = sum(1 for item in pages if int(item.get("status_code") or 0) != 200)
    http_error_pages = sum(1 for item in pages if int(item.get("status_code") or 0) >= 400)
    critical_ttfb_pages = sum(1 for item in pages if int(item.get("ttfb_ms") or 0) >= 3000)
    slow_ttfb_pages = sum(1 for item in pages if int(item.get("ttfb_ms") or 0) >= 1800)
    warning_ttfb_pages = sum(1 for item in pages if int(item.get("ttfb_ms") or 0) >= 900)

    critical_speed_pages = sum(
        1 for item in pages if str(item.get("speed_status") or "").strip().lower() == SEOPage.SpeedStatus.CRITICAL
    )
    warning_speed_pages = sum(
        1 for item in pages if str(item.get("speed_status") or "").strip().lower() == SEOPage.SpeedStatus.WARNING
    )
    unknown_speed_pages = sum(
        1 for item in pages if str(item.get("speed_status") or "").strip().lower() == SEOPage.SpeedStatus.UNKNOWN
    )

    index_unknown_pages = sum(
        1
        for item in pages
        if str(item.get("indexability_status") or "").strip().lower() == SEOPage.IndexabilityStatus.UNKNOWN
    )
    index_noindex_pages = sum(
        1
        for item in pages
        if str(item.get("indexability_status") or "").strip().lower() == SEOPage.IndexabilityStatus.NOINDEX
    )
    index_conflict_pages = sum(
        1
        for item in pages
        if str(item.get("indexability_status") or "").strip().lower() == SEOPage.IndexabilityStatus.CONFLICT
    )
    blocked_by_robots_pages = sum(1 for item in pages if bool(item.get("blocked_by_robots")))

    missing_title_pages = sum(1 for item in status_200_pages if not str(item.get("title") or "").strip())
    missing_description_pages = sum(1 for item in status_200_pages if not str(item.get("description") or "").strip())
    missing_h1_pages = sum(
        1
        for item in status_200_pages
        if int(item.get("h1_count") or 0) <= 0 or not str(item.get("h1") or "").strip()
    )
    multiple_h1_pages = sum(1 for item in status_200_pages if int(item.get("h1_count") or 0) > 1)
    low_word_count_pages = sum(1 for item in status_200_pages if int(item.get("word_count") or 0) < 300)
    missing_canonical_pages = sum(1 for item in status_200_pages if not str(item.get("canonical_url") or "").strip())
    invalid_canonical_pages = len(issue_page_ids_by_type["invalid_canonical"] & status_200_ids)
    missing_meta_robots_pages = len(issue_page_ids_by_type["missing_meta_robots"] & status_200_ids)
    not_in_sitemap_pages = sum(1 for item in status_200_pages if not bool(item.get("in_sitemap")))

    ttfb_values = [int(item.get("ttfb_ms") or 0) for item in pages if int(item.get("ttfb_ms") or 0) > 0]
    performance_values = [
        int(item.get("performance_score") or 0) for item in pages if int(item.get("performance_score") or 0) > 0
    ]
    avg_ttfb = _average_int(ttfb_values)
    avg_performance = _average_int(performance_values)

    network_error_ratio = _safe_ratio(network_error_pages, pages_count)
    non_200_ratio = _safe_ratio(non_200_pages, pages_count)
    http_error_ratio = _safe_ratio(http_error_pages, pages_count)
    critical_ttfb_ratio = _safe_ratio(critical_ttfb_pages, pages_count)
    slow_ttfb_ratio = _safe_ratio(slow_ttfb_pages, pages_count)
    warning_ttfb_ratio = _safe_ratio(warning_ttfb_pages, pages_count)
    critical_speed_ratio = _safe_ratio(critical_speed_pages, pages_count)
    warning_speed_ratio = _safe_ratio(warning_speed_pages, pages_count)
    unknown_speed_ratio = _safe_ratio(unknown_speed_pages, pages_count)
    index_unknown_ratio = _safe_ratio(index_unknown_pages, pages_count)
    index_noindex_ratio = _safe_ratio(index_noindex_pages, pages_count)
    index_conflict_ratio = _safe_ratio(index_conflict_pages, pages_count)
    blocked_by_robots_ratio = _safe_ratio(blocked_by_robots_pages, pages_count)

    if pages_count <= 0:
        technical_accessibility_score = 0
    else:
        technical_raw = 100.0
        technical_raw -= network_error_ratio * 70
        technical_raw -= http_error_ratio * 45
        technical_raw -= non_200_ratio * 20
        technical_raw -= critical_ttfb_ratio * 20
        technical_raw -= slow_ttfb_ratio * 10
        if network_error_pages > 0:
            technical_raw -= 15
        if status_200_count == 0:
            technical_raw -= 35
        technical_accessibility_score = _clamp_score(technical_raw)

    if pages_count <= 0:
        indexability_score = 0
    else:
        indexability_raw = 100.0
        if not bool(audit.has_robots_txt):
            indexability_raw -= 30
        if not bool(audit.has_sitemap_xml):
            indexability_raw -= 25
        if issue_type_counts.get("robots_disallow_all", 0) > 0:
            indexability_raw -= 30
        indexability_raw -= blocked_by_robots_ratio * 32
        indexability_raw -= index_unknown_ratio * 28
        indexability_raw -= index_noindex_ratio * 20
        indexability_raw -= index_conflict_ratio * 18
        if status_200_count > 0:
            indexability_raw -= _safe_ratio(missing_canonical_pages, status_200_count) * 18
            indexability_raw -= _safe_ratio(invalid_canonical_pages, status_200_count) * 16
            if bool(audit.has_sitemap_xml) and int(audit.sitemap_urls_count or 0) > 0:
                indexability_raw -= _safe_ratio(not_in_sitemap_pages, status_200_count) * 12
        else:
            indexability_raw -= 15
        if issue_type_counts.get("missing_sitemap", 0) > 0 and not bool(audit.has_sitemap_xml):
            indexability_raw -= 10
        indexability_score = _clamp_score(indexability_raw)

    if pages_count <= 0:
        meta_structure_score = 0
    elif status_200_count <= 0:
        meta_structure_score = 10 if network_error_pages > 0 else 20
    else:
        meta_raw = 100.0
        meta_raw -= _safe_ratio(missing_title_pages, status_200_count) * 35
        meta_raw -= _safe_ratio(missing_description_pages, status_200_count) * 25
        meta_raw -= _safe_ratio(missing_h1_pages, status_200_count) * 20
        meta_raw -= _safe_ratio(multiple_h1_pages, status_200_count) * 10
        meta_raw -= _safe_ratio(low_word_count_pages, status_200_count) * 10
        meta_raw -= _safe_ratio(missing_meta_robots_pages, status_200_count) * 8
        if status_200_count < pages_count:
            meta_raw -= 8
        meta_structure_score = _clamp_score(meta_raw)

    if pages_count <= 0:
        performance_group_score = 0
    else:
        performance_raw = float(avg_performance if avg_performance > 0 else 25)
        if avg_ttfb >= 3000:
            performance_raw -= 35
        elif avg_ttfb >= 2000:
            performance_raw -= 25
        elif avg_ttfb >= 1300:
            performance_raw -= 15
        elif avg_ttfb >= 900:
            performance_raw -= 8
        performance_raw -= critical_speed_ratio * 30
        performance_raw -= warning_speed_ratio * 12
        performance_raw -= network_error_ratio * 20
        if avg_performance <= 0:
            performance_raw -= 10
        if unknown_speed_ratio > 0.6:
            performance_raw -= 8
        performance_group_score = _clamp_score(performance_raw)

    critical_issue_instances = sum(issue_type_counts.get(issue_type, 0) for issue_type in CRITICAL_SCORE_ISSUE_TYPES)
    issues_penalty_points = (
        severity_counts[SEOIssue.Severity.HIGH] * 5
        + severity_counts[SEOIssue.Severity.MEDIUM] * 2
        + severity_counts[SEOIssue.Severity.LOW] * 0.75
        + critical_issue_instances * 2.5
    )
    if pages_count > 0:
        issues_penalty_points += _safe_ratio(critical_issue_instances, pages_count) * 8
    issues_health_score = _clamp_score(100 - min(85, issues_penalty_points))

    weighted_score = (
        technical_accessibility_score * SCORE_COMPONENT_WEIGHTS["technical_accessibility"]
        + indexability_score * SCORE_COMPONENT_WEIGHTS["indexability"]
        + meta_structure_score * SCORE_COMPONENT_WEIGHTS["meta_structure"]
        + performance_group_score * SCORE_COMPONENT_WEIGHTS["performance"]
        + issues_health_score * SCORE_COMPONENT_WEIGHTS["issues_health"]
    )
    score = _clamp_score(weighted_score)

    guardrails_applied = {
        "all_pages_unavailable": False,
        "high_network_error_ratio": False,
        "missing_robots_and_sitemap": False,
        "very_high_avg_ttfb": False,
        "unknown_indexability_all_pages": False,
        "critical_technical_and_indexability": False,
        "network_plus_missing_index_files": False,
    }
    if pages_count > 0:
        if status_200_count == 0:
            score = min(score, 35)
            guardrails_applied["all_pages_unavailable"] = True
        if network_error_ratio >= 0.5:
            score = min(score, 40)
            guardrails_applied["high_network_error_ratio"] = True
        if (not bool(audit.has_robots_txt)) and (not bool(audit.has_sitemap_xml)):
            score = min(score, 60)
            guardrails_applied["missing_robots_and_sitemap"] = True
        if avg_ttfb >= 3000:
            score = min(score, 55)
            guardrails_applied["very_high_avg_ttfb"] = True
        if index_unknown_pages == pages_count:
            score = min(score, 50)
            guardrails_applied["unknown_indexability_all_pages"] = True
        if technical_accessibility_score <= 25 and indexability_score <= 35:
            score = min(score, 42)
            guardrails_applied["critical_technical_and_indexability"] = True
        if issue_type_counts.get("network_error", 0) > 0 and (not bool(audit.has_robots_txt)) and (not bool(audit.has_sitemap_xml)):
            score = min(score, 35)
            guardrails_applied["network_plus_missing_index_files"] = True
    score = _clamp_score(score)

    return {
        "score": score,
        "severity_counts": severity_counts,
        "avg_ttfb_ms": avg_ttfb,
        "avg_performance_score": avg_performance,
        "pages_count": pages_count,
        "pages_with_speed_issues": len(speed_issue_page_ids),
        "pages_with_indexing_issues": len(indexing_issue_page_ids),
        "score_components": {
            "technical_accessibility_score": technical_accessibility_score,
            "indexability_score": indexability_score,
            "meta_structure_score": meta_structure_score,
            "performance_score": performance_group_score,
            "issues_health_score": issues_health_score,
            "weights": {name: int(round(weight * 100)) for name, weight in SCORE_COMPONENT_WEIGHTS.items()},
            "issues_penalty_points": round(float(issues_penalty_points), 2),
            "guardrails": guardrails_applied,
        },
        "score_inputs": {
            "pages_total": pages_count,
            "pages_http_200": status_200_count,
            "pages_network_error": network_error_pages,
            "pages_http_error": http_error_pages,
            "pages_non_200": non_200_pages,
            "pages_unknown_indexability": index_unknown_pages,
            "pages_blocked_by_robots": blocked_by_robots_pages,
            "pages_not_in_sitemap": not_in_sitemap_pages,
            "pages_missing_title": missing_title_pages,
            "pages_missing_description": missing_description_pages,
            "pages_missing_h1": missing_h1_pages,
            "pages_multiple_h1": multiple_h1_pages,
            "pages_low_word_count": low_word_count_pages,
            "pages_missing_canonical": missing_canonical_pages,
            "pages_invalid_canonical": invalid_canonical_pages,
            "pages_missing_meta_robots": missing_meta_robots_pages,
            "pages_critical_speed": critical_speed_pages,
            "pages_warning_speed": warning_speed_pages,
            "pages_unknown_speed": unknown_speed_pages,
            "avg_ttfb_ms": avg_ttfb,
            "avg_performance_score": avg_performance,
            "ratio_network_error": round(network_error_ratio, 4),
            "ratio_non_200": round(non_200_ratio, 4),
            "ratio_http_error": round(http_error_ratio, 4),
            "ratio_critical_ttfb": round(critical_ttfb_ratio, 4),
            "ratio_slow_ttfb": round(slow_ttfb_ratio, 4),
            "ratio_warning_ttfb": round(warning_ttfb_ratio, 4),
            "ratio_unknown_indexability": round(index_unknown_ratio, 4),
            "ratio_blocked_by_robots": round(blocked_by_robots_ratio, 4),
        },
    }


def calculate_audit_score_breakdown(audit: SiteSEOAudit) -> dict[str, object]:
    snapshot = _build_audit_score_snapshot(audit)
    severity_counts = snapshot["severity_counts"]
    return {
        "score": int(snapshot["score"] or 0),
        "high_issues": int(severity_counts[SEOIssue.Severity.HIGH]),
        "medium_issues": int(severity_counts[SEOIssue.Severity.MEDIUM]),
        "low_issues": int(severity_counts[SEOIssue.Severity.LOW]),
        "score_components": snapshot["score_components"],
        "score_inputs": snapshot["score_inputs"],
    }


def recalculate_audit_score(audit: SiteSEOAudit) -> dict[str, object]:
    snapshot = _build_audit_score_snapshot(audit)
    severity_counts = snapshot["severity_counts"]

    audit.seo_score = int(snapshot["score"] or 0)
    audit.pages_count = int(snapshot["pages_count"] or 0)
    audit.avg_ttfb_ms = int(snapshot["avg_ttfb_ms"] or 0)
    audit.avg_performance_score = int(snapshot["avg_performance_score"] or 0)
    audit.pages_with_speed_issues = int(snapshot["pages_with_speed_issues"] or 0)
    audit.pages_with_indexing_issues = int(snapshot["pages_with_indexing_issues"] or 0)
    audit.save(
        update_fields=[
            "seo_score",
            "pages_count",
            "avg_ttfb_ms",
            "avg_performance_score",
            "pages_with_speed_issues",
            "pages_with_indexing_issues",
        ]
    )

    return {
        "score": int(snapshot["score"] or 0),
        "high_issues": int(severity_counts[SEOIssue.Severity.HIGH]),
        "medium_issues": int(severity_counts[SEOIssue.Severity.MEDIUM]),
        "low_issues": int(severity_counts[SEOIssue.Severity.LOW]),
        "score_components": snapshot["score_components"],
        "score_inputs": snapshot["score_inputs"],
    }


SEVERITY_PRIORITY_WEIGHT = {
    SEOIssue.Severity.HIGH: 3,
    SEOIssue.Severity.MEDIUM: 2,
    SEOIssue.Severity.LOW: 1,
}

PRIORITY_SORT_WEIGHT = {
    "urgent": 3,
    "important": 2,
    "later": 1,
}


def _normalize_severity(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in SEVERITY_PRIORITY_WEIGHT:
        return normalized
    return SEOIssue.Severity.LOW


def _priority_from_severity(severity: str, default_priority: str) -> str:
    normalized = _normalize_severity(severity)
    if normalized == SEOIssue.Severity.HIGH:
        return "urgent"
    if normalized == SEOIssue.Severity.MEDIUM:
        return "important" if default_priority != "urgent" else "urgent"
    return default_priority if default_priority in PRIORITY_SORT_WEIGHT else "later"


def _max_severity(left: str, right: str) -> str:
    l = _normalize_severity(left)
    r = _normalize_severity(right)
    return l if SEVERITY_PRIORITY_WEIGHT[l] >= SEVERITY_PRIORITY_WEIGHT[r] else r


def build_issue_groups(issues_payload: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for issue in issues_payload or []:
        issue_type = str(issue.get("issue_type") or "").strip().lower()
        if not issue_type:
            continue
        severity = _normalize_severity(issue.get("severity"))
        page_url = str(issue.get("page_url") or "").strip()
        meta = get_issue_group_meta(issue_type)
        entry = grouped.get(issue_type)
        if not entry:
            entry = {
                "issue_type": issue_type,
                "title": str(issue.get("issue_title") or get_issue_title(issue_type) or issue_type),
                "group_key": meta["group_key"],
                "group_label": meta["label"],
                "description": meta["description"],
                "target_block": meta["target_block"],
                "severity": severity,
                "issues_count": 0,
                "pages_affected": set(),
                "pages": [],
                "priority_key": _priority_from_severity(severity, meta["default_priority"]),
            }
            grouped[issue_type] = entry

        entry["issues_count"] += 1
        entry["severity"] = _max_severity(entry["severity"], severity)
        entry["priority_key"] = _priority_from_severity(entry["severity"], meta["default_priority"])
        if page_url and page_url not in entry["pages_affected"]:
            entry["pages_affected"].add(page_url)
            if len(entry["pages"]) < 25:
                entry["pages"].append(page_url)

    rows: list[dict] = []
    for entry in grouped.values():
        rows.append(
            {
                "issue_type": entry["issue_type"],
                "title": entry["title"],
                "group_key": entry["group_key"],
                "group_label": entry["group_label"],
                "description": entry["description"],
                "target_block": entry["target_block"],
                "severity": entry["severity"],
                "issues_count": int(entry["issues_count"]),
                "pages_affected": int(len(entry["pages_affected"])),
                "pages": entry["pages"],
                "priority_key": entry["priority_key"],
                "priority_label": get_priority_label(entry["priority_key"]),
            }
        )

    rows.sort(
        key=lambda item: (
            PRIORITY_SORT_WEIGHT.get(item["priority_key"], 0),
            SEVERITY_PRIORITY_WEIGHT.get(item["severity"], 0),
            item["pages_affected"],
            item["issues_count"],
        ),
        reverse=True,
    )
    return rows


def enrich_commercial_pages(pages_payload: list[dict]) -> list[dict]:
    enriched = []
    for row in pages_payload or []:
        payload = row.get("commercial_signals_payload")
        payload = payload if isinstance(payload, dict) else {}
        payload_conversion_signals = payload.get("conversion_signals")
        payload_conversion_signals = payload_conversion_signals if isinstance(payload_conversion_signals, dict) else {}

        signals = {
            "has_form": bool(row.get("has_form")),
            "has_cta": bool(row.get("has_cta")),
            "has_phone_or_contact": bool(row.get("has_phone_or_contact")),
            "has_messenger": bool(row.get("has_messenger")),
            "has_offer_like_heading": bool(row.get("has_offer_like_heading")),
            "has_benefits_block": bool(row.get("has_benefits_block")),
            "has_faq": bool(row.get("has_faq")),
            "has_direct_contact": bool(payload_conversion_signals.get("has_direct_contact")),
            "has_contact_block": bool(payload_conversion_signals.get("has_contact_block")),
            "has_messenger_contact": bool(payload_conversion_signals.get("has_messenger_contact", row.get("has_messenger"))),
            "has_widget": bool(payload_conversion_signals.get("has_widget")),
            "has_multi_channel_contact": bool(payload_conversion_signals.get("has_multi_channel_contact")),
        }
        has_conversion_path = row.get("has_conversion_path")
        if has_conversion_path is None:
            has_conversion_path = payload.get("has_conversion_path")
        conversion_path_type = str(
            row.get("conversion_path_type") or payload.get("conversion_path_type") or SEOPage.ConversionPathType.NONE
        )
        resolved_has_conversion_path = (
            bool(has_conversion_path)
            if has_conversion_path is not None
            else bool(
                signals.get("has_form")
                or signals.get("has_direct_contact")
                or signals.get("has_contact_block")
                or signals.get("has_messenger_contact")
                or signals.get("has_widget")
                or conversion_path_type in {
                    SEOPage.ConversionPathType.FORM,
                    SEOPage.ConversionPathType.CONTACTS,
                    SEOPage.ConversionPathType.MESSENGER,
                    SEOPage.ConversionPathType.WIDGET,
                    SEOPage.ConversionPathType.MIXED,
                }
            )
        )
        signals["has_conversion_path"] = resolved_has_conversion_path
        signals["conversion_path_type"] = conversion_path_type

        score = int(row.get("commercial_readiness_score") or 0)
        status_key = str(row.get("commercial_status") or SEOPage.CommercialStatus.WARNING)
        recommendations = get_commercial_recommendations(
            signals,
            has_conversion_path=resolved_has_conversion_path,
            conversion_path_type=conversion_path_type,
            score=score,
        )
        status_label = get_commercial_status_label(
            status_key,
            signals=signals,
            has_conversion_path=resolved_has_conversion_path,
            conversion_path_type=conversion_path_type,
            score=score,
        )
        business_key = get_commercial_business_status(
            status_key=status_key,
            signals=signals,
            has_conversion_path=resolved_has_conversion_path,
            conversion_path_type=conversion_path_type,
            score=score,
        )
        explanation = get_commercial_explanation(
            signals=signals,
            has_conversion_path=resolved_has_conversion_path,
            conversion_path_type=conversion_path_type,
            status_key=status_key,
            score=score,
        )
        conversion_signals = {
            "has_form": bool(signals.get("has_form")),
            "has_cta": bool(signals.get("has_cta")),
            "has_direct_contact": bool(signals.get("has_direct_contact") or signals.get("has_phone_or_contact")),
            "has_contact_block": bool(signals.get("has_contact_block")),
            "has_messenger_contact": bool(signals.get("has_messenger_contact") or signals.get("has_messenger")),
            "has_widget": bool(signals.get("has_widget")),
            "has_multi_channel_contact": bool(signals.get("has_multi_channel_contact")),
            "has_offer_like_heading": bool(signals.get("has_offer_like_heading")),
            "has_benefits_block": bool(signals.get("has_benefits_block")),
            "has_faq": bool(signals.get("has_faq")),
        }
        enriched.append(
            {
                **row,
                "commercial_signals": signals,
                "conversion_signals": conversion_signals,
                "has_conversion_path": resolved_has_conversion_path,
                "conversion_path_type": conversion_path_type,
                "conversion_path_type_label": get_conversion_path_label(conversion_path_type),
                "contact_signals": payload.get("contact_signals") or {},
                "cta_signals": payload.get("cta_signals") or {},
                "messenger_signals": payload.get("messenger_signals") or {},
                "widget_signals": payload.get("widget_signals") or {},
                "commercial_explanation": explanation,
                "commercial_recommendations": recommendations,
                "commercial_status_label": status_label,
                "commercial_business_status": business_key,
                "commercial_business_status_label": status_label,
            }
        )
    return enriched


def build_commercial_summary(pages_payload: list[dict]) -> dict[str, object]:
    pages = enrich_commercial_pages(pages_payload)
    total = len(pages)
    if total == 0:
        return {
            "has_data": False,
            "pages_total": 0,
            "avg_score": 0,
            "good_pages": 0,
            "warning_pages": 0,
            "critical_pages": 0,
            "ready_pages": 0,
            "has_channel_pages": 0,
            "improvable_pages": 0,
            "weak_pages": 0,
            "no_conversion_path_pages": 0,
            "conversion_path_types": {},
            "signals_presence": {},
            "top_recommendations": [],
            "pages": [],
        }

    good_pages = 0
    warning_pages = 0
    critical_pages = 0
    business_status_counts = defaultdict(int)
    conversion_path_counts = defaultdict(int)
    score_sum = 0
    signal_counts = defaultdict(int)
    recommendation_counts = defaultdict(int)
    for row in pages:
        status_key = str(row.get("commercial_status") or SEOPage.CommercialStatus.WARNING)
        if status_key == SEOPage.CommercialStatus.GOOD:
            good_pages += 1
        elif status_key == SEOPage.CommercialStatus.CRITICAL:
            critical_pages += 1
        else:
            warning_pages += 1

        score_sum += int(row.get("commercial_readiness_score") or 0)
        business_key = str(row.get("commercial_business_status") or "").strip().lower() or "improvable"
        business_status_counts[business_key] += 1
        path_type = str(row.get("conversion_path_type") or SEOPage.ConversionPathType.NONE)
        conversion_path_counts[path_type] += 1

        signals = row.get("conversion_signals") or row.get("commercial_signals") or {}
        for signal_key, value in signals.items():
            if bool(value):
                signal_counts[signal_key] += 1
        for recommendation in row.get("commercial_recommendations") or []:
            recommendation_counts[recommendation] += 1

    top_recommendations = sorted(
        [
            {"text": text, "pages_affected": count}
            for text, count in recommendation_counts.items()
            if count > 0
        ],
        key=lambda item: item["pages_affected"],
        reverse=True,
    )[:7]

    return {
        "has_data": True,
        "pages_total": total,
        "avg_score": int(round(score_sum / total)),
        "good_pages": good_pages,
        "warning_pages": warning_pages,
        "critical_pages": critical_pages,
        "ready_pages": int(business_status_counts["ready"]),
        "has_channel_pages": int(business_status_counts["has_channel"]),
        "improvable_pages": int(business_status_counts["improvable"]),
        "weak_pages": int(business_status_counts["weak"]),
        "no_conversion_path_pages": int(business_status_counts["none"]),
        "conversion_path_types": {key: int(value) for key, value in conversion_path_counts.items()},
        "signals_presence": {key: int(value) for key, value in signal_counts.items()},
        "top_recommendations": top_recommendations,
        "pages": pages,
    }


def build_fix_plan(
    *,
    audit: SiteSEOAudit,
    issue_groups: list[dict],
    commercial_summary: dict[str, object],
) -> list[dict]:
    plan: list[dict] = []
    for item in issue_groups[:7]:
        if int(item.get("pages_affected") or 0) <= 0:
            continue
        plan.append(
            {
                "title": item["title"],
                "why_it_matters": item["description"],
                "pages_affected": int(item["pages_affected"]),
                "priority_key": item["priority_key"],
                "priority_label": item["priority_label"],
                "target_block": item["target_block"],
            }
        )

    critical_commercial_pages = int(commercial_summary.get("critical_pages") or 0)
    warning_commercial_pages = int(commercial_summary.get("warning_pages") or 0)
    total_pages = int(commercial_summary.get("pages_total") or 0)
    if total_pages > 0 and (critical_commercial_pages > 0 or warning_commercial_pages > 0):
        priority_key = "urgent" if critical_commercial_pages > 0 else "important"
        plan.append(
            {
                "title": "Недостаточная коммерческая готовность страниц",
                "why_it_matters": "Страницы могут не доводить посетителя до заявки из-за слабых конверсионных элементов.",
                "pages_affected": critical_commercial_pages + warning_commercial_pages,
                "priority_key": priority_key,
                "priority_label": get_priority_label(priority_key),
                "target_block": "Коммерческий SEO-аудит страницы",
            }
        )

    if not bool(audit.has_robots_txt):
        plan.append(
            {
                "title": "Не найден robots.txt",
                "why_it_matters": "Поисковым системам сложнее правильно обходить сайт.",
                "pages_affected": int(audit.pages_count or 0),
                "priority_key": "urgent",
                "priority_label": get_priority_label("urgent"),
                "target_block": "Индексация",
            }
        )
    if not bool(audit.has_sitemap_xml):
        plan.append(
            {
                "title": "Не найден sitemap.xml",
                "why_it_matters": "Часть страниц может индексироваться хуже, чем должна.",
                "pages_affected": int(audit.pages_count or 0),
                "priority_key": "urgent",
                "priority_label": get_priority_label("urgent"),
                "target_block": "Индексация",
            }
        )

    deduplicated: dict[str, dict] = {}
    for item in plan:
        key = f"{item['title']}|{item['target_block']}"
        if key not in deduplicated:
            deduplicated[key] = item
            continue
        if int(item.get("pages_affected") or 0) > int(deduplicated[key].get("pages_affected") or 0):
            deduplicated[key] = item

    rows = list(deduplicated.values())
    rows.sort(
        key=lambda item: (
            PRIORITY_SORT_WEIGHT.get(item["priority_key"], 0),
            int(item.get("pages_affected") or 0),
        ),
        reverse=True,
    )
    return rows[:7]


def _bool_state_transition(previous: bool, current: bool) -> str:
    if previous and current:
        return "without_changes"
    if previous and not current:
        return "missing_now"
    if not previous and current:
        return "appeared"
    return "without_changes"


def build_audit_comparison(
    *,
    current_audit: SiteSEOAudit,
    previous_audit: SiteSEOAudit,
) -> dict[str, object]:
    current_breakdown = calculate_audit_score_breakdown(current_audit)
    previous_breakdown = calculate_audit_score_breakdown(previous_audit)

    current_issues = set(
        SEOIssue.objects.filter(page__audit=current_audit)
        .select_related("page")
        .values_list("issue_type", "page__url")
    )
    previous_issues = set(
        SEOIssue.objects.filter(page__audit=previous_audit)
        .select_related("page")
        .values_list("issue_type", "page__url")
    )
    new_issues = current_issues - previous_issues
    fixed_issues = previous_issues - current_issues

    score_delta = int(current_breakdown["score"]) - int(previous_breakdown["score"])
    if score_delta > 2 and len(new_issues) <= len(fixed_issues):
        trend = "better"
        trend_label = "Стало лучше"
    elif score_delta < -2 and len(new_issues) > len(fixed_issues):
        trend = "worse"
        trend_label = "Появились новые проблемы"
    else:
        trend = "stable"
        trend_label = "Без заметных изменений"

    robots_transition = _bool_state_transition(bool(previous_audit.has_robots_txt), bool(current_audit.has_robots_txt))
    sitemap_transition = _bool_state_transition(bool(previous_audit.has_sitemap_xml), bool(current_audit.has_sitemap_xml))

    return {
        "has_data": True,
        "trend": trend,
        "trend_label": trend_label,
        "current_audit_id": current_audit.id,
        "previous_audit_id": previous_audit.id,
        "score": {
            "before": int(previous_breakdown["score"]),
            "after": int(current_breakdown["score"]),
            "delta": score_delta,
        },
        "issues": {
            "high": {
                "before": int(previous_breakdown["high_issues"]),
                "after": int(current_breakdown["high_issues"]),
                "delta": int(current_breakdown["high_issues"]) - int(previous_breakdown["high_issues"]),
            },
            "medium": {
                "before": int(previous_breakdown["medium_issues"]),
                "after": int(current_breakdown["medium_issues"]),
                "delta": int(current_breakdown["medium_issues"]) - int(previous_breakdown["medium_issues"]),
            },
            "low": {
                "before": int(previous_breakdown["low_issues"]),
                "after": int(current_breakdown["low_issues"]),
                "delta": int(current_breakdown["low_issues"]) - int(previous_breakdown["low_issues"]),
            },
        },
        "speed_pages": {
            "before": int(previous_audit.pages_with_speed_issues or 0),
            "after": int(current_audit.pages_with_speed_issues or 0),
            "delta": int(current_audit.pages_with_speed_issues or 0) - int(previous_audit.pages_with_speed_issues or 0),
        },
        "indexing_pages": {
            "before": int(previous_audit.pages_with_indexing_issues or 0),
            "after": int(current_audit.pages_with_indexing_issues or 0),
            "delta": int(current_audit.pages_with_indexing_issues or 0)
            - int(previous_audit.pages_with_indexing_issues or 0),
        },
        "robots_txt": {
            "before": bool(previous_audit.has_robots_txt),
            "after": bool(current_audit.has_robots_txt),
            "status": robots_transition,
        },
        "sitemap_xml": {
            "before": bool(previous_audit.has_sitemap_xml),
            "after": bool(current_audit.has_sitemap_xml),
            "status": sitemap_transition,
        },
        "new_issues_count": len(new_issues),
        "fixed_issues_count": len(fixed_issues),
        "new_issues": [
            {"issue_type": item[0], "issue_title": get_issue_title(item[0]), "page_url": item[1]}
            for item in sorted(new_issues)
        ][:25],
        "fixed_issues": [
            {"issue_type": item[0], "issue_title": get_issue_title(item[0]), "page_url": item[1]}
            for item in sorted(fixed_issues)
        ][:25],
    }
