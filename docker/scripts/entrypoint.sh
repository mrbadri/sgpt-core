#!/bin/bash
set -e

# Wait for database to be ready
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    /docker-scripts/wait_for_db.sh
fi

# Run database migrations (use root alembic.ini, PYTHONPATH for app imports)
echo "Running database migrations..."
cd /app && PYTHONPATH=/app/src uv run alembic -c alembic.ini upgrade head

# Execute the main command
exec "$@"
