# Design: Multi-Platform Identity

## Context

StudyGPT currently uses a "platform-first" identity model where `bale_user_id` is the primary
user key embedded in every table. The desired "user-first" model (used by Google, Stripe, Slack,
Discord) separates the canonical user record from platform-specific credentials.

Stakeholders: backend engineer (mrbadri), future platform integrations (Web, Telegram).

## Goals / Non-Goals

- **Goals:**
  - A single `users` row represents one real person regardless of how they joined
  - Any platform can resolve its local user ID to the canonical `users.id` via `user_identities`
  - Payments, subscriptions, messages, and AI memory all unify under one `user_id`
  - Zero data loss for existing Bale users

- **Non-Goals:**
  - Implementing the Web or Telegram channel (that is a separate change)
  - Merging duplicate accounts (out of scope for this change)
  - Changing the Bale webhook interface or bot UX

## Decisions

### Decision: Separate `user_identities` table (not a JSON column)
A dedicated table with a unique index on `(provider, provider_user_id)` gives fast indexed
lookups, clean FK integrity, and is easy to extend. A JSON column on `users` would require
application-level uniqueness enforcement and complicate indexing.

Alternatives considered:
- One nullable column per provider on `users` (e.g., `bale_user_id`, `telegram_user_id`) — rejected:
  schema changes needed for every new platform, violates open/closed.
- JSONB `identities` column on `users` — rejected: loses FK integrity and indexed lookups.

### Decision: `provider_user_id` stored as `str`
Platform IDs vary by type (int for Bale/Telegram, string for web tokens). Storing as `str` avoids
type mismatch and keeps the model uniform. Application layer casts as needed.

### Decision: `channel` on messages, `provider` on payments (separate names)
`channel` describes the delivery medium of a message (where it was sent/received).
`provider` describes the payment gateway (who processed money). Different semantics → different names.

### Decision: Thread ID migrated from `bale-{tid}` to `user-{user_id}`
LangGraph thread IDs encode conversation history. After migration, all new interactions use
`user-{user_id}`. Existing threads are not migrated (history is preserved in FalkorDB graph memory,
which is keyed by `bale_tid` in Graphiti episode metadata — cross-reference if needed).

## Risks / Trade-offs

- **LangGraph thread continuity** — Existing Bale sessions use `bale-{tid}` thread IDs. After the
  migration cutover, new sessions use `user-{uuid}`, so in-flight LangGraph state is lost.
  Mitigation: accept the one-time session break; Graphiti long-term memory is unaffected.
- **Memory file rename** — `user_{bale_tid}.md` files need to be renamed to `user_{user_id}.md`
  for existing users. A migration script should perform this rename.
  Mitigation: include file rename step in the migration task.
- **Alembic data migration complexity** — The migration must handle NULL `bale_user_id` on `users`
  (if any) gracefully and must be idempotent.

## Migration Plan

1. Add `user_identities` table (new Alembic migration).
2. Add `email` column to `users`, backfill `user_identities` from `users.bale_user_id`.
3. Add `user_id` FK + `channel` to `messages`; backfill `user_id` from existing `bale_user_id → users` join; drop `bale_user_id` column.
4. Add `user_id` FK + `provider` + `status` to `payments`; backfill `user_id` via `user_identities`; drop `bale_user_id`.
5. Add `user_id` FK to `subscriptions`; backfill; drop `bale_user_id`.
6. Remove `bale_user_id` from `users`.
7. Rename memory files on disk: `user_{bale_tid}.md → user_{user_id}.md`.
8. Rollback strategy: keep a `_bale_user_id_backup` column during migration window, drop after validation.

## Open Questions

- Should `email` on `users` be unique or just nullable? (Web login will likely require unique-nullable)
- Should existing LangGraph `bale-{tid}` thread state be migrated or simply abandoned?
