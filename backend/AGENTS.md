# Backend Agent Notes

## Scope
- Applies to everything under `backend/`.
- Backend is a FastAPI + SQLModel service for the Bale bot, subscriptions/payments, and a LangGraph/Graphiti deep-agent bridge.
- Root repo commit messages must follow `.cursorrules`: `<emoji> type(scope): imperative subject` with the exact emoji/type pairing.

## Project Layout
- `src/app/main.py` creates the FastAPI app, registers routers, initializes DB, and starts Bale polling when `BALE_BOT_TOKEN` is set.
- `src/app/settings.py` defines env-driven settings. It reads `.env` and `../.env`; never commit real secrets.
- `src/app/models/` contains SQLModel tables. Import new models in `src/app/models/__init__.py` so Alembic metadata sees them.
- `src/app/services/` holds database/business logic decoupled from HTTP and bot adapters.
- `src/integrations/bale/` contains TeleBot integration, client helpers, formatting, and message handlers.
- `src/app/agent/` and `src/app/knowledge_graph/` contain the LangGraph/Graphiti agent and search wiring.
- `src/app/db/migrations/versions/` contains Alembic migrations.
- `tests/` contains unit and integration tests.

## Setup And Commands
- Work from `backend/` for Python commands unless using root `make` targets.
- Install/sync deps: `uv sync --extra dev`.
- Run app locally: `PYTHONPATH=src uv run uvicorn app.main:app --reload`.
- Run tests locally: `PYTHONPATH=src uv run pytest`.
- Run a focused test: `PYTHONPATH=src uv run pytest tests/path/to/test.py -v`.
- Create migration: `PYTHONPATH=src uv run alembic -c alembic.ini revision --autogenerate -m "message"`.
- Apply migrations: `PYTHONPATH=src uv run alembic -c alembic.ini upgrade head`.
- Docker-backed equivalents are in the root `Makefile` (`make test`, `make test-unit`, `make migrate`, etc.).

## Coding Conventions
- Python 3.11+, line length 100, Black/Ruff-compatible style.
- Prefer small service functions and keep TeleBot/FastAPI handlers thin.
- Use `sqlmodel.Session` for DB work. Commit/refresh in services that create or mutate persisted records; callers should rollback and close sessions on errors.
- Keep bot message logging best-effort: logging failures must not block or break user-facing replies.
- Use `app.*` imports for application modules and `integrations.*` for integration modules; keep `PYTHONPATH=src` in local commands.
- Avoid adding broad `except Exception` unless matching existing adapter boundaries where external APIs/bot handlers must not crash the process.

## Database And Models
- Models typically inherit from `BaseDBModel` (integer id) or `BaseDBModelUUID` (UUID string id).
- For integer IDs from Bale or prices, use SQLAlchemy `BigInteger` via `sa_type=sa.BigInteger`.
- When relating another table to `User`, use `user.id` as the foreign key target. Keep `bale_user_id` as an external Bale identifier, not as a relational foreign key.
- When adding tables/columns, update models, import exports, and add an Alembic migration.
- Existing migrations use timestamped filenames like `YYYYMMDD_HHMM-<rev>_<message>.py`.

## Tests
- Tests default to SQLite in-memory when neither `TEST_DATABASE_URL` nor `DATABASE_URL` is set.
- `tests/conftest.py` creates/drops metadata using `app.db.base.Base`; ensure new models are registered before `create_all`.
- Add or update tests near the behavior changed, especially for services and bot flow edge cases.

## Operational Notes
- `BALE_BOT_TOKEN` controls whether polling starts during app lifespan.
- `BALE_PAYMENT_PROVIDER_TOKEN`, `BALE_API_URL`, `BALE_REQUIRED_CHANNELS`, and `USER_MEMORIES_DIR` affect bot/payment/agent behavior.
- Agent calls may touch external LLM/Graphiti services; prefer mocking or focused unit tests rather than live network calls.
- Be careful with `.env`, user memory files, `.venv/`, `.langgraph_api/`, and generated caches.
