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
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from analytics_app.services.metrics import default_period_days
from analytics_app.services.report_builder import build_full_report
from seo_audit.models import SEOIssue, SiteSEOAudit

FONT_REGULAR = "TrackNodeRegular"
FONT_BOLD = "TrackNodeBold"

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
COLOR_ACCENT = colors.HexColor("#EAF1FF")
COLOR_BORDER = colors.HexColor("#CBD5E1")
COLOR_TEXT = colors.HexColor("#1F2937")


def _first_existing(paths):
    for path in paths:
        if path.exists():
            return path
    return None


def _ensure_fonts_registered():
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


def _sanitize_text(value: Any, fallback: str = "—") -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return fallback
    return "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)


def _styles():
    styles = getSampleStyleSheet()
    if "tn_title" in styles:
        return styles

    styles.add(
        ParagraphStyle(
            name="tn_title",
            parent=styles["Title"],
            fontName=FONT_BOLD,
            fontSize=19,
            leading=24,
            textColor=COLOR_PRIMARY,
            alignment=1,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="tn_subtitle",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=14,
            textColor=COLOR_TEXT,
            alignment=1,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="tn_section",
            parent=styles["Heading2"],
            fontName=FONT_BOLD,
            fontSize=12,
            leading=16,
            textColor=COLOR_PRIMARY,
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="tn_cell",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=8.7,
            leading=11,
            textColor=COLOR_TEXT,
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            name="tn_cell_header",
            parent=styles["BodyText"],
            fontName=FONT_BOLD,
            fontSize=8.7,
            leading=11,
            textColor=COLOR_PRIMARY,
            wordWrap="CJK",
        )
    )
    return styles


def _paragraph(text: Any, style_name: str):
    styles = _styles()
    escaped = _sanitize_text(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(escaped, styles[style_name])


def _table(elements, title: str, headers: list[str], rows: list[list[Any]], widths: list[float], rows_per_page: int = 26):
    elements.append(_paragraph(title, "tn_section"))
    if not rows:
        rows = [["Данные отсутствуют"] + [""] * (len(headers) - 1)]

    start = 0
    while start < len(rows):
        chunk = rows[start : start + rows_per_page]
        matrix = [[_paragraph(item, "tn_cell_header") for item in headers]]
        for row in chunk:
            matrix.append([_paragraph(item, "tn_cell") for item in row])

        table = Table(matrix, colWidths=widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
                    ("GRID", (0, 0), (-1, -1), 0.35, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFBFF")]),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 8))
        start += rows_per_page
        if start < len(rows):
            elements.append(PageBreak())


def build_pdf_for_client(*, client, user, date_from=None, date_to=None):
    if date_from is None or date_to is None:
        date_from, date_to = default_period_days(days=14)

    report = build_full_report(client=client, date_from=date_from, date_to=date_to)
    summary = report["summary"]
    seo_latest = SiteSEOAudit.objects.filter(client=client).order_by("-created_at").first()

    _ensure_fonts_registered()

    generated_at = timezone.localtime(timezone.now())
    filename = f"tracknode-full-report-client-{client.id}-{timezone.localdate():%Y%m%d}.pdf"
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=15 * mm,
        bottomMargin=16 * mm,
        title="Yadro Mini CRM — PDF отчёт",
    )

    period_text = f"{date_from:%d.%m.%Y} — {date_to:%d.%m.%Y}"
    client_name = _sanitize_text(getattr(client, "name", ""), "Не указано")
    owner_email = _sanitize_text(getattr(user, "email", "-"), "-")

    elements = [
        _paragraph("Yadro Mini CRM", "tn_title"),
        _paragraph("Ежедневный аналитический отчёт", "tn_subtitle"),
        _paragraph(f"Период: {period_text}", "tn_subtitle"),
        _paragraph(f"Сайт: {client_name}", "tn_subtitle"),
        _paragraph(f"Владелец: {owner_email}", "tn_subtitle"),
        _paragraph(f"Дата формирования: {generated_at:%d.%m.%Y %H:%M}", "tn_subtitle"),
        Spacer(1, 10),
    ]

    _table(
        elements,
        "1. Ключевые показатели",
        ["Метрика", "Значение"],
        [
            ["Визиты", str(summary["visits"])],
            ["Уникальные пользователи", str(summary["unique_users"])],
            ["Отправки форм", str(summary["forms"])],
            ["Заявки", str(summary["leads"])],
            ["Конверсия", f"{summary['conversion']:.2f}%"],
        ],
        widths=[104 * mm, 72 * mm],
        rows_per_page=30,
    )

    daily_rows = [
        [
            row["day"].strftime("%d.%m.%Y"),
            str(row["visits"]),
            str(row["unique_users"]),
            str(row["forms"]),
            str(row["leads"]),
            f"{row['conversion']:.2f}%",
        ]
        for row in report["daily_stats"]
    ]
    _table(
        elements,
        "2. Динамика по дням",
        ["Дата", "Визиты", "Уникальные", "Формы", "Заявки", "Конверсия"],
        daily_rows,
        widths=[29 * mm, 28 * mm, 30 * mm, 26 * mm, 26 * mm, 37 * mm],
        rows_per_page=24,
    )

    page_rows = [
        [
            _sanitize_text(row["pathname"]),
            str(row["visits"]),
            str(row["leads"]),
            f"{row['conversion_pct']:.2f}%",
        ]
        for row in report["page_conversion"]
    ]
    _table(
        elements,
        "3. Конверсия по страницам",
        ["Страница", "Визиты", "Заявки", "Конверсия"],
        page_rows,
        widths=[106 * mm, 24 * mm, 24 * mm, 26 * mm],
        rows_per_page=24,
    )

    seo_rows = []
    if seo_latest:
        seo_rows.append(["Статус аудита", seo_latest.status])
        seo_rows.append(["SEO Score", str(seo_latest.seo_score)])
        seo_rows.append(["Проверено страниц", str(seo_latest.pages_count)])
        seo_rows.append(["Ошибок в скорости", str(seo_latest.pages_with_speed_issues)])
        seo_rows.append(["Ошибок индексации", str(seo_latest.pages_with_indexing_issues)])
    _table(
        elements,
        "4. SEO-аудит (последний запуск)",
        ["Показатель", "Значение"],
        seo_rows,
        widths=[104 * mm, 72 * mm],
        rows_per_page=30,
    )

    seo_issue_rows = []
    seo_recommendation_rows = []
    if seo_latest:
        issues_qs = (
            SEOIssue.objects.filter(page__audit=seo_latest)
            .select_related("page")
            .order_by("id")
        )
        for issue in list(issues_qs[:20]):
            seo_issue_rows.append(
                [
                    _sanitize_text(issue.severity),
                    _sanitize_text(issue.issue_type),
                    _sanitize_text(getattr(issue.page, "url", "")),
                ]
            )

        seen = set()
        for issue in issues_qs:
            recommendation = _sanitize_text(issue.recommendation, "")
            if not recommendation or recommendation in seen:
                continue
            seen.add(recommendation)
            seo_recommendation_rows.append([recommendation])
            if len(seo_recommendation_rows) >= 15:
                break

    _table(
        elements,
        "5. SEO-проблемы (топ)",
        ["Серьёзность", "Код проблемы", "Страница"],
        seo_issue_rows,
        widths=[24 * mm, 52 * mm, 100 * mm],
        rows_per_page=20,
    )

    _table(
        elements,
        "6. Рекомендации по SEO",
        ["Рекомендация"],
        seo_recommendation_rows,
        widths=[176 * mm],
        rows_per_page=25,
    )

    doc.build(elements)
    return buffer.getvalue(), filename
