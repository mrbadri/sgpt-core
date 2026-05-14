## ADDED Requirements

### Requirement: User Identity Table
The system SHALL maintain a `user_identities` table that links canonical `users.id` records to
platform-specific credentials. Each row represents one (provider, provider_user_id) pair. The
combination of `provider` and `provider_user_id` SHALL be unique across the table.

#### Scenario: Bale user linked on first contact
- **WHEN** a Bale user shares their contact for the first time
- **THEN** a `user_identities` row is created with `provider="bale"` and `provider_user_id=str(bale_user_id)`, linked to the canonical `users.id`

#### Scenario: Duplicate identity rejected
- **WHEN** a second attempt is made to link the same (provider, provider_user_id) pair to a different user
- **THEN** the operation is rejected and the existing link is preserved

### Requirement: Identity-Based User Lookup
The system SHALL provide a lookup function `fetch_user_by_identity(provider, provider_user_id)`
that returns the canonical `User` for the given platform credentials, or `None` if no match exists.
All handlers and services SHALL use this function instead of querying `bale_user_id` directly on `users`.

#### Scenario: Known Bale user resolved
- **WHEN** a Bale message arrives with a known `bale_user_id`
- **THEN** `fetch_user_by_identity("bale", str(bale_user_id))` returns the linked `User`

#### Scenario: Unknown identity returns None
- **WHEN** `fetch_user_by_identity` is called with a provider_user_id that has no matching row
- **THEN** `None` is returned and the caller handles first-time registration

### Requirement: Platform-Agnostic User Record
The `users` table SHALL NOT contain any platform-specific identifier columns. User profile fields
SHALL be limited to: `id` (UUID PK), `first_name`, `last_name`, `mobile` (nullable), `email`
(nullable), `created_at`, `updated_at`.

#### Scenario: User exists without Bale identity
- **WHEN** a user is created via the Web channel
- **THEN** a `users` row is created with no `bale_user_id`; the web credential is stored only in `user_identities`

#### Scenario: Data migration preserves existing Bale users
- **WHEN** the Alembic migration runs on a database containing `users.bale_user_id` values
- **THEN** each non-null `bale_user_id` is backfilled into `user_identities` with `provider="bale"` before the column is dropped
