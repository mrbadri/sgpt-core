# Change: Integrate frontend with Docker Compose and root Makefile

## Why

The repository has a Turbo **pnpm** monorepo under `frontend/` (Next.js **web** app) and Docker-based **backend** stacks under `infrastructure/`, but the **Makefile** and **Compose** files only orchestrate **db**, **backend**, and supporting services. Developers cannot bring up the marketing/site UI alongside the API with one workflow, and production deployment of the web app is not defined in the same infra surface as the Python service.

## What Changes

- Add an optional **`web`** service to **dev** and **prod** Docker Compose (or a dedicated compose override) so the Next.js app can run **in-container** with predictable ports and **backend** networking (`http://backend:8000` from the server, public URL from the browser via env).
- Extend the **root `Makefile`** with targets for **full-stack dev** (`docker compose` including web), **web-only** logs/shell/rebuild, and **host-side** frontend tasks (`pnpm` via `frontend/`) for contributors who prefer not to containerize the Node toolchain.
- Document and optionally adjust **repository layout** so infra stays the single place for deployment assets: e.g. `infrastructure/docker/` for `Dockerfile.web`, `infrastructure/compose/` for `*.yml` (recommended in `design.md`); **BREAKING** only if existing CI/docs reference old compose paths — migration = update commands and docs in the same change.

## Impact

- **Affected specs (new):** `docker-compose-stack`, `makefile-developer-workflow` (deltas introduce these capabilities).
- **Affected code:** `Makefile`, `infrastructure/docker-compose.*.yml`, new `infrastructure/**/Dockerfile*` for web (if approved), `infrastructure/.env.example`, `frontend/` env documentation; `openspec/project.md` should be updated when the change is archived to reflect the new workflow.
