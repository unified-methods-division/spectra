#!/bin/bash
set -e

echo "Waiting for database..."
until uv run python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
print('Database ready.')
" 2>/dev/null; do
  sleep 2
done

if [ "${RUN_MIGRATIONS}" = "1" ]; then
  echo "Running database migrations..."
  uv run python manage.py migrate --noinput

  if [ "$1" = "gunicorn" ]; then
      echo "Collecting static files..."
      uv run python manage.py collectstatic --noinput
  fi
fi

exec "$@"