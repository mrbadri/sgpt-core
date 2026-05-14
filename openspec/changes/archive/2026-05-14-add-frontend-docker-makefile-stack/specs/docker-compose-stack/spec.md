## ADDED Requirements

### Requirement: Application stack includes optional web service

The Docker Compose application stack SHALL define an optional **`web`** service that runs the repository **Next.js** application (`frontend/apps/web`), using build context and Dockerfile path(s) documented in `infrastructure/`.

#### Scenario: Development stack runs web with backend

- **WHEN** a developer starts the development Compose project
- **THEN** they MAY start **`web`** together with **`db`** and **`backend`** such that the web UI is reachable on a documented host port
- **AND** the **`web`** container CAN resolve the FastAPI service at the Docker network hostname **`backend`** on port **8000** for server-side requests

#### Scenario: Production stack runs web without source bind mounts

- **WHEN** the production Compose project is started
- **THEN** the **`web`** service SHALL run from an image built with a **multi-stage** build (dependencies + build + runtime)
- **AND** the running container SHALL NOT rely on bind-mounting the host `frontend/` source tree for normal operation

### Requirement: Compose environment documents API URLs for web

The infrastructure environment templates SHALL document variables needed for the web app to reach the backend from the **browser** (public/host URL) and from **server-side** Next.js code (internal Docker URL where applicable).

#### Scenario: Env example lists web-related variables

- **WHEN** a developer copies `infrastructure/.env.example` for local setup
- **THEN** it SHALL include placeholders for at least one **`NEXT_PUBLIC_`** variable used by the browser to call the API
- **AND** documentation SHALL state which value to use on the host vs inside Compose

### Requirement: Deployment asset layout changes MUST stay consistent with automation

If deployment assets under `infrastructure/` are reorganized (for example grouping **Compose files** under `infrastructure/compose/` and **Dockerfiles** under `infrastructure/docker/`), the change SHALL update every consumer of the old paths in the same delivery (root **`Makefile`**, documentation, and CI).

#### Scenario: Path moves do not break developer workflows

- **WHEN** Compose file or Dockerfile paths are moved for maintainability
- **THEN** the root **`Makefile`**, developer documentation, and any CI references MUST be updated in the same change
- **AND** `make help` MUST remain accurate for the new paths
