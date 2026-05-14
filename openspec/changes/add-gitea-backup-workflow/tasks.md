# Tasks: add-gitea-backup-workflow

## 1. Secrets (operator action, not code)

- [ ] 1.1 Generate a strong passphrase (≥ 32 chars, alphanumeric)
- [ ] 1.2 Add `BACKUP_PASSPHRASE` to Gitea → Settings → Actions → Secrets
- [ ] 1.3 Store the same passphrase in the team password manager

## 2. Workflow file

- [ ] 2.1 Create `.gitea/workflows/backup.yaml` with:
  - `on: schedule: - cron: '0 * * * *'` and `on: workflow_dispatch:`
  - Step: manual checkout (`git clone` + `git checkout ${{ gitea.sha || 'main' }}`)
  - Step: install `jq` (`apt-get install -y jq`)
  - Step: bundle tarball of the three targets, set `TIMESTAMP` + `TARBALL` envs
  - Step: encrypt with `openssl enc -aes-256-cbc -pbkdf2 -iter 100000`, delete plaintext
  - Step: compute SHA-256 checksum
  - Step: create Gitea release via API, upload `.enc` + `.sha256` assets
  - Step: retention pruning — delete `backup-*` releases beyond 72 most recent
  - Step: cleanup (`rm -f`, `if: always()`)
- [ ] 2.2 Commit and push to main

## 3. Verification

- [ ] 3.1 Trigger `workflow_dispatch` manually; confirm release `backup-<timestamp>` appears in Gitea Releases
- [ ] 3.2 Download the `.enc` and `.sha256` assets; verify checksum; decrypt; extract
- [ ] 3.3 Confirm extracted `infrastructure/.env` matches the live server file
- [ ] 3.4 Confirm `.gitea/workflows/` directory is present in the extract
- [ ] 3.5 Wait for the next scheduled run (top of the next hour); confirm a second release appears
- [ ] 3.6 Run `openspec validate add-gitea-backup-workflow --strict --no-interactive`

## 4. Documentation (optional)

- [ ] 4.1 Add a "Backup & Restore" section to `README.md` (or a dedicated `docs/backup.md`)
      describing how to trigger, download, decrypt, and restore from a backup release
