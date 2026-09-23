#!/bin/sh
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

if [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput || true
fi

exec gunicorn core.wsgi:application --bind 0.0.0.0:8080 --workers 2 --threads 4 --timeout 60
