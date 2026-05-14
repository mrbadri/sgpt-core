## 1. Specification / docs

- [x] 1.1 Get proposal review approval before merging implementation. *(implemented per explicit request to apply the change.)*

## 2. Docker / Compose

- [x] 2.1 Add **Dockerfile** for `frontend` (multi-stage for prod; dev stage or inline command documented).
- [x] 2.2 Add **`web`** service to `infrastructure/docker-compose.dev.yml` with health-appropriate `depends_on`, published port, and env for API URL(s).
- [x] 2.3 Add **`web`** service to `infrastructure/docker-compose.prod.yml` (no dev bind mounts; resource limits optional).
- [x] 2.4 Update `infrastructure/.env.example` with `NEXT_PUBLIC_*` and any server-side `API_URL` / rewrites.
- [ ] 2.5 (Optional) Restructure to `infrastructure/compose/` + `infrastructure/docker/` and update **Makefile** paths + references in docs.

## 3. Next.js / frontend config

- [x] 3.1 Ensure `apps/web` listens on `0.0.0.0` when run in Docker dev.
- [x] 3.2 Add or align env handling for public API base URL vs internal backend URL (document in README fragment or `frontend/README.md`).
- [x] 3.3 (Optional) Enable **`output: 'standalone'`** in `next.config.mjs` if adopted in Dockerfile.

## 4. Makefile

- [x] 4.1 Add `.PHONY` targets for **web**: e.g. `dev-up-web` / `dev-logs-web`, or extend `dev-up` to include web via compose profiles.
- [x] 4.2 Add **host-side** targets: `frontend-install`, `frontend-dev`, `frontend-build`, `frontend-lint`, `frontend-typecheck` wrapping `pnpm` in `frontend/`.
- [x] 4.3 Update **`help`** text to describe full-stack quick start (db + backend + web).

## 5. Verification

- [x] 5.1 `make dev-up` (or profile) brings up **web**; landing page reachable on documented port.
- [x] 5.2 `make prod-build && make prod-up` includes **web**; smoke test HTTP 200 on web port.
- [x] 5.3 Run `openspec validate add-frontend-docker-makefile-stack --strict --no-interactive` after edits to this change.
