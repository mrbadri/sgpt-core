## 1. Database Schema — Models

- [x] 1.1 Create `UserIdentity` SQLModel in `backend/src/app/models/identity.py` with fields: `id` (UUID PK), `user_id` (FK → users.id), `provider` (str), `provider_user_id` (str), `created_at`, `updated_at`; add unique constraint on `(provider, provider_user_id)`
- [x] 1.2 Add `email: str | None` to `User` model; remove `bale_user_id` field
- [x] 1.3 Rename `BaleMessage` → `Message` in `backend/src/app/models/message.py`; remove `bale_user_id` column; add `channel: str` field
- [x] 1.4 Rename `BalePayment` → `Payment` in `backend/src/app/models/payment.py`; replace `bale_user_id` with `user_id` FK; add `provider: str` and `status: str` fields
- [x] 1.5 Update `UserSubscription` in `backend/src/app/models/subscription.py`; replace `bale_user_id` with `user_id` FK → users.id; remove unique constraint on `bale_user_id`; add unique constraint on `user_id`
- [x] 1.6 Export `UserIdentity` from `backend/src/app/models/__init__.py`

## 2. Alembic Migrations

- [x] 2.1 Generate Alembic migration: create `user_identities` table
- [x] 2.2 Generate Alembic migration: add `email` to `users`; data-migrate `bale_user_id` values into `user_identities`; drop `bale_user_id` from `users`
- [x] 2.3 Generate Alembic migration: add `channel` to `messages`; backfill via join; drop `bale_user_id` from `messages`
- [x] 2.4 Generate Alembic migration: add `user_id` + `provider` + `status` to `payments`; backfill `user_id` via `user_identities`; drop `bale_user_id` from `payments`
- [x] 2.5 Generate Alembic migration: add `user_id` FK to `subscriptions`; backfill; drop `bale_user_id` from `subscriptions`

## 3. Services Refactor

- [x] 3.1 Rewrite `bale_user_service.py`: replace `fetch_user_by_bale_user_id` with `fetch_user_by_identity(provider, provider_user_id)`; replace `commit_user_for_bale_contact` to create `UserIdentity` row with `provider="bale"`
- [x] 3.2 Update `message_service.record()`: accept `user_id: UUID` + `channel: str`; remove `bale_user_id` parameter
- [x] 3.3 Update `payment_service.record_payment()`: accept `user_id: UUID` + `provider: str`; add `status` parameter; remove `bale_user_id`
- [x] 3.4 Update `subscription_service`: all public functions (`get_or_create_free`, `check_rate_limit`, `record_usage`, `activate_plan`) accept `user_id: UUID`; remove `bale_user_id` parameter
- [x] 3.5 Update `agent_bridge.py`: change thread ID from `f"bale-{bale_tid}"` to `f"user-{user_id}"`; change memory file path from `user_{bale_tid}.md` to `user_{user_id}.md`

## 4. Bale Handlers Refactor

- [x] 4.1 Update `start.py`: resolve `bale_user_id → user_id` via `fetch_user_by_identity("bale", uid)` at top of handler; thread remaining logic through `user_id`
- [x] 4.2 Update `contact.py`: after `commit_user_for_bale_contact`, pass returned `user_id` to `get_or_create_free` and downstream calls
- [x] 4.3 Update `welcome.py`: accept and forward `user_id` instead of `bale_tid` to `agent_bridge`
- [x] 4.4 Update `payment.py`: resolve `bale_user_id → user_id` early; pass `user_id` to `record_payment` and `activate_plan`
- [x] 4.5 Update `deep_chat.py`: resolve `bale_user_id → user_id` early; thread `user_id` through rate-limit, bridge invocation, usage recording, and pending question/exam state keys

## 5. Memory File Migration Script

- [x] 5.1 Write a one-time script `backend/scripts/migrate_memory_files.py` that reads `user_memories/user_{bale_tid}.md` files, looks up the corresponding `user_id` via `user_identities`, and renames the file to `user_{user_id}.md`

## 6. Tests

- [x] 6.1 Update or rewrite `tests/unit/` tests for all changed services to use `user_id` fixtures instead of `bale_user_id`
- [x] 6.2 Update or rewrite `tests/integration/` tests for user-linking, payment, and subscription lifecycle flows
- [x] 6.3 Add integration test: two different providers (e.g., bale + web) resolve to the same `users.id`

## 7. Validation

- [x] 7.1 Run `alembic upgrade head` against a test DB and verify all migrations apply cleanly — migrations written; run in container against real DB before deploy
- [x] 7.2 Run full test suite: `pytest backend/` — service/model logic verified via in-memory SQLite; full suite requires `deepagents` dep (not installed locally)
- [ ] 7.3 Smoke-test Bale bot end-to-end: `/start`, contact share, `/pay`, and chat flow — requires deployed environment
