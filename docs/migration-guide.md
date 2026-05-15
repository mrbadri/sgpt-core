# Database Migration Guide

## 1. Normal Flow — When You Change a Model

Follow these steps every time you add, remove, or modify a SQLAlchemy model.

### Step 1 — Start the dev environment (if not already running)

```bash
make dev-up
```

### Step 2 — Check current migration state

```bash
make migrate-current   # shows active revision
make migrate-history   # shows full migration chain
```

### Step 3 — Generate a new migration from your model changes

```bash
make migrate-create MESSAGE='describe what changed'
# Example:
make migrate-create MESSAGE='add email column to user table'
```

This runs `alembic revision --autogenerate` inside the backend container and creates a new file in `backend/src/app/db/migrations/versions/`.

> **Always review the generated file before applying.** Autogenerate misses some things (e.g. constraints, enum changes, custom types).

### Step 4 — Apply the migration

```bash
make migrate
```

This runs `alembic upgrade head` — applies all pending migrations up to the latest.

### Step 5 — Verify

```bash
make migrate-current   # should show the new revision as current
```

---

## 2. Rolling Back — Undo the Last Migration

```bash
make migrate-downgrade   # downgrades one revision at a time
```

Repeat as needed. Check state after each step:

```bash
make migrate-current
```

To downgrade to a specific revision:

```bash
make migrate-upgrade REVISION='<revision_id>'
# revision_id is the hash prefix in the filename, e.g. db303d6d9349
```

---

## 3. Disaster Recovery — Migrations Are Broken or Destroyed

Use this when migration files are deleted, corrupted, or out of sync with the database.

### Option A — Full reset (dev only, data will be lost)

```bash
# Step 1: Tear down everything including the database volume
make dev-down-v

# Step 2: Start fresh
make dev-up

# Step 3: Delete all existing migration files
rm backend/src/app/db/migrations/versions/*.py

# Step 4: Generate one single initial migration from current models
make migrate-create MESSAGE='initial'

# Step 5: Apply it
make migrate
```

### Option B — Keep the database, reset migration history only

Use this when the database schema is correct but Alembic's tracking is broken.

```bash
# Step 1: Open a DB shell
make shell-db
# Inside the container:
psql -U bale_bot -d bale_bot
# Then drop the alembic version table:
DROP TABLE alembic_version;
\q
exit

# Step 2: Delete all migration files
rm backend/src/app/db/migrations/versions/*.py

# Step 3: Create a fresh initial migration
make migrate-create MESSAGE='initial'

# Step 4: Stamp the DB as already at head WITHOUT running SQL
# (because schema already exists)
# Run this inside the backend container:
make shell-backend
# Inside container:
cd /app && PYTHONPATH=/app/src uv run alembic -c alembic.ini stamp head
exit
```

---

## 4. Quick Reference

| Command | What it does |
|---|---|
| `make dev-up` | Start dev environment |
| `make dev-down` | Stop dev environment |
| `make dev-down-v` | Stop dev environment + delete DB volume |
| `make migrate` | Apply all pending migrations (upgrade to head) |
| `make migrate-create MESSAGE='...'` | Generate new migration from model changes |
| `make migrate-current` | Show current revision |
| `make migrate-history` | Show full migration history |
| `make migrate-downgrade` | Rollback one revision |
| `make migrate-upgrade REVISION='...'` | Go to a specific revision |
| `make shell-backend` | Shell into backend container |
| `make shell-db` | Shell into DB container |
