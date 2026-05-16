#!/bin/bash
set -e

echo "============================================"
echo "  🎭 Face Login System - Starting Up..."
echo "============================================"

# Wait for PostgreSQL to be ready
echo ""
echo "⏳ Waiting for PostgreSQL..."
until python -c "
import dj_database_url, os, psycopg2
url = os.environ.get('DATABASE_URL', 'postgres://facelogin:facelogin_secret@db:5432/facelogin')
conf = dj_database_url.parse(url)
psycopg2.connect(dbname=conf['NAME'], user=conf['USER'], password=conf['PASSWORD'], host=conf['HOST'], port=conf['PORT'])
" 2>/dev/null; do
    echo "   PostgreSQL not ready, retrying in 2s..."
    sleep 2
done
echo "✅ PostgreSQL is ready!"

# Enable pgvector extension
echo ""
echo "🔌 Enabling pgvector extension..."
python -c "
import dj_database_url, os, psycopg2
url = os.environ.get('DATABASE_URL', 'postgres://facelogin:facelogin_secret@db:5432/facelogin')
conf = dj_database_url.parse(url)
conn = psycopg2.connect(dbname=conf['NAME'], user=conf['USER'], password=conf['PASSWORD'], host=conf['HOST'], port=conf['PORT'])
conn.autocommit = True
cur = conn.cursor()
cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
cur.close()
conn.close()
print('✅ pgvector extension enabled')
"

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
    echo "  📊 Database: PostgreSQL + pgvector"
    echo "============================================"
    python manage.py runserver 0.0.0.0:8000
else
    echo "============================================"
    echo "  🚀 PROD Server (gunicorn) at port $PORT"
    echo "  📊 Database: PostgreSQL + pgvector"
    echo "============================================"
    gunicorn facelogin.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers 2 \
        --timeout 120 \
        --access-logfile -
fi
