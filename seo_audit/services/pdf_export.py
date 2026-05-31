# -*- coding: utf-8 -*-
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_REGULAR = "SeoAuditPdfRegular"
FONT_BOLD = "SeoAuditPdfBold"

FONT_REGULAR_CANDIDATES = [
    Path(settings.BASE_DIR) / "static" / "fonts" / "DejaVuSans.ttf",
    Path(settings.BASE_DIR) / "static" / "fonts" / "Arial.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]
FONT_BOLD_CANDIDATES = [
    Path(settings.BASE_DIR) / "static" / "fonts" / "DejaVuSans-Bold.ttf",
    Path(settings.BASE_DIR) / "static" / "fonts" / "Arial Bold.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    Path("C:/Windows/Fonts/arialbd.ttf"),
]

COLOR_PRIMARY = colors.HexColor("#1E3A8A")
COLOR_BORDER = colors.HexColor("#CBD5E1")
COLOR_TEXT = colors.HexColor("#111827")
COLOR_ROW_ALT = colors.HexColor("#F8FAFC")
COLOR_ROW_HEAD = colors.HexColor("#EAF1FF")


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _ensure_fonts_registered() -> None:
    try:
        pdfmetrics.getFont(FONT_REGULAR)
        pdfmetrics.getFont(FONT_BOLD)
        return
    except KeyError:
        pass

    regular_path = _first_existing(FONT_REGULAR_CANDIDATES)
    if not regular_path:
        raise FileNotFoundError(
            "Не найден шрифт для PDF с поддержкой кириллицы. Ожидался один из: "
            + ", ".join(str(path) for path in FONT_REGULAR_CANDIDATES)
        )

    bold_path = _first_existing(FONT_BOLD_CANDIDATES) or regular_path
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular_path)))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold_path)))


def _styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    if "seo_pdf_title" not in styles:
        styles.add(
            ParagraphStyle(
                name="seo_pdf_title",
                parent=styles["Title"],
                fontName=FONT_BOLD,
                fontSize=18,
                leading=23,
                textColor=COLOR_PRIMARY,
                alignment=1,
                spaceAfter=3,
            )
        )
        styles.add(
            ParagraphStyle(
                name="seo_pdf_subtitle",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=9,
                leading=13,
                textColor=COLOR_TEXT,
                alignment=1,
                spaceAfter=2,
            )
        )
        styles.add(
            ParagraphStyle(
                name="seo_pdf_h2",
                parent=styles["Heading2"],
                fontName=FONT_BOLD,
                fontSize=11,
                leading=15,
                textColor=COLOR_PRIMARY,
                spaceBefore=7,
                spaceAfter=4,
            )
        )
        styles.add(
            ParagraphStyle(
                name="seo_pdf_body",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=9,
                leading=13,
                textColor=COLOR_TEXT,
            )
        )
        styles.add(
            ParagraphStyle(
                name="seo_pdf_cell",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=8.4,
                leading=10.8,
                textColor=COLOR_TEXT,
                wordWrap="CJK",
            )
        )
        styles.add(
            ParagraphStyle(
                name="seo_pdf_cell_head",
                parent=styles["BodyText"],
                fontName=FONT_BOLD,
                fontSize=8.4,
                leading=10.8,
                textColor=COLOR_PRIMARY,
                wordWrap="CJK",
            )
        )
    return {
        "title": styles["seo_pdf_title"],
        "subtitle": styles["seo_pdf_subtitle"],
        "h2": styles["seo_pdf_h2"],
        "body": styles["seo_pdf_body"],
        "cell": styles["seo_pdf_cell"],
        "cell_head": styles["seo_pdf_cell_head"],
    }


def _sanitize_text(value: Any, *, fallback: str = "—") -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return fallback
    return "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)


def _escape_text(value: Any, *, fallback: str = "—") -> str:
    text = _sanitize_text(value, fallback=fallback)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _p(text: Any, style_key: str, *, fallback: str = "—") -> Paragraph:
    return Paragraph(_escape_text(text, fallback=fallback), _styles()[style_key])


def _render_table(
    elements: list,
    *,
    title: str,
    headers: list[str],
    rows: list[list[Any]],
    col_widths: list[float],
    rows_per_chunk: int = 26,
) -> None:
    elements.append(_p(title, "h2"))
    if not rows:
        rows = [["Данные отсутствуют"] + [""] * max(0, len(headers) - 1)]

    start = 0
    while start < len(rows):
        chunk = rows[start : start + rows_per_chunk]
        table_rows = [[_p(item, "cell_head") for item in headers]]
        for row in chunk:
            table_rows.append([_p(value, "cell") for value in row])

        table = Table(table_rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_ROW_HEAD),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_ROW_ALT]),
                    ("GRID", (0, 0), (-1, -1), 0.3, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 7))
        start += rows_per_chunk


def _build_pdf_filename(domain: str | None) -> str:
    raw_domain = str(domain or "").strip().lower() or "site"
    safe_domain = "".join(ch if ch.isalnum() or ch in ("-", ".") else "-" for ch in raw_domain).strip("-.")
    date_part = timezone.localdate().strftime("%Y%m%d")
    return f"seo-audit-{safe_domain or 'site'}-{date_part}.pdf"


def build_seo_audit_pdf(*, detail_payload: dict[str, Any], comparison: dict[str, Any] | None = None) -> tuple[bytes, str]:
    _ensure_fonts_registered()

    domain = _sanitize_text(detail_payload.get("domain"), fallback="Не указан")
    generated_at = timezone.localtime(timezone.now())
    filename = _build_pdf_filename(detail_payload.get("domain"))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"SEO-аудит: {domain}",
    )
    elements: list = [
        _p("Отчёт SEO-аудита сайта", "title"),
        _p(f"Домен: {domain}", "subtitle"),
        _p(f"Дата формирования: {generated_at:%d.%m.%Y %H:%M}", "subtitle"),
        Spacer(1, 8),
    ]

    score = int(detail_payload.get("score") or detail_payload.get("seo_score") or 0)
    pages_count = int(detail_payload.get("pages_count") or 0)
    high = int(detail_payload.get("breakdown", {}).get("high_issues") or 0)
    medium = int(detail_payload.get("breakdown", {}).get("medium_issues") or 0)
    low = int(detail_payload.get("breakdown", {}).get("low_issues") or 0)

    summary_rows = [
        ["SEO Score", score],
        ["Проверено страниц", pages_count],
        ["Критичных проблем", high],
        ["Средних проблем", medium],
        ["Низких проблем", low],
        ["robots.txt", "Да" if bool(detail_payload.get("has_robots_txt")) else "Нет"],
        ["sitemap.xml", "Да" if bool(detail_payload.get("has_sitemap_xml")) else "Нет"],
    ]
    _render_table(
        elements,
        title="Сводка",
        headers=["Показатель", "Значение"],
        rows=summary_rows,
        col_widths=[108 * mm, 68 * mm],
        rows_per_chunk=24,
    )

    if comparison and bool(comparison.get("has_data")):
        score_delta = int(comparison.get("score", {}).get("delta") or 0)
        compare_rows = [
            ["Тренд", _sanitize_text(comparison.get("trend_label"), fallback="Без изменений")],
            ["Изменение score", f"{score_delta:+d}"],
            ["Новых проблем", int(comparison.get("new_issues_count") or 0)],
            ["Исправленных проблем", int(comparison.get("fixed_issues_count") or 0)],
        ]
        _render_table(
            elements,
            title="Сравнение с предыдущим аудитом",
            headers=["Показатель", "Значение"],
            rows=compare_rows,
            col_widths=[108 * mm, 68 * mm],
            rows_per_chunk=24,
        )

    pages_rows = []
    for page in (detail_payload.get("pages") or [])[:60]:
        if not isinstance(page, dict):
            continue
        pages_rows.append(
            [
                _sanitize_text(page.get("url"), fallback="—"),
                int(page.get("status_code") or 0),
                int(page.get("ttfb_ms") or 0),
                int(page.get("performance_score") or 0),
            ]
        )
    _render_table(
        elements,
        title="Проверенные страницы",
        headers=["URL", "HTTP", "TTFB, мс", "Performance"],
        rows=pages_rows,
        col_widths=[112 * mm, 18 * mm, 24 * mm, 22 * mm],
        rows_per_chunk=20,
    )

    issues_rows = []
    for issue in (detail_payload.get("errors") or [])[:120]:
        if not isinstance(issue, dict):
            continue
        issues_rows.append(
            [
                _sanitize_text(issue.get("severity"), fallback="—"),
                _sanitize_text(issue.get("issue_title"), fallback="SEO-замечание"),
                _sanitize_text(issue.get("page_url"), fallback="—"),
                _sanitize_text(issue.get("recommendation"), fallback="—"),
            ]
        )
    _render_table(
        elements,
        title="SEO-проблемы",
        headers=["Серьёзность", "Проблема", "Страница", "Рекомендация"],
        rows=issues_rows,
        col_widths=[22 * mm, 48 * mm, 50 * mm, 56 * mm],
        rows_per_chunk=18,
    )

    recommendations_payload = detail_payload.get("recommendations")
    recommendations_items = []
    if isinstance(recommendations_payload, dict):
        recommendations_items = recommendations_payload.get("items") or []
    recommendations_rows = [
        [idx, _sanitize_text(item, fallback="—")]
        for idx, item in enumerate(recommendations_items[:20], start=1)
        if _sanitize_text(item, fallback="") != ""
    ]
    _render_table(
        elements,
        title="Рекомендации",
        headers=["#", "Что сделать"],
        rows=recommendations_rows,
        col_widths=[12 * mm, 164 * mm],
        rows_per_chunk=24,
    )

    doc.build(elements)
    payload = buffer.getvalue()
    buffer.close()
    return payload, filename
