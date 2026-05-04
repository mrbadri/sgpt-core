#!/bin/bash
set -e

# Extract host and port from DATABASE_URL
# Format: postgresql://user:password@host:port/database
host=$(echo $DATABASE_URL | sed -E 's|.*@([^:]+):.*|\1|')
port=$(echo $DATABASE_URL | sed -E 's|.*:([0-9]+)/.*|\1|')

# Default values if parsing fails
host=${host:-db}
port=${port:-5432}

echo "Waiting for PostgreSQL at $host:$port..."

# Use uv-managed Python to check database connection (pg_isready might not be available)
until uv run python -c "
import sys
import psycopg2
from urllib.parse import urlparse

try:
    # Parse DATABASE_URL
    parsed = urlparse('$DATABASE_URL')
    conn = psycopg2.connect(
        host=parsed.hostname or '$host',
        port=parsed.port or $port,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:] if parsed.path else 'bale_bot',
        connect_timeout=2
    )
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is up - executing command"
