#!/bin/sh
echo "Running Alembic migrations..."
poetry run alembic upgrade head

echo "Starting application..."
exec poetry run python ./app/main.py