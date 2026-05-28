# -*- coding: utf-8 -*-
from __future__ import annotations

ISSUE_MESSAGES = {
    "missing_title": {
        "title": "Отсутствует заголовок Title.",
        "recommendation": "Добавьте уникальный Title длиной 50–60 символов с ключевой темой страницы.",
    },
    "bad_title_length": {
        "title": "Некорректная длина заголовка Title.",
        "recommendation": "Скорректируйте длину Title до рекомендуемого диапазона 50–60 символов.",
    },
    "title_too_short": {
        "title": "Слишком короткий Title.",
        "recommendation": "Увеличьте длину Title минимум до 15 символов и уточните смысл страницы.",
    },
    "title_too_long": {
        "title": "Слишком длинный Title.",
        "recommendation": "Сократите Title до 65 символов, чтобы избежать обрезки в поисковой выдаче.",
    },
    "missing_description": {
        "title": "Нет описания страницы для поиска (meta description).",
        "recommendation": "Добавьте короткое описание страницы на 120–160 символов. Это поможет пользователю понять смысл страницы ещё в выдаче.",
    },
    "description_too_short": {
        "title": "Описание страницы в поиске слишком короткое.",
        "recommendation": "Сделайте описание более информативным: минимум 50 символов с пользой для пользователя.",
    },
    "description_too_long": {
        "title": "Описание страницы в поиске слишком длинное.",
        "recommendation": "Сократите описание до 160 символов, чтобы оно не обрезалось в поисковой выдаче.",
    },
    "duplicate_title": {
        "title": "Обнаружен дублирующийся Title.",
        "recommendation": "Сделайте Title уникальным для каждой страницы.",
    },
    "missing_h1": {
        "title": "Нет главного заголовка страницы (H1).",
        "recommendation": "Добавьте один понятный главный заголовок (H1), чтобы поисковые системы и пользователи быстрее понимали тему страницы.",
    },
    "multiple_h1": {
        "title": "На странице несколько главных заголовков (H1).",
        "recommendation": "Оставьте один главный заголовок (H1), а для остальных блоков используйте подзаголовки H2–H6.",
    },
    "long_h1": {
        "title": "Главный заголовок страницы (H1) слишком длинный.",
        "recommendation": "Сократите H1 до 70 символов, чтобы заголовок оставался понятным с первого взгляда.",
    },
    "heading_hierarchy_gap": {
        "title": "Нарушена иерархия заголовков.",
        "recommendation": "Используйте последовательную структуру заголовков без пропусков уровней.",
    },
    "low_word_count": {
        "title": "Недостаточно текстового контента.",
        "recommendation": "Добавьте полезный текстовый контент, как правило от 300 слов.",
    },
    "image_missing_alt": {
        "title": "У части изображений нет текстового описания (alt).",
        "recommendation": "Добавьте короткие описания (alt) к важным изображениям. Это помогает поисковым системам понимать содержимое картинок.",
    },
    "image_empty_alt": {
        "title": "У части изображений пустое описание (alt).",
        "recommendation": "Заполните alt там, где изображение несёт смысл. Для декоративных изображений можно оставить пустое значение.",
    },
    "bad_status": {
        "title": "Некорректный HTTP-статус страницы.",
        "recommendation": "Проверьте URL и серверную обработку. Страница должна отдавать HTTP 200.",
    },
    "network_error": {
        "title": "Сетевая ошибка при загрузке страницы.",
        "recommendation": "Проверьте доступность сайта, DNS, SSL и сетевые ограничения.",
    },
    "redirect": {
        "title": "Обнаружено перенаправление страницы (redirect).",
        "recommendation": "Используйте сразу конечный адрес страницы, чтобы сократить цепочки перенаправлений и ускорить загрузку.",
    },
    "slow_response": {
        "title": "Медленный ответ сервера.",
        "recommendation": "Ускорьте ответ сервера и включите кеширование. Это уменьшит задержку и снизит потери пользователей на загрузке.",
    },
    "large_page_size": {
        "title": "Размер страницы слишком большой.",
        "recommendation": "Уменьшите общий размер HTML и ресурсов страницы.",
    },
    "slow_ttfb": {
        "title": "Сервер долго начинает отдавать страницу (высокий TTFB).",
        "recommendation": "Проверьте тяжёлые запросы к базе, кеширование и серверные настройки, чтобы страница начинала загружаться быстрее.",
    },
    "large_html_size": {
        "title": "Слишком большой HTML-документ.",
        "recommendation": "Сократите объём HTML, удалите лишнюю разметку и дублирующийся контент.",
    },
    "too_many_js": {
        "title": "Слишком много JS-файлов.",
        "recommendation": "Сократите количество скриптов и используйте отложенную загрузку.",
    },
    "too_many_css": {
        "title": "Слишком много CSS-файлов.",
        "recommendation": "Объедините и оптимизируйте CSS, удалите неиспользуемые стили.",
    },
    "too_many_images": {
        "title": "Слишком много изображений.",
        "recommendation": "Сократите число изображений и включите lazy-loading.",
    },
    "heavy_js_payload": {
        "title": "Слишком тяжёлый JavaScript.",
        "recommendation": "Уменьшите размер JS-бандлов, включите code-splitting.",
    },
    "heavy_css_payload": {
        "title": "Слишком тяжёлый CSS.",
        "recommendation": "Минифицируйте и оптимизируйте CSS.",
    },
    "heavy_images_payload": {
        "title": "Слишком тяжёлые изображения.",
        "recommendation": "Сжимайте изображения, используйте WebP/AVIF и lazy-loading.",
    },
    "heavy_page_payload": {
        "title": "Слишком большой суммарный вес ресурсов.",
        "recommendation": "Оптимизируйте HTML, JS, CSS и изображения для снижения общего веса страницы.",
    },
    "missing_canonical": {
        "title": "Не указан основной адрес страницы (canonical).",
        "recommendation": "Укажите canonical, чтобы поисковая система понимала, какую версию страницы считать основной.",
    },
    "invalid_canonical": {
        "title": "Основной адрес страницы (canonical) указан с ошибкой.",
        "recommendation": "Исправьте canonical: используйте полный корректный URL с правильным доменом и протоколом.",
    },
    "canonical_conflict": {
        "title": "Настройки canonical и индексации противоречат друг другу.",
        "recommendation": "Приведите canonical и правила индексации (meta robots/noindex) к одному сценарию, чтобы убрать путаницу для поисковой системы.",
    },
    "page_noindex": {
        "title": "Страница закрыта от индексации (noindex).",
        "recommendation": "Если страница должна попадать в поиск, уберите noindex в мета-тегах или заголовках ответа.",
    },
    "page_nofollow": {
        "title": "На странице запрещён переход веса по ссылкам (nofollow).",
        "recommendation": "Проверьте, нужен ли nofollow. Если важно передавать вес по ссылкам, уберите это ограничение.",
    },
    "blocked_by_robots": {
        "title": "Страница заблокирована в robots.txt.",
        "recommendation": "Проверьте правила Disallow/Allow в robots.txt и откройте страницу, если она должна индексироваться.",
    },
    "sitemap_page_missing": {
        "title": "Страница не добавлена в карту сайта (sitemap.xml).",
        "recommendation": "Добавьте страницу в sitemap.xml, если она важна для поиска и должна индексироваться.",
    },
    "missing_meta_robots": {
        "title": "Не задано правило индексации страницы (meta robots).",
        "recommendation": "Добавьте meta robots, если нужно явно указать, можно ли индексировать страницу и переходить по её ссылкам.",
    },
    "missing_viewport": {
        "title": "Не задана адаптация под мобильные устройства (meta viewport).",
        "recommendation": "Добавьте meta viewport в `<head>`, чтобы страница корректно отображалась на телефонах и планшетах.",
    },
    "missing_charset": {
        "title": "Не задана кодировка страницы (meta charset).",
        "recommendation": "Добавьте `<meta charset=\"utf-8\">` в `<head>`, чтобы текст на русском отображался без искажений.",
    },
    "missing_robots_txt": {
        "title": "Не найден файл robots.txt.",
        "recommendation": "Создайте robots.txt в корне сайта и добавьте в него ссылку на sitemap.xml, чтобы упростить обход сайта поисковыми системами.",
    },
    "robots_disallow_all": {
        "title": "robots.txt запрещает обход всего сайта.",
        "recommendation": "Проверьте правило `Disallow: /` для `User-agent: *`. Сейчас поисковые системы не могут обходить страницы сайта.",
    },
    "robots_missing_sitemap": {
        "title": "В robots.txt нет ссылки на карту сайта (sitemap.xml).",
        "recommendation": "Добавьте строку `Sitemap:` с полным адресом sitemap.xml.",
    },
    "missing_sitemap": {
        "title": "Не найден файл sitemap.xml.",
        "recommendation": "Создайте sitemap.xml и добавьте в него важные индексируемые страницы.",
    },
    "bad_sitemap_status": {
        "title": "Файл sitemap.xml недоступен или отдает ошибку.",
        "recommendation": "Проверьте доступность sitemap.xml. Для корректной работы он должен отвечать со статусом HTTP 200.",
    },
    "sitemap_mismatch": {
        "title": "Карта сайта (sitemap.xml) неполная.",
        "recommendation": "Обновите sitemap.xml: добавьте в неё страницы, которые должны попадать в поиск.",
    },
}


def get_issue_message(issue_type: str) -> dict[str, str]:
    key = str(issue_type or "").strip()
    data = ISSUE_MESSAGES.get(key)
    if data:
        return data
    return {
        "title": f"Проблема SEO: {key or 'неизвестный тип'}.",
        "recommendation": "Проверьте страницу и устраните обнаруженную SEO-проблему.",
    }


def get_issue_title(issue_type: str) -> str:
    return get_issue_message(issue_type).get("title", "")


def get_issue_recommendation(issue_type: str) -> str:
    return get_issue_message(issue_type).get("recommendation", "")


ISSUE_GROUP_PRESETS = {
    "robots": {
        "label": "Проблемы с robots.txt",
        "description": "Поисковым системам сложнее корректно обходить сайт.",
        "target_block": "Индексация",
        "default_priority": "urgent",
    },
    "sitemap": {
        "label": "Проблемы с sitemap.xml",
        "description": "Часть страниц может индексироваться хуже, чем должна.",
        "target_block": "Индексация",
        "default_priority": "urgent",
    },
    "titles": {
        "label": "Проблемы с заголовком и описанием страницы (title/description)",
        "description": "Страницы хуже выглядят в поисковой выдаче и получают меньше переходов.",
        "target_block": "Страницы",
        "default_priority": "important",
    },
    "headings": {
        "label": "Проблемы со структурой заголовков (H1-H6)",
        "description": "Поисковику и пользователю сложнее понимать содержание страницы.",
        "target_block": "Страницы",
        "default_priority": "important",
    },
    "speed": {
        "label": "Проблемы скорости и веса страниц",
        "description": "Медленная загрузка ухудшает поведение пользователей и конверсию.",
        "target_block": "Скорость и производительность",
        "default_priority": "important",
    },
    "indexability": {
        "label": "Проблемы индексации страниц",
        "description": "Страницы могут индексироваться некорректно.",
        "target_block": "Индексация",
        "default_priority": "important",
    },
    "commercial": {
        "label": "Проблемы коммерческой готовности",
        "description": "Страницы слабо подготовлены к заявкам и обращениям.",
        "target_block": "Коммерческий SEO-аудит страницы",
        "default_priority": "important",
    },
    "status": {
        "label": "Страницы с ошибками ответа",
        "description": "Некоторые страницы недоступны или возвращают ошибки.",
        "target_block": "Ошибки",
        "default_priority": "urgent",
    },
    "other": {
        "label": "Другие SEO-замечания",
        "description": "Есть дополнительные точки улучшения сайта.",
        "target_block": "Ошибки",
        "default_priority": "later",
    },
}

ISSUE_TYPE_TO_GROUP = {
    "missing_robots_txt": "robots",
    "robots_disallow_all": "robots",
    "robots_missing_sitemap": "robots",
    "missing_sitemap": "sitemap",
    "bad_sitemap_status": "sitemap",
    "sitemap_mismatch": "sitemap",
    "sitemap_page_missing": "sitemap",
    "missing_title": "titles",
    "bad_title_length": "titles",
    "title_too_short": "titles",
    "title_too_long": "titles",
    "missing_description": "titles",
    "description_too_short": "titles",
    "description_too_long": "titles",
    "duplicate_title": "titles",
    "missing_h1": "headings",
    "multiple_h1": "headings",
    "long_h1": "headings",
    "heading_hierarchy_gap": "headings",
    "slow_response": "speed",
    "large_page_size": "speed",
    "slow_ttfb": "speed",
    "large_html_size": "speed",
    "too_many_js": "speed",
    "too_many_css": "speed",
    "too_many_images": "speed",
    "heavy_js_payload": "speed",
    "heavy_css_payload": "speed",
    "heavy_images_payload": "speed",
    "heavy_page_payload": "speed",
    "missing_canonical": "indexability",
    "invalid_canonical": "indexability",
    "canonical_conflict": "indexability",
    "page_noindex": "indexability",
    "page_nofollow": "indexability",
    "blocked_by_robots": "indexability",
    "missing_meta_robots": "indexability",
    "bad_status": "status",
    "network_error": "status",
    "redirect": "status",
}

PRIORITY_LABELS = {
    "urgent": "Срочно",
    "important": "Важно",
    "later": "Потом",
}

COMMERCIAL_STATUS_LABELS = {
    "good": "Готова к заявкам",
    "warning": "Можно усилить конверсию",
    "critical": "Слабо подготовлена",
}

COMMERCIAL_BUSINESS_STATUS_LABELS = {
    "ready": "Готова к заявкам",
    "has_channel": "Есть канал обращения",
    "improvable": "Можно усилить конверсию",
    "weak": "Слабо подготовлена",
    "none": "Нет сценария обращения",
}

CONVERSION_PATH_LABELS = {
    "form": "Классическая форма",
    "contacts": "Прямые контакты",
    "messenger": "Мессенджеры или соцсети",
    "widget": "Чат или плавающая кнопка",
    "mixed": "Смешанный сценарий",
    "none": "Не найден",
}


def get_issue_group_meta(issue_type: str) -> dict[str, str]:
    normalized = str(issue_type or "").strip().lower()
    group_key = ISSUE_TYPE_TO_GROUP.get(normalized, "other")
    preset = ISSUE_GROUP_PRESETS.get(group_key, ISSUE_GROUP_PRESETS["other"])
    return {
        "group_key": group_key,
        "label": preset["label"],
        "description": preset["description"],
        "target_block": preset["target_block"],
        "default_priority": preset["default_priority"],
    }


def get_priority_label(priority_key: str) -> str:
    return PRIORITY_LABELS.get(str(priority_key or "").strip().lower(), PRIORITY_LABELS["later"])


def _signal_bool(signals: dict | None, key: str) -> bool:
    return bool((signals or {}).get(key))


def get_commercial_business_status(
    *,
    status_key: str,
    signals: dict | None = None,
    has_conversion_path: bool | None = None,
    conversion_path_type: str | None = None,
    score: int | None = None,
) -> str:
    normalized_status = str(status_key or "").strip().lower() or "warning"
    normalized_path = str(conversion_path_type or "").strip().lower() or "none"
    has_path = bool(has_conversion_path)
    if has_conversion_path is None:
        has_path = bool(
            _signal_bool(signals, "has_conversion_path")
            or _signal_bool(signals, "has_form")
            or _signal_bool(signals, "has_direct_contact")
            or _signal_bool(signals, "has_phone_or_contact")
            or _signal_bool(signals, "has_messenger")
            or _signal_bool(signals, "has_messenger_contact")
            or _signal_bool(signals, "has_widget")
            or normalized_path in {"form", "contacts", "messenger", "widget", "mixed"}
        )

    numeric_score = int(score or 0)
    if not has_path or normalized_path == "none":
        return "none"
    if normalized_status == "good" and numeric_score >= 70:
        return "ready"
    if normalized_path in {"contacts", "messenger", "widget"} and numeric_score >= 45:
        return "has_channel"
    if normalized_status == "critical" or numeric_score < 45:
        return "weak"
    return "improvable"


def get_commercial_status_label(
    status_key: str,
    *,
    signals: dict | None = None,
    has_conversion_path: bool | None = None,
    conversion_path_type: str | None = None,
    score: int | None = None,
) -> str:
    business_key = get_commercial_business_status(
        status_key=status_key,
        signals=signals,
        has_conversion_path=has_conversion_path,
        conversion_path_type=conversion_path_type,
        score=score,
    )
    if business_key in COMMERCIAL_BUSINESS_STATUS_LABELS:
        return COMMERCIAL_BUSINESS_STATUS_LABELS[business_key]
    normalized = str(status_key or "").strip().lower()
    return COMMERCIAL_STATUS_LABELS.get(normalized, COMMERCIAL_STATUS_LABELS["warning"])


def get_conversion_path_label(path_type: str) -> str:
    key = str(path_type or "").strip().lower()
    return CONVERSION_PATH_LABELS.get(key, CONVERSION_PATH_LABELS["none"])


def get_commercial_explanation(
    *,
    signals: dict | None = None,
    has_conversion_path: bool | None = None,
    conversion_path_type: str | None = None,
    status_key: str = "warning",
    score: int | None = None,
) -> str:
    normalized_path = str(conversion_path_type or "").strip().lower() or "none"
    has_path = bool(has_conversion_path)
    if has_conversion_path is None:
        has_path = bool(
            _signal_bool(signals, "has_conversion_path")
            or normalized_path in {"form", "contacts", "messenger", "widget", "mixed"}
        )

    if not has_path or normalized_path == "none":
        return "На странице не найден явный сценарий обращения: нет формы, контактного блока, мессенджера или виджета."
    if normalized_path == "mixed":
        return "На странице есть несколько способов обращения: форма, кнопка действия (CTA) и дополнительные каналы связи."
    if normalized_path == "form":
        return "На странице есть форма заявки. Добавьте быстрый альтернативный канал связи для части пользователей."
    if normalized_path == "contacts":
        return "На странице есть прямые контакты для обращения, но классическая форма может дополнительно повысить отклик."
    if normalized_path == "messenger":
        return "На странице найден сценарий связи через мессенджеры или соцсети."
    if normalized_path == "widget":
        return "На странице найден виджет или плавающая кнопка для быстрого обращения."

    label = get_commercial_status_label(
        status_key,
        signals=signals,
        has_conversion_path=has_path,
        conversion_path_type=normalized_path,
        score=score,
    )
    return f"Текущий статус: {label}."


def get_commercial_recommendations(
    signals: dict[str, bool] | None,
    *,
    has_conversion_path: bool | None = None,
    conversion_path_type: str | None = None,
    score: int | None = None,
) -> list[str]:
    signal_map = signals or {}
    has_form = bool(signal_map.get("has_form"))
    has_cta = bool(signal_map.get("has_cta"))
    has_direct_contact = bool(signal_map.get("has_direct_contact") or signal_map.get("has_phone_or_contact"))
    has_messenger = bool(signal_map.get("has_messenger_contact") or signal_map.get("has_messenger"))
    has_widget = bool(signal_map.get("has_widget"))
    has_offer = bool(signal_map.get("has_offer_like_heading"))
    has_benefits = bool(signal_map.get("has_benefits_block"))
    has_faq = bool(signal_map.get("has_faq"))

    normalized_path = str(conversion_path_type or signal_map.get("conversion_path_type") or "").strip().lower() or "none"
    resolved_has_path = bool(has_conversion_path)
    if has_conversion_path is None:
        resolved_has_path = bool(
            signal_map.get("has_conversion_path")
            or has_form
            or has_direct_contact
            or has_messenger
            or has_widget
            or normalized_path in {"form", "contacts", "messenger", "widget", "mixed"}
        )

    rows: list[str] = []
    if not resolved_has_path or normalized_path == "none":
        rows.extend(
            [
                "Добавьте хотя бы один явный сценарий обращения: форму, мессенджер, контактный блок или чат-виджет.",
                "Сделайте заметную кнопку действия (CTA) на первом экране с понятным текстом: «Оставить заявку», «Получить расчёт», «Записаться».",
                "Добавьте контакты для быстрого обращения: телефон, email или мессенджер.",
            ]
        )
    else:
        if normalized_path in {"contacts", "messenger", "widget"} and not has_form:
            rows.append("Каналы связи уже найдены. Можно усилить конверсию короткой формой заявки.")
        if has_form and not (has_messenger or has_widget or has_direct_contact):
            rows.append("Форма найдена. Добавьте быстрый альтернативный канал связи через мессенджер или контакты.")
        if not has_cta:
            rows.append(
                "Сценарий обращения есть, но призыв к действию слабый. Сделайте кнопку действия (CTA) заметнее и напишите конкретный следующий шаг."
            )

    if not has_offer:
        rows.append("Уточните оффер в первом экране: что получает клиент и почему это выгодно.")
    if not has_benefits:
        rows.append("Добавьте короткий блок преимуществ, чтобы повысить доверие к предложению.")
    if not has_faq:
        rows.append("Добавьте блок FAQ или ответы на типовые вопросы для снятия возражений.")

    deduplicated: list[str] = []
    for item in rows:
        if item not in deduplicated:
            deduplicated.append(item)
    return deduplicated[:5]
