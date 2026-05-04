#!/bin/bash
set -e

# Run database migrations using Alembic

echo "Running database migrations..."

# Change to backend directory
cd "$(dirname "$0")/.."

# Run migrations through uv-managed environment
uv run alembic upgrade head

echo "Migrations completed successfully."
