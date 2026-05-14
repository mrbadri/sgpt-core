# Project Context

## Purpose

**SGPT (StudyGPT)** is an intelligent tutoring assistant for Iranian high-school Biology (Grade 11)
students, delivered through the **Bale** messenger platform. It combines a LangGraph-powered AI agent
with a Graphiti knowledge graph (backed by FalkorDB) to answer subject-specific questions,
administer exams, and maintain long-term per-user memory. A subscription system (free / basic / pro)
gates usage and tracks token-level costs in IRR.

---

## Tech Stack

**Backend (Python 3.11+)**
- **FastAPI** + **Uvicorn** — async REST API & webhook server
- **SQLModel** / **SQLAlchemy 2** + **Alembic** — ORM and migrations
- **PostgreSQL 18** — primary relational database
- **LangGraph** + **LangChain** — agent state graph and LLM orchestration
- **deepagents** — high-level deep-agent abstraction
- **graphiti-core** (FalkorDB backend) — knowledge graph management & search
- **FalkorDB** — Redis-backed graph database hosting the Graphiti graph
- **pyTelegramBotAPI** — Bale (Telegram-compatible) bot protocol (long-polling)
- **httpx** — async HTTP client
- **Pydantic v2** + **pydantic-settings** — validation and env-driven config
- **Black** (line-length 100) + **Ruff** — formatting and linting
- **pytest** + **pytest-asyncio** — test framework

**Infrastructure**
- **Docker Compose** (`infrastructure/`) — dev and prod stacks
- **PostgreSQL** (dev: port 5433, prod: internal), **pgAdmin** (port 5050)
- **FalkorDB** (port 6379 internal, 8379 host; browser UI port 3000 internal, 3379 host)
- **Makefile** — task automation (`make prod-up`, `make prod-down-v`, etc.)

---

## Project Conventions

### Code Style
- **Formatter:** Black, line length 100, target Python 3.11
- **Linter:** Ruff, same line length
- Full type hints throughout; `from __future__ import annotations` for forward refs
- Private helpers prefixed with `_` (e.g. `_normalize()`, `_now()`)
- No inline comments explaining *what* — only *why* when non-obvious
- Async/await everywhere; `asyncio.run()` used only to bridge sync bot callbacks into async services

### Naming Conventions
| Layer | Convention | Example |
|---|---|---|
| Services | `*_service.py` | `subscription_service.py` |
| Models | one file per entity in `models/` | `user.py`, `subscription.py` |
| Bot handlers | one file per interaction in `handlers/` | `deep_chat.py`, `payment.py` |
| Config | env-backed Pydantic settings in `config/` | `graphiti.py` |
| API endpoints | grouped by version in `api/v1/endpoints/` | `health.py` |

### Architecture Patterns
- **Layered:** `handlers → services → models/DB` — handlers never touch SQLAlchemy directly
- **Dependency injection:** FastAPI `Depends()` for DB sessions; `BaleHandlerDeps` dataclass for bot handlers
- **Bridge pattern:** `AgentBridge` decouples the LangGraph agent from Bale-specific concerns
- **Custom error hierarchy:** `ApplicationError → ValidationError / NotFoundError / AuthorizationError / PermissionError` — all converted to JSON by exception handlers in `errors/handlers.py`
- **Structured logging:** JSON format in production, text in development; structured fields via `logging.py`

### Testing Strategy
- `tests/unit/` — isolated service and model logic
- `tests/integration/` — full flows (user linking, payment, subscription lifecycle)
- `tests/factories/` — DB-backed test data builders
- `conftest.py` — shared async fixtures
- Run with `pytest` from `backend/`; async tests use `pytest-asyncio`

### Git Workflow
- Branch strategy: feature branch → `main`
- **Commit format:** `<emoji> <type>(<scope>): <imperative summary>; <optional detail>`
  - `✨ feat(topic):` — new feature
  - `🐛 fix(topic):` — bug fix
  - `📦 refactor(topic):` — refactor without behaviour change
  - `🧹 chore:` — tooling / config / housekeeping
- Messages describe **what changed and why**, not just "update X"

---

## Domain Context

- Target audience: Iranian high-school students studying Biology Grade 11
- Interface language: **Persian (Farsi)**; Bale-native Markdown (`*bold*`, `_italic_`, `• bullets`)
- **Bale** is a Telegram-compatible messenger popular in Iran (`https://tapi.bale.ai`)
- Users are identified by **mobile number** (normalized to national digits) linked to a `bale_user_id`
- The **knowledge graph** stores Biology G11 curriculum as graph edges (facts) and episodes (source chunks); searched via RRF or cross-encoder strategy
- **Long-term user memory** is stored as a Markdown file per user (`user_memories/user_{bale_tid}.md`) containing personality notes, learning style, and signup date — prepended to every agent call
- **Exam context injection:** pending exam answers are queued in memory and prepended to the next agent invocation, then cleared
- **Subscription plans:** free / basic / pro — differentiated by monthly USD budget; token costs are $0.50/1M input, $3.00/1M output

---

## Important Constraints

- Persian text can exceed Bale's 4096-char message limit — replies are chunked by `messaging.py`
- Bale API rejects long Persian query strings → custom request sender posts body via POST instead of query params
- FalkorDB browser login uses **Redis ACL username `default`** (not the service hostname); password set via `FALKORDB_PASSWORD` in `.env`
- FalkorDB browser UI connects to `localhost:6379` (internal port), not the host-mapped `8379`
- Special characters (backslash, `@`, `|`) in passwords can break dotenv parsers and browser auth forms — keep `FALKORDB_PASSWORD` free of backslashes
- `PGADMIN_CONFIG_ALLOW_SPECIAL_EMAIL_DOMAINS` must be a **Python literal string** (e.g. `"['local']"`) not a bare value
- All DB operations use async sessions; never call blocking SQLAlchemy methods in async context

---

## External Dependencies

| Service | Purpose | Config env vars |
|---|---|---|
| **Bale Bot API** | Messaging, payments, channel checks | `BALE_BOT_TOKEN`, `BALE_API_URL` |
| **GapGPT / OpenAI-compatible API** | LLM for agent + Graphiti indexing | `GAPGPT_API_KEY`, `AGENT_CHAT_*`, `GRAPHITI_INDEX_LLM_*` |
| **FalkorDB** | Graph DB backing Graphiti | `FALKOR_HOST`, `FALKOR_PORT`, `FALKORDB_PASSWORD`, `FALKOR_DATABASE` |
| **PostgreSQL** | Users, messages, subscriptions, payments | `DATABASE_URL`, `POSTGRES_*` |
| **Graphiti** | Knowledge graph search (RRF / cross-encoder) | `GRAPHITI_INDEX_*`, `GRAPHITI_SEARCH_*` |
| **Embeddings API** | Text embeddings for Graphiti | `GRAPHITI_INDEX_EMBEDDING_*`, `EMBEDDING_*` |
| **pgAdmin** | DB management UI (prod port 5050) | `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD` |
| **LangSmith** (optional) | LangChain tracing | `LANGSMITH_API_KEY`, `LANGCHAIN_TRACING_V2` |

---

## Infrastructure Quick Reference

| Stack | Command | Notes |
|---|---|---|
| Dev up | `make dev-up` | Hot-reload, port 8000, pgAdmin 5050 |
| Prod up | `make prod-up` | Port 8800, FalkorDB browser 3379 |
| Prod down + wipe | `make prod-down-v` | Removes all volumes |
| Migrations | `alembic upgrade head` (inside backend container) | |
| FalkorDB browser | `localhost:3379` | Host `localhost`, port `6379`, user `default` |
| pgAdmin (prod) | `localhost:5050` | Credentials from `PGADMIN_DEFAULT_*` |
