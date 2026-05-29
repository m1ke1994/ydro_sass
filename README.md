# Yadro SaaS (core + mini_bitrix)

Монорепозиторий объединяет ядро Yadro и функциональность mini_bitrix/mini_saas:
- подключаемые клиентские сайты;
- публичный tracker.js + сбор событий;
- сбор заявок (leads) и статусы;
- SEO-аудит с историей, сравнениями и PDF-экспортом;
- Telegram-уведомления и отправка отчетов;
- AI-рекомендации (с fallback без ключа);
- Vue Admin для клиента.

## 1. Быстрый старт (Docker)

```bash
docker compose up --build
```

После старта:
- Backend API: `http://localhost:8000`
- Vue Admin: `http://localhost:5173`

## 2. Первичная настройка

1. Скопировать `.env.example` в `.env` и заполнить значения.
2. Применить миграции:

```bash
docker compose exec backend python manage.py migrate
```

3. Создать суперпользователя:

```bash
docker compose exec backend python manage.py createsuperuser
```

## 3. Локальный запуск без Docker

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Vue Admin:

```bash
cd vue-admin
npm install
npm run dev
```

## 4. Создание сайта и API-ключ

- Создайте клиента/сайт в Django Admin (`/admin`).
- У клиента используется `api_key` для публичных endpoints и tracker.js.

## 5. Подключение tracker.js

Endpoint скрипта:
- `GET /tracker.js`
- совместимый alias: `GET /api/mini/tracker.js`

Вставка на публичный сайт:

```html
<script
  src="https://YOUR_DOMAIN/tracker.js"
  data-api-key="SITE_API_KEY"
  async
></script>
```

Nuxt env-вариант:

```env
NUXT_PUBLIC_TRACKNODE_TRACKER_SRC=https://YOUR_DOMAIN/tracker.js
NUXT_PUBLIC_TRACKNODE_API_KEY=SITE_API_KEY
```

## 6. Тестовая отправка заявки

```bash
curl -X POST http://localhost:8000/api/public/lead/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SITE_API_KEY" \
  -d '{
    "name": "Иван",
    "phone": "+79990000000",
    "email": "ivan@example.com",
    "message": "Нужна консультация",
    "source_url": "https://client-site.ru/landing"
  }'
```

## 7. Запуск SEO-аудита

1. Авторизуйтесь в API как клиент.
2. Запустите аудит:

```bash
POST /api/seo/start/
```

3. Получить детали:

```bash
GET /api/seo/{audit_id}/
```

4. Скачать PDF:

```bash
GET /api/seo/{audit_id}/export/
```

## 8. Telegram

Основные env:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_BOT_USERNAME`
- `PUBLIC_BASE_URL`
- `TELEGRAM_BIND_TOKEN_MAX_AGE`

Webhook endpoint:
- `/api/public/telegram/webhook/`
- alias: `/api/mini/public/telegram/webhook/`

## 9. Генерация PDF-отчетов

Поддерживается экспорт:
- SEO-аудит: `/api/seo/{audit_id}/export/`
- отчеты из модуля `reports`.

## 10. Запуск тестов

Backend:

```bash
# SQLite-based test run
DB_ENGINE=sqlite python manage.py test
```

Docker:

```bash
docker compose exec backend python manage.py test
```

Frontend:
- отдельные frontend-тесты в текущей конфигурации не заведены (есть `build`/`dev`).

## 11. Celery

Подняты сервисы:
- `celery_worker`
- `celery_beat`

Запуск в Docker уже включен в `docker-compose.yml`.

## 12. Совместимость mini_bitrix

Сохранены совместимые маршруты mini API:
- `/api/mini/*`
- `/api/track/*`
- `/api/public/lead/`
- `/api/public/event/`
- `/api/analytics/event/`
- `/api/analytics/*`
- `/api/seo/*`
- `/api/reports/*`

Это позволяет подключать старые публичные сайты и клиентские интеграции без смены контрактов.
