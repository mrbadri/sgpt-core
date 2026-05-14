#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$ROOT_DIR/infrastructure/.env"
BACKUP_DIR="$ROOT_DIR/infrastructure/backup"
DEV_COMPOSE="$ROOT_DIR/infrastructure/docker-compose.dev.yml"
PROD_COMPOSE="$ROOT_DIR/infrastructure/docker-compose.prod.yml"

# ── Load .env ─────────────────────────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found." >&2
  exit 1
fi
set -a; source "$ENV_FILE"; set +a

# ── List backup files ─────────────────────────────────────────────────────────
if [ ! -d "$BACKUP_DIR" ]; then
  echo "ERROR: Backup directory not found: $BACKUP_DIR" >&2
  exit 1
fi

# Collect .sql and .tar.gz files, sorted newest first
FILES=()
while IFS= read -r f; do FILES+=("$f"); done < <(
  find "$BACKUP_DIR" -maxdepth 1 \( -name "*.sql" -o -name "*.tar.gz" \) | sort -r
)

if [ ${#FILES[@]} -eq 0 ]; then
  echo "No backup files found in $BACKUP_DIR" >&2
  echo "Place .sql or .tar.gz (containing postgres.sql) files there to restore." >&2
  exit 1
fi

echo ""
echo "Available backups in infrastructure/backup/:"
for i in "${!FILES[@]}"; do
  printf "  %2d) %s\n" "$((i + 1))" "$(basename "${FILES[$i]}")"
done

echo ""
read -rp "Select backup number [1-${#FILES[@]}]: " CHOICE
if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "${#FILES[@]}" ]; then
  echo "Invalid selection." >&2
  exit 1
fi
SELECTED="${FILES[$((CHOICE - 1))]}"

# ── Choose environment ────────────────────────────────────────────────────────
ENV_ARG="${1:-}"
if [ "$ENV_ARG" = "dev" ]; then
  COMPOSE_FILE="$DEV_COMPOSE"
  ENV_LABEL="development"
elif [ "$ENV_ARG" = "prod" ]; then
  COMPOSE_FILE="$PROD_COMPOSE"
  ENV_LABEL="production"
else
  echo ""
  echo "Restore to:"
  echo "  1) Development"
  echo "  2) Production"
  read -rp "Select [1-2]: " ENV_CHOICE
  case "$ENV_CHOICE" in
    1) COMPOSE_FILE="$DEV_COMPOSE"; ENV_LABEL="development" ;;
    2) COMPOSE_FILE="$PROD_COMPOSE"; ENV_LABEL="production" ;;
    *) echo "Invalid selection." >&2; exit 1 ;;
  esac
fi

# ── Confirm ───────────────────────────────────────────────────────────────────
echo ""
echo "WARNING: This will OVERWRITE the PostgreSQL database in ${ENV_LABEL}."
echo "  File   : $(basename "$SELECTED")"
echo "  Target : ${ENV_LABEL} (${POSTGRES_DB})"
echo ""
read -rp "Type 'yes' to confirm: " CONFIRM
[ "$CONFIRM" = "yes" ] || { echo "Aborted."; exit 1; }

# ── Resolve SQL file ──────────────────────────────────────────────────────────
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

case "$SELECTED" in
  *.tar.gz)
    echo "Extracting postgres.sql from archive..."
    tar -xzf "$SELECTED" -C "$TMPDIR" postgres.sql
    SQL_FILE="$TMPDIR/postgres.sql"
    ;;
  *.sql)
    SQL_FILE="$SELECTED"
    ;;
esac

# ── Restore database ──────────────────────────────────────────────────────────
echo "Terminating active connections..."
docker compose -f "$COMPOSE_FILE" exec -T db \
  psql -U "$POSTGRES_USER" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();" \
  > /dev/null

echo "Dropping and recreating database..."
docker compose -f "$COMPOSE_FILE" exec -T db \
  psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" > /dev/null
docker compose -f "$COMPOSE_FILE" exec -T db \
  psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE ${POSTGRES_DB};" > /dev/null

echo "Restoring data..."
docker compose -f "$COMPOSE_FILE" exec -T db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$SQL_FILE"

echo ""
echo "Restore complete: $(basename "$SELECTED") → ${ENV_LABEL} (${POSTGRES_DB})"
