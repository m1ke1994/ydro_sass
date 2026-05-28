from io import BytesIO
from pathlib import Path

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

FONT_REGULAR = "TrackNodeRegular"
FONT_BOLD = "TrackNodeBold"

FONT_REGULAR_CANDIDATES = [
    Path(settings.BASE_DIR) / "static" / "fonts" / "DejaVuSans.ttf",
    Path(settings.BASE_DIR) / "static" / "fonts" / "Arial.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
FONT_BOLD_CANDIDATES = [
    Path(settings.BASE_DIR) / "static" / "fonts" / "DejaVuSans-Bold.ttf",
    Path(settings.BASE_DIR) / "static" / "fonts" / "Arial Bold.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
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
            "Unicode font not found for PDF generation. Expected one of: "
            + ", ".join(str(path) for path in FONT_REGULAR_CANDIDATES)
        )

    bold_path = _first_existing(FONT_BOLD_CANDIDATES) or regular_path
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular_path)))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold_path)))


def _sanitize_text(value):
    if value is None:
        return "-"
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return "-"
    # Убираем управляющие символы, которые могут ломать верстку PDF.
    return "".join(ch for ch in text if ch == "\n" or ord(ch) >= 32)


def _format_duration(seconds):
    total_seconds = max(0, int(float(seconds or 0)))
    if total_seconds < 60:
        return f"{total_seconds} сек"
    if total_seconds < 3600:
        minutes = total_seconds // 60
        rest_seconds = total_seconds % 60
        return f"{minutes} мин {rest_seconds} сек"
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours} ч {minutes} мин"


def _styles():
    styles = getSampleStyleSheet()
    if "tn_title" not in styles:
        styles.add(
            ParagraphStyle(
                name="tn_title",
                parent=styles["Title"],
                fontName=FONT_BOLD,
                fontSize=20,
                leading=25,
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
                spaceBefore=8,
                spaceAfter=6,
            )
        )
        styles.add(
            ParagraphStyle(
                name="tn_body",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=9,
                leading=13,
                textColor=COLOR_TEXT,
            )
        )
        styles.add(
            ParagraphStyle(
                name="tn_cell",
                parent=styles["BodyText"],
                fontName=FONT_REGULAR,
                fontSize=8.5,
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
        styles.add(
            ParagraphStyle(
                name="tn_cell_right",
                parent=styles["tn_cell"],
                alignment=2,
            )
        )
        styles.add(
            ParagraphStyle(
                name="tn_cell_header_right",
                parent=styles["tn_cell_header"],
                alignment=2,
            )
        )
    return {
        "title": styles["tn_title"],
        "subtitle": styles["tn_subtitle"],
        "section": styles["tn_section"],
        "body": styles["tn_body"],
        "cell": styles["tn_cell"],
        "cell_header": styles["tn_cell_header"],
        "cell_right": styles["tn_cell_right"],
        "cell_header_right": styles["tn_cell_header_right"],
    }


def _to_paragraph_cell(value, *, numeric=False, header=False):
    styles = _styles()
    text = _sanitize_text(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if header and numeric:
        style = styles["cell_header_right"]
    elif header:
        style = styles["cell_header"]
    elif numeric:
        style = styles["cell_right"]
    else:
        style = styles["cell"]
    return Paragraph(text, style)


def _render_table(elements, title, headers, rows, widths, *, numeric_cols=None, rows_per_page=26):
    numeric_cols = set(numeric_cols or [])
    elements.append(Paragraph(_sanitize_text(title), _styles()["section"]))

    if not rows:
        rows = [["Данных за выбранный период нет"] + [""] * (len(headers) - 1)]

    start = 0
    while start < len(rows):
        chunk = rows[start : start + rows_per_page]
        table_rows = [
            [_to_paragraph_cell(h, numeric=(idx in numeric_cols), header=True) for idx, h in enumerate(headers)]
        ]
        for row in chunk:
            table_rows.append(
                [_to_paragraph_cell(cell, numeric=(idx in numeric_cols), header=False) for idx, cell in enumerate(row)]
            )

        table = Table(table_rows, colWidths=widths, repeatRows=1)
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
            elements.append(Paragraph(f"{_sanitize_text(title)} (продолжение)", _styles()["section"]))


def _top_name_and_count(rows):
    if not rows:
        return "Нет данных", 0
    top = max(rows, key=lambda row: int(row.get("count") or 0))
    return _sanitize_text(top.get("name") or "Нет данных"), int(top.get("count") or 0)


def _draw_page_footer(canvas, doc):
    canvas.saveState()
    page_width, _ = A4
    footer_y = 8 * mm
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(doc.leftMargin, footer_y + 6 * mm, page_width - doc.rightMargin, footer_y + 6 * mm)

    canvas.setFont(FONT_REGULAR, 8)
    canvas.setFillColor(COLOR_TEXT)
    canvas.drawString(doc.leftMargin, footer_y + 1.5 * mm, "TrackNode Analytics")
    canvas.drawRightString(page_width - doc.rightMargin, footer_y + 1.5 * mm, f"Стр. {canvas.getPageNumber()}")
    canvas.restoreState()


def build_pdf_for_client(*, client, user):
    date_from, date_to = default_period_days(days=14)
    report = build_full_report(client=client, date_from=date_from, date_to=date_to)
    summary = report["summary"]

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
        title="TrackNode Analytics - Отчет по эффективности",
    )

    styles = _styles()
    period_text = f"{report['period']['date_from']:%d.%m.%Y} - {report['period']['date_to']:%d.%m.%Y}"
    client_name = _sanitize_text(getattr(client, "name", "")) if getattr(client, "name", "") else "Не указан"
    owner_email = _sanitize_text(getattr(user, "email", "-"))

    elements = [
        Paragraph("TrackNode Analytics", styles["title"]),
        Paragraph("Управленческий отчет по эффективности", styles["subtitle"]),
        Paragraph(f"Период отчета: {period_text}", styles["subtitle"]),
        Paragraph(f"Клиент: {client_name}", styles["subtitle"]),
        Paragraph(f"Ответственный: {owner_email}", styles["subtitle"]),
        Paragraph(f"Дата формирования: {generated_at:%d.%m.%Y %H:%M}", styles["subtitle"]),
        Spacer(1, 10),
    ]

    _render_table(
        elements,
        "Раздел 1. Ключевые метрики",
        ["Метрика", "Значение"],
        [
            ["Визиты", str(summary["visits"])],
            ["Уникальные пользователи", str(summary["unique_users"])],
            ["Отправки форм", str(summary["forms"])],
            ["Заявки", str(summary["leads"])],
            ["Конверсия", f"{summary['conversion']:.2f}%"],
        ],
        widths=[104 * mm, 72 * mm],
        numeric_cols={1},
        rows_per_page=32,
    )

    top_device_name, top_device_count = _top_name_and_count(report["devices_distribution"]["devices"])
    top_os_name, top_os_count = _top_name_and_count(report["devices_distribution"]["os"])
    top_browser_name, top_browser_count = _top_name_and_count(report["devices_distribution"]["browsers"])
    _render_table(
        elements,
        "Раздел 2. Сводка по устройствам",
        ["Категория", "Лидер", "Количество"],
        [
            ["Тип устройства", top_device_name, str(top_device_count)],
            ["Операционная система", top_os_name, str(top_os_count)],
            ["Браузер", top_browser_name, str(top_browser_count)],
        ],
        widths=[52 * mm, 94 * mm, 30 * mm],
        numeric_cols={2},
        rows_per_page=32,
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
    _render_table(
        elements,
        "Раздел 3. Динамика по дням",
        ["Дата", "Визиты", "Уникальные", "Формы", "Заявки", "Конверсия"],
        daily_rows,
        widths=[29 * mm, 28 * mm, 30 * mm, 26 * mm, 26 * mm, 37 * mm],
        numeric_cols={1, 2, 3, 4, 5},
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
    _render_table(
        elements,
        "Раздел 4. Конверсия по страницам",
        ["Страница", "Визиты", "Заявки", "Конверсия"],
        page_rows,
        widths=[106 * mm, 24 * mm, 24 * mm, 26 * mm],
        numeric_cols={1, 2, 3},
        rows_per_page=24,
    )

    click_rows = []
    for row in report["top_clicks"]:
        element_text = row["element_text"] or row["element_id"] or row["element_class"] or "-"
        click_rows.append(
            [
                _sanitize_text(row["page_pathname"]),
                _sanitize_text(element_text),
                str(row["count"]),
                f"{row['percent_of_total']:.2f}%",
            ]
        )
    _render_table(
        elements,
        "Раздел 5. Топ кликов",
        ["Страница", "Элемент", "Клики", "% от всех кликов"],
        click_rows,
        widths=[74 * mm, 74 * mm, 16 * mm, 16 * mm],
        numeric_cols={2, 3},
        rows_per_page=24,
    )

    source_rows = [[_sanitize_text(row["source"]), str(row["visits"]), f"{row['percent_of_total']:.2f}%"] for row in report["sources"]]
    _render_table(
        elements,
        "Раздел 6. Топ источников",
        ["Источник", "Визиты", "% от общего"],
        source_rows,
        widths=[116 * mm, 30 * mm, 34 * mm],
        numeric_cols={1, 2},
        rows_per_page=28,
    )

    devices_rows = [[_sanitize_text(row["name"]), str(row["count"]), f"{row['percent']:.2f}%"] for row in report["devices_distribution"]["devices"]]
    _render_table(
        elements,
        "Раздел 7. Распределение устройств - Тип устройства",
        ["Тип устройства", "Количество", "%"],
        devices_rows,
        widths=[112 * mm, 30 * mm, 34 * mm],
        numeric_cols={1, 2},
        rows_per_page=28,
    )

    os_rows = [[_sanitize_text(row["name"]), str(row["count"]), f"{row['percent']:.2f}%"] for row in report["devices_distribution"]["os"]]
    _render_table(
        elements,
        "Раздел 8. Распределение устройств - Операционная система",
        ["Операционная система", "Количество", "%"],
        os_rows,
        widths=[112 * mm, 30 * mm, 34 * mm],
        numeric_cols={1, 2},
        rows_per_page=28,
    )

    browser_rows = [[_sanitize_text(row["name"]), str(row["count"]), f"{row['percent']:.2f}%"] for row in report["devices_distribution"]["browsers"]]
    _render_table(
        elements,
        "Раздел 9. Распределение устройств - Браузер",
        ["Браузер", "Количество", "%"],
        browser_rows,
        widths=[112 * mm, 30 * mm, 34 * mm],
        numeric_cols={1, 2},
        rows_per_page=28,
    )

    notifications_sent = int(summary.get("notifications_sent") or 0)
    notification_rows = [[f"Всего отправлено уведомлений: {notifications_sent}"]]
    _render_table(
        elements,
        "Раздел 10. Заявки (уведомления)",
        ["Показатель"],
        notification_rows,
        widths=[176 * mm],
        rows_per_page=32,
    )

    engagement = report.get("engagement") or {}
    total_time_on_site_seconds = int(engagement.get("total_time_on_site_seconds") or 0)
    avg_visit_duration_seconds = float(engagement.get("avg_visit_duration_seconds") or 0)
    engagement_summary_rows = [
        ["Общее время на сайте", _format_duration(total_time_on_site_seconds)],
        ["Среднее время визита", _format_duration(avg_visit_duration_seconds)],
    ]
    _render_table(
        elements,
        "Раздел 11. Вовлечённость",
        ["Показатель", "Значение"],
        engagement_summary_rows,
        widths=[104 * mm, 72 * mm],
        rows_per_page=32,
    )

    top_time_pages_rows = [
        [
            _sanitize_text(row.get("pathname") or "/"),
            _format_duration(row.get("avg_duration_seconds") or 0),
            _format_duration(row.get("total_duration_seconds") or 0),
            str(int(row.get("visits_count") or 0)),
        ]
        for row in (engagement.get("pages") or [])[:5]
    ]
    _render_table(
        elements,
        "Раздел 12. Топ-5 страниц по времени",
        ["Страница", "Среднее время", "Общее время", "Посещения"],
        top_time_pages_rows,
        widths=[86 * mm, 30 * mm, 30 * mm, 30 * mm],
        rows_per_page=24,
    )

    doc.build(elements, onFirstPage=_draw_page_footer, onLaterPages=_draw_page_footer)
    return buffer.getvalue(), filename
