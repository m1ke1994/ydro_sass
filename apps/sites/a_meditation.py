from copy import deepcopy


A_MEDITATION_SITE_SLUG = "a-meditation"


def field(key, label, field_type="text", default="", **extra):
    return {
        "key": key,
        "label": label,
        "type": field_type,
        "default": deepcopy(default),
        **extra,
    }


def repeater(key, label, fields, default=None, **extra):
    return field(
        key,
        label,
        "repeater",
        [] if default is None else default,
        fields=fields,
        **extra,
    )


def text_items(key, label):
    return repeater(
        key,
        label,
        [field("text", "Текст", "textarea")],
    )


SECTION_TITLES = {
    "header": "Шапка сайта",
    "hero": "Hero-блок",
    "simple_words": "Об игре Лила",
    "guide": "О проекте и проводнике",
    "meditations": "Медитации",
    "gallery": "Галерея",
    "reviews": "Отзывы",
    "services": "Форматы занятий",
    "contacts": "Форма заявки и контакты",
    "footer": "Подвал сайта",
}


A_MEDITATION_SECTION_SEEDS = [
    {
        "key": "header",
        "title": SECTION_TITLES["header"],
        "order": 1,
        "schema": {
            "fields": [
                field("brand_left", "Название слева от логотипа"),
                field("brand_right", "Название справа от логотипа"),
                repeater(
                    "left_links",
                    "Ссылки слева",
                    [
                        field("label", "Название"),
                        field("href", "Ссылка на блок"),
                    ],
                ),
                repeater(
                    "right_links",
                    "Ссылки справа",
                    [
                        field("label", "Название"),
                        field("href", "Ссылка на блок"),
                    ],
                ),
            ]
        },
        "content": {
            "brand_left": "ЛИЛА",
            "brand_right": "МОСКВА",
            "left_links": [
                {"label": "ПРО ЛИЛУ", "href": "#simple-words"},
                {"label": "ПРОВОДНИК ЛИЛЫ", "href": "#guide"},
                {"label": "ОТЗЫВЫ", "href": "#reviews"},
            ],
            "right_links": [
                {"label": "МЕДИТАЦИИ", "href": "#meditations"},
                {"label": "СТОИМОСТЬ", "href": "#pricing"},
                {"label": "КОНТАКТЫ", "href": "#contacts"},
            ],
        },
    },
    {
        "key": "hero",
        "title": SECTION_TITLES["hero"],
        "order": 2,
        "schema": {
            "fields": [
                field("tag", "Надзаголовок"),
                repeater(
                    "phrases",
                    "Сменяющиеся заголовки",
                    [field("text", "Заголовок", "textarea")],
                ),
                field("description", "Описание", "textarea"),
                field("button_text", "Текст основной кнопки"),
                field("button_link", "Ссылка основной кнопки"),
                field("secondary_button_text", "Текст второй кнопки"),
                field("secondary_button_link", "Ссылка второй кнопки"),
                field("image", "Фоновое изображение", "image"),
                field("background_video", "Фоновое видео", "video"),
            ]
        },
        "content": {
            "tag": "ЛИЛА МОСКВА",
            "phrases": [
                {"text": "Игра, которая помогает услышать себя"},
                {"text": "Пространство для честного внутреннего диалога"},
                {"text": "Мягкий путь к ясности, решениям и опоре"},
                {"text": "Лила в Москве — встреча с собой через игру"},
                {"text": "Когда ответы приходят не из шума, а из тишины"},
            ],
            "description": "Практика, где игра становится проводником к ясности, спокойствию и внутренним ответам.",
            "button_text": "Записаться на игру",
            "button_link": "#contacts",
            "secondary_button_text": "Узнать стоимость",
            "secondary_button_link": "#pricing",
            "image": "/images/Lila_Olga_2.2.poster.jpg",
            "background_video": "/images/Lila_Olga_2.2_compressed.mp4",
        },
    },
    {
        "key": "simple_words",
        "title": SECTION_TITLES["simple_words"],
        "order": 3,
        "schema": {
            "fields": [
                field("eyebrow", "Надзаголовок"),
                field("title", "Заголовок"),
                field("description", "Описание", "textarea"),
                repeater(
                    "cards",
                    "Карточки об игре",
                    [
                        field("number", "Номер"),
                        field("title", "Заголовок"),
                        field("text", "Текст", "textarea"),
                    ],
                ),
                field("mobile_cards_label", "Подсказка на телефоне"),
                field("process_eyebrow", "Надзаголовок процесса"),
                field("process_title", "Заголовок процесса"),
                repeater(
                    "process_cards",
                    "Этапы процесса",
                    [
                        field("icon", "Номер"),
                        field("title", "Заголовок"),
                        field("text", "Текст", "textarea"),
                    ],
                ),
                field("mobile_process_label", "Подсказка процесса на телефоне"),
            ]
        },
        "content": {
            "eyebrow": "Понятно и бережно",
            "title": "Лила простыми словами",
            "description": "Игра Лила — это не гадание и не случайный набор ходов. Это мягкий способ увидеть свои внутренние состояния, вопросы и повторяющиеся сценарии через игровое поле.",
            "cards": [
                {
                    "number": "01",
                    "title": "Что такое Лила?",
                    "text": "Лила — древняя трансформационная игра, где человек формулирует запрос и проходит путь по игровому полю. Каждый ход помогает посмотреть на ситуацию глубже и честнее.",
                },
                {
                    "number": "02",
                    "title": "Как проходит игра?",
                    "text": "Игрок движется по клеткам поля, а проводник помогает расшифровать значения состояний и связать их с реальной жизнью, вопросом или внутренним выбором.",
                },
                {
                    "number": "03",
                    "title": "Для чего это нужно?",
                    "text": "Игра помогает увидеть скрытые причины напряжения, найти опору, принять решение и почувствовать больше ясности в себе.",
                },
                {
                    "number": "04",
                    "title": "Что получают игроки?",
                    "text": "Уверенность, ясность, отношения, работу, жизнь мечты.\nВы точно узнаете, чего на самом деле хотите, раскроете свой потенциал и запустите процесс изменений в свою жизнь.",
                },
            ],
            "mobile_cards_label": "Листайте карточки",
            "process_eyebrow": "Процесс",
            "process_title": "Как проходит Лила?",
            "process_cards": [
                {"icon": "01", "title": "Без спешки", "text": "Есть возможность проходить игру до полного прохождения."},
                {"icon": "02", "title": "С мастером игры", "text": "Глубокие практики Лилы простым и понятным языком."},
                {"icon": "03", "title": "Подберём дату", "text": "Удобные дата и время игры в группе или индивидуально."},
                {"icon": "04", "title": "Большое поле", "text": "Играющий перемещается по клеткам поля своими ногами."},
            ],
            "mobile_process_label": "Свайпните процесс",
        },
    },
    {
        "key": "guide",
        "title": SECTION_TITLES["guide"],
        "order": 4,
        "schema": {
            "fields": [
                field("tag", "Надзаголовок"),
                field("subtitle", "Имя проводника"),
                field("brand", "Подпись под именем"),
                field("description", "Краткое описание", "textarea"),
                field("image", "Фото проводника", "image"),
                field("image_alt", "Описание фото"),
                text_items("intro_paragraphs", "Вводный текст"),
                text_items("expanded_paragraphs", "Продолжение"),
                field("results_title", "Заголовок результатов"),
                text_items("results", "Результаты участников"),
                text_items("final_paragraphs", "Заключительный текст"),
                field("closing_text", "Выделенная цитата", "textarea"),
                repeater(
                    "metrics",
                    "Преимущества и факты",
                    [
                        field("value", "Значение"),
                        field("label", "Подпись"),
                    ],
                ),
            ]
        },
        "content": {
            "tag": "Проводник игры Лила",
            "subtitle": "Ольга Бердникова",
            "brand": "Leelabird",
            "description": "Практик осознанности, медитации и Игры Лила",
            "image": "/images/2025-02-26 12-35-42.JPG",
            "image_alt": "Проводник игры Лила Ольга Бердникова",
            "intro_paragraphs": [
                {"text": "Пройдя глубокий опыт випассаны — специального ретрита, проведенного в полном молчании, аскетизме и медитациях, в 2022 году на день рождения в подарок получила участие в Игре Лила."},
                {"text": "После игры во мне произошла сильная трансформация. События, отыгранные на поле, разворачивались четыре месяца, меняя вектор моей жизни. Уходило лишнее, приходило нужное."},
                {"text": "Но самое главное — произошло узнавание себя как Проводника Лилы."},
            ],
            "expanded_paragraphs": [
                {"text": "Я прошла обучение в международной школе OMKARA и с тех пор веду Игру на постоянной основе, являюсь игропрактиком на фестивалях самопознания День Йоги, День Индии, Этно космос и других."},
            ],
            "results_title": "250+ человек уже прошли со мной свою трансформацию:",
            "results": [
                {"text": "Возобновили или с нуля создали доходные проекты по сердцу, в которые до этого не верили"},
                {"text": "Переехали в место, подходящее для развития и счастливой жизни"},
                {"text": "Выстроили гармоничные отношения с близкими, сохраняя свои интересы"},
                {"text": "Научились кайфовать от себя и жизни и похудели на 8 кг без диет и стресса"},
            ],
            "final_paragraphs": [
                {"text": "Исповедую идею баланса, ответственного отношения к жизни, сострадания, красоты и здорового юмора."},
                {"text": "Называю себя чутким, но четким проводником: веду очень мягко, без насилия, чувствую поле, но при необходимости крепким словцом верну в реальность — сплошная ваниль трансформации не дает, а ведь игроки приходят ко мне за реальными изменениями."},
                {"text": "Важно! На поле Лилы есть клеточка Дана — Щедрость. Она поднимает игрока по стреле в состояние баланса."},
                {"text": "Играя в Лилу со мной, вы автоматически участвуете в благотворительности: 10% после каждой игры я перевожу на помощь женщинам в трудной жизненной ситуации, детям или семьям с детьми."},
            ],
            "closing_text": "Делая лучше хотя бы одному живому существу, мы оказываем большую помощь себе, и это не может не сказаться на качестве и скорости изменений в вашей жизни после Игры.",
            "metrics": [
                {"value": "100%", "label": "экологичное ведение"},
                {"value": "2000+", "label": "проведённых игр"},
                {"value": "мягко", "label": "без давления"},
                {"value": "ясно", "label": "простым языком"},
            ],
        },
    },
    {
        "key": "meditations",
        "title": SECTION_TITLES["meditations"],
        "order": 5,
        "schema": {
            "fields": [
                field("subtitle", "Надзаголовок"),
                field("title", "Заголовок"),
                field("accent", "Выделенная строка заголовка"),
                field("description", "Краткое описание", "textarea"),
                field("detail_text", "Подробное описание", "textarea"),
                repeater(
                    "items",
                    "Фото и видео практик",
                    [
                        field("number", "Номер"),
                        field("title", "Название"),
                        field("text", "Описание", "textarea"),
                        field("image", "Фото или видео", "media"),
                        field(
                            "type",
                            "Тип файла",
                            "select",
                            "image",
                            options=[
                                {"value": "image", "label": "Изображение"},
                                {"value": "video", "label": "Видео"},
                            ],
                        ),
                    ],
                ),
                field("format_label", "Надзаголовок формата"),
                field("format_text", "Описание формата", "textarea"),
                field("button_text", "Текст кнопки"),
            ]
        },
        "content": {
            "subtitle": "Практики тишины",
            "title": "Медитации",
            "accent": "для восстановления",
            "description": "Пространство тишины, бережного внимания и внутренней опоры",
            "detail_text": "Медитации помогают замедлиться, отпустить лишнее напряжение и мягко вернуться к себе. Это спокойная практика для восстановления ресурса, ясности и более глубокого контакта со своим состоянием.",
            "items": [
                {"number": "01", "title": "Глубокое расслабление", "text": "Мягкая практика для снятия напряжения.", "image": "/images/m1.jpg", "type": "image"},
                {"number": "02", "title": "Восстановление ресурса", "text": "Тишина и дыхание для внутреннего восстановления.", "image": "/images/Lila_Olga_2.2_compressed.mp4", "type": "video"},
                {"number": "03", "title": "Контакт с собой", "text": "Практика возвращения к ощущениям и ясности.", "image": "/images/m3.jpg", "type": "image"},
                {"number": "04", "title": "Внутренняя настройка", "text": "Мягкая настройка на важный период жизни.", "image": "/images/m4.jpg", "type": "image"},
            ],
            "format_label": "Формат практики",
            "format_text": "Медитации проходят в мягком темпе: без давления, без спешки и без необходимости «делать правильно». Главное — ваше состояние, дыхание и бережное возвращение внимания к себе.",
            "button_text": "Выбрать практику",
        },
    },
    {
        "key": "gallery",
        "title": SECTION_TITLES["gallery"],
        "order": 6,
        "schema": {
            "fields": [
                field("subtitle", "Надзаголовок"),
                field("title", "Заголовок"),
                field("description", "Описание", "textarea"),
                repeater(
                    "items",
                    "Изображения",
                    [
                        field("src", "Изображение", "image"),
                        field("alt", "Описание изображения"),
                        field("title", "Подпись"),
                    ],
                ),
            ]
        },
        "content": {
            "subtitle": "Визуальная история",
            "title": "Галерея",
            "description": "Атмосфера практик, встреч и пространства",
            "items": [
                {"src": "/images/DSC08101.JPG", "alt": "Атмосфера практики Лила", "title": "Пространство встречи"},
                {"src": "/images/2025-02-26 13-06-17.JPG", "alt": "Практика и пространство", "title": "Тихая практика"},
                {"src": "/images/IMG_5131.JPG", "alt": "Детали пространства для практик", "title": "Детали пространства"},
                {"src": "/images/Lila_Olga_2.2.poster.jpg", "alt": "Глубокое состояние практики", "title": "Глубокое состояние"},
            ],
        },
    },
    {
        "key": "reviews",
        "title": SECTION_TITLES["reviews"],
        "order": 7,
        "schema": {
            "fields": [
                field("subtitle", "Надзаголовок"),
                field("title", "Заголовок"),
                field("description", "Описание", "textarea"),
                field("button_text", "Текст кнопки"),
                field("button_link", "Ссылка кнопки"),
                repeater(
                    "items",
                    "Отзывы",
                    [
                        field("name", "Имя"),
                        field("date", "Подпись или дата"),
                        field("avatar", "Фотография", "image"),
                        field("text", "Текст отзыва", "textarea"),
                    ],
                ),
            ]
        },
        "content": {
            "subtitle": "Реальные впечатления",
            "title": "Отзывы участников",
            "description": "Истории людей, которые прошли практику и поделились своим опытом.",
            "button_text": "Читать больше отзывов",
            "button_link": "https://t.me/leelabirdcase",
            "items": [
                {"name": "Участница игры", "date": "Отзыв из Telegram", "avatar": "/images/IMG_1245.JPG", "text": "Игра запустила глубокий процесс размышлений. Спасибо за бережное сопровождение и возможность прийти к собственным ответам."},
                {"name": "Участница игры", "date": "Отзыв из Telegram", "avatar": "/images/IMG_1246.JPG", "text": "Очень комфортная игра и безопасная атмосфера. Инсайты продолжали приходить ещё несколько дней после встречи."},
                {"name": "Участница игры", "date": "Отзыв из Telegram", "avatar": "/images/IMG_1249.JPG", "text": "Четыре часа пролетели как одно дыхание. Игра подсветила то, что тормозит, и направление, куда стоит двигаться."},
                {"name": "Участница игры", "date": "Отзыв из Telegram", "avatar": "/images/IMG_1988.JPG", "text": "Спокойно, бережно и честно. В процессе появилась ясность и внутренняя опора."},
            ],
        },
    },
    {
        "key": "services",
        "title": SECTION_TITLES["services"],
        "order": 8,
        "schema": {
            "fields": [
                field("title", "Заголовок"),
                field("subtitle", "Подзаголовок"),
                field("description", "Описание", "textarea"),
                field("button_text", "Текст кнопки в карточке"),
                repeater(
                    "tabs",
                    "Направления",
                    [
                        field("label", "Название направления"),
                        field("key", "", hidden=True),
                        field("intro", "Описание направления", "textarea"),
                        repeater(
                            "cards",
                            "Форматы",
                            [
                                field("title", "Название"),
                                field("description", "Описание", "textarea"),
                                field("duration", "Длительность"),
                                field("format", "Формат проведения"),
                                field("price", "Стоимость"),
                                field("button_text", "Текст кнопки"),
                            ],
                        ),
                    ],
                ),
                field("modal_tag", "Надзаголовок формы"),
                field("modal_title", "Заголовок формы"),
                field("modal_selected_label", "Подпись выбранного формата"),
                field("modal_price_label", "Подпись стоимости"),
                field("modal_duration_label", "Подпись длительности"),
                field("modal_name_label", "Подпись поля имени"),
                field("modal_name_placeholder", "Подсказка поля имени"),
                field("modal_phone_label", "Подпись поля телефона"),
                field("modal_phone_placeholder", "Подсказка поля телефона"),
                field("modal_comment_label", "Подпись комментария"),
                field("modal_comment_placeholder", "Подсказка комментария"),
                field("modal_submit_text", "Текст кнопки отправки"),
                field("modal_sending_text", "Текст во время отправки"),
                field("modal_success_text", "Сообщение после отправки"),
            ]
        },
        "content": {
            "title": "Форматы участия",
            "subtitle": "Выберите практику, которая подходит вам сейчас",
            "description": "Все форматы можно адаптировать под ваш запрос.",
            "button_text": "Записаться",
            "tabs": [
                {
                    "key": "lila",
                    "label": "Игра Лила",
                    "intro": "Форматы для личного запроса и глубокого разбора ситуации.",
                    "cards": [
                        {"title": "Индивидуальная игра Лила", "description": "Личная практика для глубокого разбора запроса и поиска внутренней опоры.", "duration": "2–3 часа", "format": "очно / онлайн", "price": "от 5 000 ₽", "button_text": "Записаться"},
                        {"title": "Групповая игра Лила", "description": "Практика в малой группе, где каждый участник проходит свой путь через поле игры.", "duration": "3–4 часа", "format": "очно", "price": "от 3 000 ₽", "button_text": "Записаться"},
                    ],
                },
                {
                    "key": "meditations",
                    "label": "Медитации",
                    "intro": "Спокойные форматы для восстановления и внутренней опоры.",
                    "cards": [
                        {"title": "Индивидуальная медитация", "description": "Персональная практика для восстановления, тишины и контакта с собой.", "duration": "60 минут", "format": "очно / онлайн", "price": "от 3 000 ₽", "button_text": "Записаться"},
                        {"title": "Групповая медитация", "description": "Мягкая практика в группе для замедления и внутренней опоры.", "duration": "60–90 минут", "format": "очно", "price": "от 1 500 ₽", "button_text": "Записаться"},
                    ],
                },
            ],
            "modal_tag": "Заявка",
            "modal_title": "Записаться на услугу",
            "modal_selected_label": "Выбранный формат",
            "modal_price_label": "Стоимость",
            "modal_duration_label": "Длительность",
            "modal_name_label": "Имя",
            "modal_name_placeholder": "Ваше имя",
            "modal_phone_label": "Телефон",
            "modal_phone_placeholder": "+7 999 000-00-00",
            "modal_comment_label": "Комментарий",
            "modal_comment_placeholder": "Дата, количество игроков, пожелания",
            "modal_submit_text": "Отправить",
            "modal_sending_text": "Отправляем...",
            "modal_success_text": "Заявка успешно отправлена",
        },
    },
    {
        "key": "contacts",
        "title": SECTION_TITLES["contacts"],
        "order": 9,
        "schema": {
            "fields": [
                field("subtitle", "Надзаголовок"),
                field("title", "Заголовок"),
                field("description", "Описание", "textarea"),
                field("form_title", "Заголовок формы"),
                field("form_description", "Описание формы", "textarea"),
                field("name_placeholder", "Подсказка поля имени"),
                field("phone_placeholder", "Подсказка поля телефона"),
                field("telegram_placeholder", "Подсказка поля Telegram"),
                field("message_placeholder", "Подсказка поля сообщения"),
                field("consent_text", "Текст согласия", "textarea"),
                field("submit_text", "Текст кнопки"),
                field("sending_text", "Текст во время отправки"),
                field("success_text", "Сообщение после отправки"),
                field("location_title", "Заголовок блока адресов"),
                field("address_label", "Подпись адреса"),
                field("address", "Адрес", "textarea"),
                field("contacts_label", "Подпись телефона и Telegram"),
                field("phone", "Телефон"),
                field("email", "Email"),
                field("telegram", "Telegram"),
                field("format_label", "Подпись формата"),
                field("format_text", "Формат проведения"),
                repeater(
                    "locations",
                    "Места проведения",
                    [
                        field("title", "Название"),
                        field("address", "Адрес"),
                        field("lat", "Широта", "number", 0),
                        field("lng", "Долгота", "number", 0),
                    ],
                ),
            ]
        },
        "content": {
            "subtitle": "Свяжитесь для записи",
            "title": "Контакты и запись на практику",
            "description": "Оставьте заявку, и мы подберем удобный формат практики под ваш запрос.",
            "form_title": "Форма обратной связи",
            "form_description": "Заполните форму, и мы свяжемся с вами в ближайшее время.",
            "name_placeholder": "ФИО",
            "phone_placeholder": "Телефон *",
            "telegram_placeholder": "Telegram",
            "message_placeholder": "Дата, количество участников, пожелания",
            "consent_text": "Нажимая кнопку «Отправить», я соглашаюсь на обработку персональных данных.",
            "submit_text": "Отправить",
            "sending_text": "Отправляем...",
            "success_text": "Заявка отправлена. Мы свяжемся с вами в ближайшее время.",
            "location_title": "Где проходит практика",
            "address_label": "Адрес:",
            "address": "Москва, ул. Ботаническая, 33В стр 1",
            "contacts_label": "Телефон / Telegram:",
            "phone": "+7 903 198-91-88",
            "email": "admin@test.ru",
            "telegram": "@leelabirdcase",
            "format_label": "Формат:",
            "format_text": "индивидуально, парами или в группе",
            "locations": [
                {"title": "Парк Горького", "address": "Москва, ул. Крымский Вал, 9", "lat": 55.7298, "lng": 37.6011},
                {"title": "Патриаршие пруды", "address": "Москва, Патриаршие пруды", "lat": 55.7636, "lng": 37.5906},
                {"title": "ВДНХ", "address": "Москва, проспект Мира, 119", "lat": 55.8298, "lng": 37.6328},
                {"title": "Третьяковская галерея", "address": "Москва, Лаврушинский пер., 10", "lat": 55.7414, "lng": 37.6208},
            ],
        },
    },
    {
        "key": "footer",
        "title": SECTION_TITLES["footer"],
        "order": 10,
        "schema": {
            "fields": [
                field("brand", "Название"),
                field("copyright", "Строка об авторских правах"),
                field("navigation_title", "Заголовок навигации"),
                repeater(
                    "navigation_links",
                    "Навигация",
                    [
                        field("label", "Название"),
                        field("href", "Ссылка на блок"),
                    ],
                ),
                field("contacts_title", "Заголовок контактов"),
                repeater(
                    "links",
                    "Контактные ссылки",
                    [
                        field("label", "Название"),
                        field("href", "Ссылка"),
                        field(
                            "target",
                            "Как открыть ссылку",
                            "select",
                            "_self",
                            options=[
                                {"value": "_self", "label": "В этом окне"},
                                {"value": "_blank", "label": "В новом окне"},
                            ],
                        ),
                    ],
                ),
                field("text", "Нижний текст", "textarea"),
            ]
        },
        "content": {
            "brand": "ЛИЛА МОСКВА",
            "copyright": "© 2026 Все права защищены.",
            "navigation_title": "Навигация",
            "navigation_links": [
                {"label": "Простыми словами", "href": "#simple-words"},
                {"label": "Проводник Лилы", "href": "#guide"},
                {"label": "Отзывы", "href": "#reviews"},
                {"label": "Стоимость", "href": "#pricing"},
            ],
            "contacts_title": "Контакты",
            "links": [
                {"label": "Записаться на игру", "href": "#contacts", "target": "_self"},
                {"label": "Telegram", "href": "https://t.me/leelabirdcase", "target": "_blank"},
            ],
            "text": "Игра Лила в Москве — путь к ясности через честный диалог с собой.",
        },
    },
]


def merge_content_defaults(defaults, current):
    if not isinstance(defaults, dict):
        return deepcopy(current if current is not None else defaults)

    current = current if isinstance(current, dict) else {}
    merged = deepcopy(defaults)
    for key, value in current.items():
        if key not in defaults:
            continue
        if isinstance(defaults[key], dict) and isinstance(value, dict):
            merged[key] = merge_content_defaults(defaults[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def get_section_seed(key):
    return next((seed for seed in A_MEDITATION_SECTION_SEEDS if seed["key"] == key), None)
