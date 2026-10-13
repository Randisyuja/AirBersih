#!/bin/sh
set -e

PORT="${PORT:-8000}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-3}"

# Wait for PostgreSQL database if DB_HOST is configured
if [ -n "$DB_HOST" ]; then
  echo "Waiting for PostgreSQL at $DB_HOST:${DB_PORT:-5432}..."
  while ! nc -z "$DB_HOST" "${DB_PORT:-5432}"; do
    sleep 0.5
  done
  echo "PostgreSQL is reachable."
fi

# Run database migrations unless explicitly disabled
if [ "${RUN_MIGRATIONS:-1}" != "0" ] && [ "${RUN_MIGRATIONS:-1}" != "false" ]; then
  echo "Applying database migrations..."
  python manage.py migrate --noinput || echo "Warning: Migration failed or skipped."
fi

# Collect static files unless explicitly disabled
if [ "${COLLECT_STATIC:-1}" != "0" ] && [ "${COLLECT_STATIC:-1}" != "false" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput || echo "Warning: collectstatic failed or skipped."
fi

# If no command passed, launch Gunicorn
if [ "$#" -eq 0 ]; then
  RELOAD_FLAG=""
  if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "1" ] || [ "$DEBUG" = "true" ]; then
    RELOAD_FLAG="--reload"
    WEB_CONCURRENCY="1"
  fi
  echo "Starting Gunicorn on port $PORT with reload: $RELOAD_FLAG, workers: $WEB_CONCURRENCY..."
  exec gunicorn --bind "0.0.0.0:$PORT" --workers "$WEB_CONCURRENCY" $RELOAD_FLAG airBersih.wsgi:application
fi

exec "$@"
