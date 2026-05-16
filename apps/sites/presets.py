HERO_SCHEMA = {
    "fields": [
        {
            "key": "title",
            "label": "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a",
            "type": "text",
            "required": True,
            "default": "",
            "placeholder": "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a",
            "help_text": "\u0413\u043b\u0430\u0432\u043d\u044b\u0439 \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a \u0431\u043b\u043e\u043a\u0430",
        },
        {
            "key": "subtitle",
            "label": "\u041f\u043e\u0434\u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a",
            "type": "textarea",
            "required": False,
            "default": "",
            "placeholder": "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043f\u043e\u0434\u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a",
            "help_text": "\u041a\u0440\u0430\u0442\u043a\u043e\u0435 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u0431\u043b\u043e\u043a\u0430",
        },
        {
            "key": "background_image",
            "label": "\u0424\u043e\u043d\u043e\u0432\u043e\u0435 \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435",
            "type": "image",
            "required": False,
            "default": "",
            "placeholder": "",
            "help_text": "\u0421\u0441\u044b\u043b\u043a\u0430 \u0438\u043b\u0438 \u043f\u0443\u0442\u044c \u043a \u0444\u0430\u0439\u043b\u0443",
        },
        {
            "key": "background_video",
            "label": "\u0424\u043e\u043d\u043e\u0432\u043e\u0435 \u0432\u0438\u0434\u0435\u043e",
            "type": "video",
            "required": False,
            "default": "",
            "placeholder": "",
            "help_text": "\u041e\u043f\u0446\u0438\u043e\u043d\u0430\u043b\u044c\u043d\u043e \u0434\u043b\u044f hero-\u0431\u043b\u043e\u043a\u0430",
        },
    ]
}

ABOUT_SCHEMA = {
    "fields": [
        {
            "key": "title",
            "label": "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a",
            "type": "text",
            "required": True,
            "default": "",
            "placeholder": "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a",
            "help_text": "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0431\u043b\u043e\u043a\u0430 \u00ab\u041e \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438\u00bb",
        },
        {
            "key": "description",
            "label": "\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
            "type": "textarea",
            "required": True,
            "default": "",
            "placeholder": "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
            "help_text": "\u041e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 \u0442\u0435\u043a\u0441\u0442 \u0431\u043b\u043e\u043a\u0430",
        },
        {
            "key": "team_size",
            "label": "\u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u043e\u0432",
            "type": "number",
            "required": False,
            "default": 0,
            "placeholder": "",
            "help_text": "\u0426\u0435\u043b\u043e\u0435 \u0447\u0438\u0441\u043b\u043e",
        },
    ]
}

SERVICES_SCHEMA = {
    "fields": [
        {
            "key": "title",
            "label": "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a \u0431\u043b\u043e\u043a\u0430",
            "type": "text",
            "required": True,
            "default": "",
            "placeholder": "\u041d\u0430\u0448\u0438 \u0443\u0441\u043b\u0443\u0433\u0438",
            "help_text": "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a \u0441\u0435\u043a\u0446\u0438\u0438 \u0443\u0441\u043b\u0443\u0433",
        },
        {
            "key": "layout",
            "label": "\u0412\u0438\u0434 \u043e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f",
            "type": "select",
            "required": False,
            "default": "grid",
            "placeholder": "",
            "help_text": "grid \u0438\u043b\u0438 list",
            "options": ["grid", "list"],
        },
        {
            "key": "show_icons",
            "label": "\u041f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0442\u044c \u0438\u043a\u043e\u043d\u043a\u0438",
            "type": "boolean",
            "required": False,
            "default": True,
            "placeholder": "",
            "help_text": "\u0412\u043a\u043b/\u0432\u044b\u043a\u043b \u0438\u043a\u043e\u043d\u043e\u043a \u0443 \u0443\u0441\u043b\u0443\u0433",
        },
        {
            "key": "items",
            "label": "\u0421\u043f\u0438\u0441\u043e\u043a \u0443\u0441\u043b\u0443\u0433",
            "type": "repeater",
            "required": False,
            "default": [],
            "placeholder": "",
            "help_text": "\u041d\u0430\u0431\u043e\u0440 \u043a\u0430\u0440\u0442\u043e\u0447\u0435\u043a \u0443\u0441\u043b\u0443\u0433",
            "fields": [
                {
                    "key": "title",
                    "label": "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a",
                    "type": "text",
                    "required": True,
                    "default": "",
                    "placeholder": "",
                    "help_text": "",
                },
                {
                    "key": "description",
                    "label": "\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
                    "type": "textarea",
                    "required": False,
                    "default": "",
                    "placeholder": "",
                    "help_text": "",
                },
                {
                    "key": "price",
                    "label": "\u0426\u0435\u043d\u0430",
                    "type": "number",
                    "required": False,
                    "default": 0,
                    "placeholder": "",
                    "help_text": "",
                },
            ],
        },
    ]
}

REVIEWS_SCHEMA = {
    "fields": [
        {
            "key": "title",
            "label": "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a \u0431\u043b\u043e\u043a\u0430",
            "type": "text",
            "required": False,
            "default": "\u041e\u0442\u0437\u044b\u0432\u044b \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u0432",
            "placeholder": "",
            "help_text": "",
        },
        {
            "key": "items",
            "label": "\u041e\u0442\u0437\u044b\u0432\u044b",
            "type": "repeater",
            "required": False,
            "default": [],
            "placeholder": "",
            "help_text": "",
            "fields": [
                {
                    "key": "author",
                    "label": "\u0410\u0432\u0442\u043e\u0440",
                    "type": "text",
                    "required": True,
                    "default": "",
                    "placeholder": "",
                    "help_text": "",
                },
                {
                    "key": "rating",
                    "label": "\u041e\u0446\u0435\u043d\u043a\u0430",
                    "type": "number",
                    "required": False,
                    "default": 5,
                    "placeholder": "",
                    "help_text": "",
                },
                {
                    "key": "text",
                    "label": "\u0422\u0435\u043a\u0441\u0442 \u043e\u0442\u0437\u044b\u0432\u0430",
                    "type": "textarea",
                    "required": True,
                    "default": "",
                    "placeholder": "",
                    "help_text": "",
                },
            ],
        },
    ]
}

CONTACTS_SCHEMA = {
    "fields": [
        {
            "key": "title",
            "label": "\u0417\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a",
            "type": "text",
            "required": False,
            "default": "\u041a\u043e\u043d\u0442\u0430\u043a\u0442\u044b",
            "placeholder": "",
            "help_text": "",
        },
        {
            "key": "phone",
            "label": "\u0422\u0435\u043b\u0435\u0444\u043e\u043d",
            "type": "text",
            "required": False,
            "default": "",
            "placeholder": "+7 ...",
            "help_text": "",
        },
        {
            "key": "email",
            "label": "Email",
            "type": "text",
            "required": False,
            "default": "",
            "placeholder": "info@example.com",
            "help_text": "",
        },
        {
            "key": "preferred_contact",
            "label": "\u041f\u0440\u0435\u0434\u043f\u043e\u0447\u0442\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u043a\u0430\u043d\u0430\u043b",
            "type": "select",
            "required": False,
            "default": "phone",
            "placeholder": "",
            "help_text": "",
            "options": ["phone", "email", "telegram"],
        },
        {
            "key": "show_form",
            "label": "\u041f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0442\u044c \u0444\u043e\u0440\u043c\u0443",
            "type": "boolean",
            "required": False,
            "default": True,
            "placeholder": "",
            "help_text": "",
        },
    ]
}

HERO_DEFAULT_SETTINGS = {
    "theme": "dark",
    "spacing": "large",
    "animation": "fade-up",
    "container": "xl",
    "visible": True,
    "layout": "centered",
    "background": "image",
    "custom_classes": "",
}

SERVICES_DEFAULT_SETTINGS = {
    "theme": "light",
    "spacing": "medium",
    "animation": "fade-up",
    "container": "xl",
    "visible": True,
    "layout": "grid",
    "background": "none",
    "custom_classes": "",
}

REVIEWS_DEFAULT_SETTINGS = {
    "theme": "light",
    "spacing": "medium",
    "animation": "fade-up",
    "container": "lg",
    "visible": True,
    "layout": "slider",
    "background": "none",
    "custom_classes": "",
}
