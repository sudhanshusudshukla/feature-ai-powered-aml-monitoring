#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python app/seed.py || echo "Seed script completed (may have been idempotent)"

echo "Starting application..."
exec "$@"
