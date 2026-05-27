#!/bin/sh
set -e

python - <<'PY'
import os
import time

import psycopg

host = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "postgres"))
port = int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432")))
user = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres"))
password = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "postgres"))
dbname = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "django_db"))

max_attempts = 60
for attempt in range(1, max_attempts + 1):
    try:
        with psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
        ):
            print("PostgreSQL is ready")
            break
    except Exception as exc:
        print(f"Waiting for PostgreSQL ({attempt}/{max_attempts}): {exc}")
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL did not become ready in time")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_demo_data

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}"