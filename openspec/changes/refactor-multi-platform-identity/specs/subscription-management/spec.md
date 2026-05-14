## ADDED Requirements

### Requirement: Subscription Keyed by user_id
The `UserSubscription` model SHALL use `user_id` (FK → users.id, unique) as its primary lookup key
instead of `bale_user_id`. There SHALL be at most one active subscription row per canonical user.

#### Scenario: Free subscription created for new Bale user
- **WHEN** a Bale user completes the contact registration flow
- **THEN** `subscription_service.get_or_create_free(db, user_id)` creates or returns a free-tier `UserSubscription` keyed by `user_id`

#### Scenario: Paid plan activated after payment
- **WHEN** `activate_plan(db, user_id, plan_key, ...)` is called after a confirmed payment
- **THEN** the subscription row for `user_id` is updated with the new plan details

### Requirement: Subscription Service Accepts user_id
The `subscription_service` SHALL expose all public functions (`get_or_create_free`,
`check_rate_limit`, `record_usage`, `activate_plan`) with `user_id: UUID` as the user-identity
parameter and SHALL NOT accept or reference `bale_user_id`.

#### Scenario: Rate limit checked by canonical user
- **WHEN** a chat request arrives from any channel
- **THEN** `check_rate_limit(db, user_id)` enforces the budget regardless of which platform the request came from

#### Scenario: Usage recorded against user_id
- **WHEN** an LLM response is generated for a user
- **THEN** `record_usage(db, user_id, cost_usd)` increments `used_usd` on the `UserSubscription` row for that `user_id`

### Requirement: Agent Thread and Memory Keyed by user_id
The `AgentBridge` SHALL use `f"user-{user_id}"` as the LangGraph thread ID and
`user_{user_id}.md` as the memory file name. No platform-specific identifier SHALL appear in
thread or memory keys.

#### Scenario: New session uses user-scoped thread ID
- **WHEN** `agent_bridge.invoke_reply_with_status` is called for a Bale user
- **THEN** the LangGraph thread key is `f"user-{user_id}"` where `user_id` is the canonical UUID

#### Scenario: Memory file path uses user_id
- **WHEN** the agent reads or writes per-user memory
- **THEN** the file path is `user_memories/user_{user_id}.md`
