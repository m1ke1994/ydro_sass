# Vue Admin

Клиентская админка Mini CRM на Vue 3 и Vite.

## Локальный запуск

```bash
npm ci
npm run dev
```

По умолчанию админка откроется на `http://localhost:5173`. API берётся из
`VITE_API_BASE_URL`, значение по умолчанию — `http://127.0.0.1:8000`.

## Docker

Запуск backend и Vue Admin:

```bash
docker compose up --build -d backend frontend
```

После запуска:

- Vue Admin: `http://localhost:8001`
- Backend API: `http://localhost:8000`

Для разработки каталог `vue-admin` подключён в контейнер как bind mount.
Изменения подхватываются Vite автоматически.

Полная пересборка frontend:

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

Проверка конфигурации:

```bash
docker compose config
```

## Проверка

```bash
npm run build
```

Проверьте адаптивность в инструментах разработчика браузера на ширинах
1440 px, 768 px и 390 px.
