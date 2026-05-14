# makefile-developer-workflow Specification

## Purpose
TBD - created by archiving change add-frontend-docker-makefile-stack. Update Purpose after archive.
## Requirements
### Requirement: Root Makefile exposes frontend and full-stack workflows

The repository root **`Makefile`** SHALL provide documented targets that integrate the **`frontend/`** monorepo with the existing Docker-based backend workflow.

#### Scenario: Host-side frontend tasks

- **WHEN** a developer runs the documented **install** target for the frontend
- **THEN** the command SHALL execute from **`frontend/`** using the workspace package manager (**pnpm**) without requiring them to remember nested paths
- **AND** there SHALL be documented targets for **dev**, **build**, **lint**, and **typecheck** (or equivalent) that delegate to **`frontend/`** scripts

#### Scenario: Docker-integrated web tasks

- **WHEN** the **`web`** service is part of the Compose project
- **THEN** the **`Makefile`** SHALL provide targets to **follow logs** for **`web`** and to **rebuild** or **restart** the **`web`** service using the same Compose file(s) as **backend**
- **AND** `make help` SHALL describe how to start **database + backend + web** together

### Requirement: Help output remains the primary discovery mechanism

The **`help`** target output SHALL remain the primary index of developer commands and SHALL include a section (or grouped lines) for **Frontend** and **Full stack** workflows after this change.

#### Scenario: New contributor finds web commands

- **WHEN** a new contributor runs `make help` at the repository root
- **THEN** they SHALL see how to start the web app via Docker **and/or** via host **pnpm**

