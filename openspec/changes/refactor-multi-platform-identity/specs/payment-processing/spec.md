## ADDED Requirements

### Requirement: Platform-Agnostic Payment Model
The system SHALL store payments in a `Payment` model (previously `BalePayment`) that references the
canonical `user_id` FK instead of `bale_user_id`. The model SHALL include a `provider` field
(accepted values: `"bale"`, `"zarinpal"`, `"stripe"`) and a `status` field (accepted values:
`"pending"`, `"success"`, `"failed"`).

#### Scenario: Successful Bale payment recorded
- **WHEN** a Bale pre-checkout callback is confirmed
- **THEN** a `Payment` row is created with `user_id` (canonical UUID), `provider="bale"`, and `status="success"`

#### Scenario: Payment linked to user not provider
- **WHEN** the same user pays via two different providers (e.g., Bale today, Zarinpal later)
- **THEN** both `Payment` rows share the same `user_id` and differ only in `provider`

### Requirement: Payment Service Accepts user_id
The `payment_service.record_payment()` function SHALL accept `user_id: UUID`, `provider: str`, and
`status: str` instead of `bale_user_id`. It SHALL NOT store or query `bale_user_id` internally.

#### Scenario: Handler resolves identity before recording payment
- **WHEN** a Bale payment handler processes a successful payment
- **THEN** it resolves `bale_user_id → user_id` via `fetch_user_by_identity` before calling `record_payment`
