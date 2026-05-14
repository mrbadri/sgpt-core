## ADDED Requirements

### Requirement: Platform-Agnostic Message Model
The system SHALL store messages in a `Message` model (previously `BaleMessage`) that records the
delivery channel alongside the canonical `user_id`. The `bale_user_id` denormalized column SHALL be
removed. The `channel` field SHALL accept the values `"bale"`, `"web"`, or `"telegram"`.

#### Scenario: Bale inbound message logged
- **WHEN** a Bale user sends a text message
- **THEN** a `Message` row is created with `user_id` set to the canonical user UUID, `channel="bale"`, and `direction="in"`

#### Scenario: Outbound reply logged with channel
- **WHEN** the bot sends a reply to a Bale user
- **THEN** a `Message` row is created with `channel="bale"` and `direction="out"`, linked to the same `user_id`

### Requirement: Message Service Accepts user_id
The `message_service.record()` function SHALL accept `user_id: UUID` and `channel: str` as
parameters instead of `bale_user_id`. It SHALL NOT perform a `bale_user_id` lookup internally.

#### Scenario: Handler passes resolved user_id
- **WHEN** a Bale handler calls `message_service.record()`
- **THEN** the handler provides the `user_id` already resolved from `user_identities`, not the raw `bale_user_id`
