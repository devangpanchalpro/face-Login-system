#!/bin/bash
set -e

echo "============================================"
echo "  🎭 Face Login System - Starting Up..."
echo "============================================"

echo ""
echo "🔄 Running database migrations..."
python manage.py makemigrations accounts --noinput
python manage.py migrate --noinput

echo ""
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

echo ""

# Use gunicorn in production, runserver in development
if [ "$DEBUG" = "1" ]; then
    echo "============================================"
    echo "  🚀 DEV Server at http://0.0.0.0:8000"
    echo "============================================"
    python manage.py runserver 0.0.0.0:8000
else
    echo "============================================"
    echo "  🚀 PROD Server (gunicorn) at port $PORT"
    echo "============================================"
    gunicorn facelogin.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers 2 \
        --timeout 120 \
        --access-logfile -
fi
