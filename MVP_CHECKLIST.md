# MVP_CHECKLIST: Yadro SaaS / Mini CRM

## 1. Запуск backend

- [ ] Проверить `.env`: `ENABLE_BILLING=false`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`.
- [ ] Запустить контейнеры:
```bash
docker compose up -d --build
```
- [ ] Применить миграции:
```bash
docker compose exec backend python manage.py migrate
```

## 2. Запуск Vue Admin

- [ ] Открыть `http://localhost:8001`.
- [ ] Проверить авторизацию пользователя `amedia@test.ru / test-test`.

## 3. Запуск публичного сайта

- [ ] Поднять публичный сайт `a-meditation`.
- [ ] Проверить подключение `tracker.js` с актуальным `data-api-key`.

## 4. Пользователь и доступы

- [ ] Выполнить:
```bash
docker compose exec backend python manage.py seed_amedia_owner
```
- [ ] Убедиться, что пользователь видит только сайт `A Meditation / Амедиа`.
- [ ] Убедиться, что при `ENABLE_BILLING=false` нет блокировок Mini CRM.
- [ ] Проверить отсутствие ошибки `Client dashboard access is available only for active client users.`.

## 5. Telegram подключение

- [ ] В разделе «Интеграции» есть кнопки:
- `Подключить Telegram`
- `Отправить тестовое сообщение`
- `Отключить Telegram`
- [ ] Сырой Connect URL не является главным элементом интерфейса.
- [ ] Нажатие «Подключить Telegram» открывает бота с bind token.
- [ ] Проверка `/start <token>` сохраняет `telegram_chat_id`.
- [ ] Статус меняется на «Telegram подключен».

## 6. Тестовое сообщение Telegram

- [ ] Нажать «Отправить тестовое сообщение».
- [ ] Убедиться, что при рабочем Telegram API сообщение доходит в чат.
- [ ] При ошибке Telegram API backend не падает и возвращает понятную ошибку.

## 7. Заявки

- [ ] Отправить тестовую заявку с публичного сайта.
- [ ] Проверить путь: публичный сайт -> backend API -> БД.
- [ ] Убедиться, что заявка видна в Django Admin.
- [ ] Убедиться, что заявка видна во Vue Admin.
- [ ] При подключенном Telegram убедиться, что уведомление о заявке отправляется.
- [ ] При ошибке Telegram заявка всё равно сохраняется.

## 8. SEO-аудит

- [ ] Открыть SEO-раздел во Vue Admin.
- [ ] Ввести домен и нажать «Запустить аудит».
- [ ] Проверить создание `SEOAudit`, `SEOPage`, `SEOIssue`.
- [ ] Проверить вкладки/данные: последний аудит, страницы, проблемы.

## 9. PDF-отчёты

- [ ] Скачать PDF из SEO-аудита (`export`).
- [ ] Проверить кириллицу и отсутствие проблем кодировки.
- [ ] Проверить наличие summary, страниц, проблем, рекомендаций.

## 10. Ежедневный PDF-отчёт

- [ ] Проверить ручной запуск:
```bash
docker compose exec backend python manage.py send_daily_reports
```
- [ ] Если Telegram не подключен, команда не падает.
- [ ] Если Telegram подключен, PDF отправляется в Telegram.

## 11. Telegram polling

- [ ] Проверить сервис polling:
```bash
docker compose ps telegram_polling
docker compose logs -f telegram_polling
```
- [ ] Альтернативный запуск команды:
```bash
docker compose exec backend python manage.py telegram_polling
```

## 12. Тесты

- [ ] Запустить backend-тесты:
```bash
docker compose exec backend python manage.py test --noinput
```
- [ ] Проверить успешное завершение тестов.

## 13. Финальная фиксация

- [ ] Повторно выполнить `docker compose up -d --build`.
- [ ] Проверить `docker compose ps`.
- [ ] Зафиксировать результаты ручного и автоматического e2e-прогона.
