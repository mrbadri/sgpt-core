#!/bin/bash
set -e

# Extract host and port from DATABASE_URL
# Format: postgresql://user:password@host:port/database
host=$(echo "${DATABASE_URL:-}" | sed -E 's|.*@([^:]+):.*|\1|')
port=$(echo "${DATABASE_URL:-}" | sed -E 's|.*:([0-9]+)/.*|\1|')

# Default values if parsing fails
host=${host:-db}
port=${port:-5432}

# Tune via environment if needed
MAX_RETRIES=${DB_WAIT_MAX_RETRIES:-20}
SLEEP_SECONDS=${DB_WAIT_SLEEP_SECONDS:-2}

echo "Waiting for PostgreSQL at $host:$port..."

attempt=1
while [ "$attempt" -le "$MAX_RETRIES" ]; do
    if uv run python -c "
import os
import sys
import psycopg2
from urllib.parse import urlparse

database_url = os.getenv('DATABASE_URL', '')
parsed = urlparse(database_url) if database_url else None

try:
    conn = psycopg2.connect(
        host=(parsed.hostname if parsed and parsed.hostname else '$host'),
        port=(parsed.port if parsed and parsed.port else $port),
        user=(parsed.username if parsed else None),
        password=(parsed.password if parsed else None),
        database=(parsed.path[1:] if parsed and parsed.path else 'bale_bot'),
        connect_timeout=2,
    )
    conn.close()
    sys.exit(0)
except Exception as exc:
    print(f'DB check failed: {exc}', file=sys.stderr)
    sys.exit(1)
" >/dev/null; then
        echo "PostgreSQL is up - executing command"
        exit 0
    fi

    echo "PostgreSQL is unavailable (attempt ${attempt}/${MAX_RETRIES}) - sleeping ${SLEEP_SECONDS}s"
    sleep "$SLEEP_SECONDS"
    attempt=$((attempt + 1))
done

echo "PostgreSQL did not become ready after ${MAX_RETRIES} attempts." >&2
exit 1
