# Design: add-gitea-backup-workflow

## Goals

- Back up `infrastructure/docker-compose.prod.yml`, `infrastructure/.env`,
  and `.gitea/` on a 1-hour schedule and on manual request.
- Never store plaintext secrets in git history or any branch.
- Keep restoration simple: standard CLI tools, no proprietary services.
- Require only one new Gitea secret (`BACKUP_PASSPHRASE`).

## Non-Goals

- Real-time replication or database backup.
- Off-site / S3 storage (no external credentials required).
- Alerting on backup failure (can be added later).
- Encrypting with asymmetric GPG keys (adds key management complexity).

## Key Architectural Decisions

### 1. Release Artifacts vs. a `backups` Branch

| | Release Artifacts | `backups` Branch |
|---|---|---|
| Plaintext risk | Binary blobs, no git history | Committed blobs appear in `git log` |
| Retention | Delete via API — no rebase needed | Requires `git push --force` or squash |
| Discovery | Gitea Releases UI | Branch listing |
| Token scope | `gitea.token` (built-in) | Needs committer identity config |

**Decision**: Release artifacts. Simpler retention, zero plaintext git-history risk.

### 2. OpenSSL AES-256-CBC (pbkdf2) vs. GPG

GPG requires key generation, key distribution, and agent management on the runner.
OpenSSL symmetric encryption with a passphrase stored in a Gitea secret is:
- Simpler to set up (one secret, no key pair).
- Simpler to restore (one `openssl enc -d` command, passphrase from vault).
- Equally strong at AES-256 with pbkdf2 key derivation.

**Decision**: OpenSSL AES-256-CBC with `-pbkdf2 -iter 100000`.

### 3. Retention Window

Hourly backups × 72 = 3 days of history. Three days covers:
- A missed deploy caught the next day.
- A weekend incident discovered Monday.
- Accidental deletion noticed within the same sprint.

Gitea's release list API supports `limit=100` per page. Since the job deletes
immediately after upload, the list will never grow beyond ~73 at the moment of
pruning. A single API page is always sufficient.

**Decision**: Keep 72 most recent `backup-*` releases.

### 4. Checkout Strategy

The workflow reuses the same manual-clone pattern as `deploy.yaml`:

```bash
git clone https://${{ gitea.token }}@git.mrbadri.ir/${{ gitea.repository }}.git .
git checkout ${{ gitea.sha || 'main' }}
```

`gitea.sha` is empty for scheduled runs, so `|| 'main'` ensures the latest
production-deployed state is captured.

### 5. Plaintext Cleanup

The plaintext tarball is deleted immediately after encryption (`rm -f "$TARBALL"`).
The encrypted file and checksum are deleted in a final `if: always()` step to
ensure no sensitive temp files survive a failed run.

## Restoration Procedure (Summary)

1. Download `.tar.gz.enc` + `.sha256` from the target Gitea release.
2. `sha256sum -c` to verify integrity.
3. `openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -pass pass:"PASSPHRASE" ...`
4. `tar -xzf` to extract files.
5. Review diffs before copying to live server.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| `BACKUP_PASSPHRASE` lost | Store in team password manager as well as Gitea secret |
| Runner has no `jq` | Add `apt-get install -y jq` step before retention pruning |
| Gitea token lacks release write permission | Ensure workflow uses default `gitea.token` with repo scope |
| More than 100 backup releases (page overflow) | Cron + immediate pruning keeps count ≤ 73; document limit |
