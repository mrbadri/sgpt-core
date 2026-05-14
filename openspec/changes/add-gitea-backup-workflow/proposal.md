# Proposal: add-gitea-backup-workflow

## Why

Production infrastructure secrets (`infrastructure/.env`) and the Docker Compose
configuration (`infrastructure/docker-compose.prod.yml`) exist **only on the server**.
A host failure, accidental overwrite, or secret rotation error would require manual
reconstruction of all credentials from scratch.

The Gitea CI/CD workflows in `.gitea/` are version-controlled but could diverge
from the live server state. Capturing a consistent snapshot of all three together
provides a single, timestamped recovery point.

There is currently no automated or manual backup mechanism for these files.

## What Changes

- **New file**: `.gitea/workflows/backup.yaml`
  Defines a Gitea Actions workflow that archives and encrypts the three targets,
  then uploads the encrypted bundle as a Gitea release artifact.
- **Operator action** (not code): Add a `BACKUP_PASSPHRASE` secret in Gitea
  repository Settings → Actions → Secrets. No code changes carry secrets.

## What Does NOT Change

- `infrastructure/docker-compose.prod.yml` — read-only during backup, not modified.
- `infrastructure/.env` — read-only during backup, not committed to git history.
- `.gitea/workflows/deploy.yaml` — untouched.
- Any application source code.

## Approach

1. **Trigger**: Gitea Actions `schedule` (cron `0 * * * *` — top of every hour)
   plus `workflow_dispatch` for on-demand runs.
2. **Bundle**: `tar -czf` of the three targets from the cloned workspace.
3. **Encrypt**: `openssl enc -aes-256-cbc -pbkdf2 -iter 100000` with passphrase
   from the `BACKUP_PASSPHRASE` secret. The plaintext tarball is deleted immediately.
4. **Checksum**: SHA-256 digest of the encrypted file stored as a companion asset.
5. **Store**: Gitea release API — each run creates a release tagged
   `backup-<YYYYMMDDTHHMMSSZ>` with two assets: `.tar.gz.enc` + `.sha256`.
6. **Retention**: After upload, list all `backup-*` releases and delete any beyond
   the 72 most recent (rolling 3-day window for hourly cadence).

## Impact

- **New spec**: `gitea-ci-backup`
- **Affected paths**: `.gitea/workflows/backup.yaml` (new)
- **Gitea releases**: up to 72 backup releases retained at any time
- **No application impact**: workflow runs in isolation, does not touch containers

## Open Questions

None. Approach is self-contained.
