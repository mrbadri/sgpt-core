#!/bin/bash
set -e

# Use the image venv explicitly (avoids system python without deps; never invokes `uv run`).
VENV_PY="${VENV_PY:-/app/.venv/bin/python}"

# Host/port for log line only (connect uses DATABASE_URL via urllib in Python below).
# JDBC-style URLs must include @host: postgresql://USER:PASSWORD@HOST:PORT/DB
read -r host port <<EOF
$("$VENV_PY" -c "
from urllib.parse import urlparse
import os
p = urlparse(os.environ.get('DATABASE_URL', ''))
print(p.hostname or 'db')
print(p.port or 5432)
")
EOF

host=${host:-db}
port=${port:-5432}

# Tune via environment if needed
MAX_RETRIES=${DB_WAIT_MAX_RETRIES:-20}
SLEEP_SECONDS=${DB_WAIT_SLEEP_SECONDS:-2}

echo "Waiting for PostgreSQL at $host:$port..."

attempt=1
while [ "$attempt" -le "$MAX_RETRIES" ]; do
    # Pass fallbacks via env so bash never injects an empty token into Python (SyntaxError).
    if WAIT_DB_HOST="$host" WAIT_DB_PORT="$port" "$VENV_PY" -c '
import os
import sys
import psycopg2
from urllib.parse import urlparse

database_url = os.getenv("DATABASE_URL", "")
parsed = urlparse(database_url) if database_url else None
fallback_host = os.environ["WAIT_DB_HOST"]
fallback_port = int(os.environ["WAIT_DB_PORT"])

try:
    conn = psycopg2.connect(
        host=(parsed.hostname if parsed and parsed.hostname else fallback_host),
        port=(parsed.port if parsed and parsed.port else fallback_port),
        user=(parsed.username if parsed else None),
        password=(parsed.password if parsed else None),
        database=(parsed.path[1:] if parsed and parsed.path else "bale_bot"),
        connect_timeout=2,
    )
    conn.close()
    sys.exit(0)
except Exception as exc:
    print(f"DB check failed: {exc}", file=sys.stderr)
    sys.exit(1)
' >/dev/null; then
        echo "PostgreSQL is up - executing command"
        exit 0
    fi

    echo "PostgreSQL is unavailable (attempt ${attempt}/${MAX_RETRIES}) - sleeping ${SLEEP_SECONDS}s"
    sleep "$SLEEP_SECONDS"
    attempt=$((attempt + 1))
done

echo "PostgreSQL did not become ready after ${MAX_RETRIES} attempts." >&2
exit 1
