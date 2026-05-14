# Change: Refactor DB to Multi-Platform Identity Architecture

## Why

The entire data model is locked to the Bale messenger platform: `bale_user_id` is the primary
identity key across `users`, `messages`, `payments`, and `subscriptions`. Adding any new channel
(Web, Telegram, mobile app) requires a parallel DB schema and breaks unified analytics, payments,
and AI memory. This change decouples user identity from the delivery platform.

## What Changes

- **BREAKING** — Add `user_identities` table: one row per (provider, provider_user_id) pair, linked to `users.id`
- **BREAKING** — Remove `bale_user_id` from `users`; add nullable `email`
- **BREAKING** — Remove `bale_user_id` from `messages`; rename model `BaleMessage → Message`; add `channel` field
- **BREAKING** — Replace `bale_user_id` with `user_id` FK in `payments`; rename `BalePayment → Payment`; add `provider` and `status` fields
- **BREAKING** — Replace `bale_user_id` with `user_id` FK in `subscriptions`
- Update all services to accept `user_id` (UUID) instead of `bale_user_id`; Bale handlers resolve `bale_user_id → user_id` early via `user_identities`
- Update `agent_bridge.py`: thread ID `bale-{tid}` → `user-{user_id}`; memory files `user_{tid}.md` → `user_{user_id}.md`
- Alembic data migration: backfill `user_identities` from existing `users.bale_user_id` values

## Impact

- Affected specs: `user-identity` (new), `message-logging` (new), `payment-processing` (new), `subscription-management` (new)
- Affected code:
  - `backend/src/app/models/` — all four model files
  - `backend/src/app/services/` — all five service files
  - `backend/src/integrations/bale/handlers/` — all handler files
  - Alembic migrations directory
- No external API contract changes (Bale webhook interface unchanged)
- Existing Bale users are preserved through the data migration
