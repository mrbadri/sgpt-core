# Spec: gitea-ci-backup

## ADDED Requirements

### Requirement: Scheduled encrypted infrastructure backup

The system SHALL automatically back up `infrastructure/docker-compose.prod.yml`,
`infrastructure/.env`, and the `.gitea/` directory every hour by running a Gitea
Actions workflow on a cron schedule (`0 * * * *`).

The backup artifact SHALL be an AES-256-CBC encrypted tarball (OpenSSL pbkdf2,
100 000 iterations) using a passphrase stored in the Gitea secret `BACKUP_PASSPHRASE`.

The plaintext tarball SHALL be deleted from the runner immediately after encryption.

#### Scenario: Hourly backup creates a release artifact
- Given the cron schedule fires at the top of an hour
- When the `backup` job completes successfully
- Then a Gitea release tagged `backup-<YYYYMMDDTHHMMSSZ>` exists
- And the release contains two assets: `backup-<timestamp>.tar.gz.enc` and
  `backup-<timestamp>.tar.gz.enc.sha256`
- And no plaintext `.env` content appears in any git commit or release description

#### Scenario: Sensitive files are never stored in plaintext
- Given the workflow runs (scheduled or manual)
- When the tarball is created and encrypted
- Then the plaintext `.tar.gz` file is removed before any upload step executes
- And the encrypted file is removed in the final cleanup step (`if: always()`)

---

### Requirement: Manual backup trigger

The system SHALL allow an operator to trigger an infrastructure backup on demand
via Gitea's `workflow_dispatch` event without requiring a code push.

#### Scenario: Manual trigger produces a release artifact
- Given an operator visits the Gitea repository → Actions → "Infra Backup" workflow
- When they click "Run workflow" and confirm
- Then a new `backup-<timestamp>` release is created within the expected runtime
  (clone + encrypt + upload ≤ 3 minutes on a standard runner)

---

### Requirement: Automatic retention pruning

The system SHALL retain at most 72 backup releases at any time. After each
successful upload, the workflow SHALL delete any `backup-*` releases beyond
the 72 most recent, ordered by creation date descending.

#### Scenario: Old releases are pruned after upload
- Given more than 72 `backup-*` releases exist in the repository
- When the backup workflow completes a new upload
- Then releases beyond the 72 most recent are deleted via the Gitea releases API
- And the total count of `backup-*` releases is ≤ 72 after the job finishes

---

### Requirement: Backup restoration

The system SHALL support restoration of any retained backup using standard CLI
tools (`openssl`, `sha256sum`, `tar`) without proprietary software or additional
services.

#### Scenario: Operator decrypts and extracts backup
- Given an operator downloads a `.tar.gz.enc` and its `.sha256` companion from a
  Gitea backup release
- And they know the `BACKUP_PASSPHRASE` value
- When they run:
  1. `sha256sum -c <file>.sha256` (passes)
  2. `openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -pass pass:"PASSPHRASE" -in <file>.enc -out <file>.tar.gz`
  3. `tar -xzf <file>.tar.gz`
- Then `infrastructure/docker-compose.prod.yml`, `infrastructure/.env`, and
  `.gitea/` are extracted to the working directory
- And the restored `.env` matches the state at the time the backup was taken
