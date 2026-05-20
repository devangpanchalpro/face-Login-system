#!/bin/bash
set -e

echo "============================================"
echo "  🎭 Face Login System - Starting Up..."
echo "  ⚡ Powered by InsightFace (ArcFace)"
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

# Check if vector dimension needs migration (128 → 512)
echo ""
echo "🔍 Checking vector dimensions..."
python -c "
import dj_database_url, os, psycopg2
url = os.environ.get('DATABASE_URL', 'postgres://facelogin:facelogin_secret@db:5432/facelogin')
conf = dj_database_url.parse(url)
conn = psycopg2.connect(dbname=conf['NAME'], user=conf['USER'], password=conf['PASSWORD'], host=conf['HOST'], port=conf['PORT'])
conn.autocommit = True
cur = conn.cursor()

# Check if the old 128-d tables exist and need migration
cur.execute(\"\"\"
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'accounts_faceencoding' AND column_name = 'encoding'
    )
\"\"\")
table_exists = cur.fetchone()[0]

if table_exists:
    # Check current vector dimension
    cur.execute(\"\"\"
        SELECT atttypmod FROM pg_attribute
        WHERE attrelid = 'accounts_faceencoding'::regclass AND attname = 'encoding'
    \"\"\")
    row = cur.fetchone()
    if row and row[0] > 0:
        current_dim = row[0]
        if current_dim != 512:
            print(f'⚠️  Vector dimension is {current_dim}, need 512. Resetting face data...')
            cur.execute('DROP TABLE IF EXISTS accounts_faceencoding CASCADE')
            cur.execute('DROP TABLE IF EXISTS accounts_loginhistory CASCADE')
            cur.execute('DROP TABLE IF EXISTS accounts_faceuser CASCADE')
            cur.execute(\"DELETE FROM django_migrations WHERE app = 'accounts'\")
            print('✅ Old tables dropped + migration records cleared. Fresh migration will recreate with 512-d vectors.')
        else:
            print('✅ Vector dimensions are already 512-d')
    else:
        print('✅ No dimension check needed (new install)')
else:
    print('✅ Fresh install — no migration needed')

cur.close()
conn.close()
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
    echo "  🧠 AI Engine: InsightFace ArcFace (512-d)"
    echo "============================================"
    python manage.py runserver 0.0.0.0:8000
else
    echo "============================================"
    echo "  🚀 PROD Server (gunicorn) at port $PORT"
    echo "  📊 Database: PostgreSQL + pgvector"
    echo "  🧠 AI Engine: InsightFace ArcFace (512-d)"
    echo "============================================"
    gunicorn facelogin.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers 2 \
        --timeout 120 \
        --access-logfile -
fi
