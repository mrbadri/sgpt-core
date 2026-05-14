## Context

- **Backend** is built from repo root context with `infrastructure/Dockerfile`; **Compose** files live in `infrastructure/` and use `context: ..` for the Python app.
- **Frontend** is a **pnpm + Turbo** monorepo in `frontend/` with the deployable app at `frontend/apps/web/`. Local dev today is `pnpm dev` from `frontend/`, independent of Docker.
- The root **Makefile** centralizes **docker-compose** and **Alembic**/**pytest** commands but has **no** web targets.

## Goals / Non-Goals

**Goals**

- One documented workflow: **database + backend + web** for local integration and demos.
- **Production-shaped** web image (multi-stage **Node** build, minimal runtime) callable from **prod** compose.
- **Browser** calls API via **public** URL (e.g. `http://localhost:8000` dev, `http://localhost:8800` prod or a reverse proxy later); **server** components or SSR fetches use **internal** Docker DNS (`http://backend:8000`) where applicable.
- Clear **Makefile** entrypoints so new contributors do not need to memorize compose file paths.

**Non-Goals**

- Replacing **Turbo**/**pnpm** with **npm** or collapsing the monorepo.
- Implementing a full **reverse proxy** (Traefik/Caddy) in this change — optional follow-up.
- Changing **Bale** bot runtime behavior.

## Decisions

1. **Folder layout (recommended)**  
   - Keep **one** logical "infra root" under `infrastructure/`.  
   - Optional refactor: `infrastructure/compose/docker-compose.dev.yml` and `docker-compose.prod.yml` plus `infrastructure/docker/Dockerfile` (backend) and `infrastructure/docker/Dockerfile.web` (frontend).  
   - **Rationale:** separates **Compose** from **Dockerfiles** and scales when adding nginx or jobs. If the team prefers minimal churn, add `infrastructure/Dockerfile.web` next to the existing Dockerfile first; document the preferred end-state in `tasks.md`.

2. **Dev web service**  
   - **Volume-mount** `frontend/` and run `pnpm install` + `pnpm dev` (or turbo filter) **or** use `command: pnpm --filter web dev` with dev server **host** `0.0.0.0`.  
   - Publish **host port** e.g. `3000:3000` (or `3001` if conflicts).  
   - Pass **`NEXT_PUBLIC_*`** for browser-side API base URL.

3. **Prod web service**  
   - **Multi-stage build**: copy `frontend/`, `pnpm install --frozen-lockfile`, `pnpm build --filter web`, run `next start` (or standalone output if enabled in `next.config`).  
   - No bind mounts; image is immutable.

4. **Makefile**  
   - Prefix targets: `web-dev-up`, `web-logs`, `frontend-install`, `frontend-lint`, etc., or group under `help` sections **Frontend** and **Full stack**.  
   - Prefer `docker compose` (v2 plugin) consistently; document if some environments still need `docker-compose` hyphenated binary.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Dev container Node/pnpm slower than host | Document **host** workflow via Make delegating to `cd frontend && pnpm dev`. |
| `node_modules` volume vs bind mount confusion | Use named volume for `node_modules` in dev optional pattern; document in `.env.example`. |
| **NEXT_PUBLIC_** vs server env | Use `.env.example` keys: public URL for browser, internal URL for server-only (`docker` network). |

## Migration Plan

1. Add **web** service and env vars to **dev** compose; verify landing page loads and API health from browser.  
2. Add **prod** image + service; smoke-test `next start` behind published port.  
3. Extend **Makefile** `help` and targets; update `openspec/project.md` after archive.  
4. If compose paths move, grep the repo for old paths and update **README**/**CI** in the implementation PR.

## Open Questions

- Exact **host ports** for web in dev/prod (avoid clash with FalkorDB browser **3000** inside container — host mapping is already **3379**).  
- Whether to enable **Next.js `output: 'standalone'`** for smaller prod images (implementation task).
