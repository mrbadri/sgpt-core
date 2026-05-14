# Makefile for Bale Bot Docker Compose Management
# 
# Quick Start:
#   make dev-up      # Start development environment
#   make prod-up     # Start production environment
#   make help        # Show all available commands

.PHONY: help dev-up dev-down dev-down-v dev-build dev-logs dev-restart \
prod-up prod-down prod-down-v prod-build prod-logs prod-restart \
clean ps shell shell-backend shell-db migrate migrate-create \
migrate-current migrate-history migrate-downgrade test test-unit \
test-integration test-users dev-logs-web dev-restart-web dev-build-web \
shell-web prod-logs-web prod-restart-web prod-build-web shell-web-prod \
frontend-install frontend-dev frontend-build frontend-lint frontend-typecheck

# Get the directory where this Makefile is located
ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
FRONTEND_DIR = $(ROOT_DIR)/frontend

# Docker Compose file paths
DEV_COMPOSE = $(ROOT_DIR)/infrastructure/docker-compose.dev.yml
PROD_COMPOSE = $(ROOT_DIR)/infrastructure/docker-compose.prod.yml
# docker-compose.prod.yml attaches services to this external network (e.g. shared reverse proxy).
PROD_PROXY_NETWORK := proxy

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Quick Start (Dev Workflow):"
	@echo "  1. make dev-up      # Start db + backend + web (Next.js :3000, API :8000)"
	@echo "  2. make migrate     # Create tables (required on first run!)"
	@echo "  3. Use the bot      # Data will be saved to bot_users table"
	@echo "  4. Open http://localhost:3000 for the marketing web app (optional)"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev-up          Start development environment"
	@echo "  dev-down        Stop development environment"
	@echo "  dev-down-v      Stop development environment and remove volumes"
	@echo "  dev-build       Build development images (backend + web)"
	@echo "  dev-logs        Show development logs"
	@echo "  dev-logs-web    Show web (Next.js) logs only"
	@echo "  dev-restart     Restart development services"
	@echo "  dev-restart-web Restart web service only"
	@echo "  dev-build-web   Build web image only"
	@echo ""
	@echo "Production Commands:"
	@echo "  prod-up         Start production environment"
	@echo "  prod-down       Stop production environment"
	@echo "  prod-down-v     Stop production environment and remove volumes"
	@echo "  prod-build      Build production images (backend + web)"
	@echo "  prod-build-web  Build production web image only"
	@echo "  prod-logs       Show production logs"
	@echo "  prod-logs-web   Show web logs only (prod)"
	@echo "  prod-restart    Restart production services"
	@echo "  prod-restart-web Restart web service only (prod)"
	@echo ""
	@echo "Utility Commands:"
	@echo "  ps              Show running containers"
	@echo "  clean           Remove containers, volumes, and images"
	@echo "  shell-backend   Open shell in backend container (dev)"
	@echo "  shell-db        Open shell in database container (dev)"
	@echo "  shell-web       Open shell in web container (dev)"
	@echo "  shell-web-prod  Open shell in web container (prod)"
	@echo ""
	@echo "Frontend (host pnpm — run without Docker Node toolchain optional):"
	@echo "  frontend-install  pnpm install in frontend/"
	@echo "  frontend-dev      pnpm dev (Turbo)"
	@echo "  frontend-build    pnpm build"
	@echo "  frontend-lint     pnpm lint"
	@echo "  frontend-typecheck  pnpm typecheck"
	@echo ""
	@echo "Migration Commands:"
	@echo "  migrate         Run database migrations (dev) - upgrade to head"
	@echo "  migrate-create  Create new migration (dev) - usage: make migrate-create MESSAGE='description'"
	@echo "  migrate-current Show current migration revision (dev)"
	@echo "  migrate-history Show migration history (dev)"
	@echo "  migrate-downgrade Downgrade one revision (dev)"
	@echo ""
	@echo "Test Commands:"
	@echo "  test            Run all tests (dev)"
	@echo "  test-unit       Run unit tests only (dev)"
	@echo "  test-integration Run integration tests only (dev)"
	@echo "  test-users      Run user-related tests only (dev)"
	@echo ""

# Development commands
dev-up: ## Start development environment
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) up -d

dev-down: ## Stop development environment
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) down

dev-build: ## Build development images
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) build

dev-logs: ## Show development logs (follow mode)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) logs -f

dev-logs-backend: ## Show backend logs only
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) logs -f backend

dev-logs-db: ## Show database logs only
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) logs -f db

dev-logs-web: ## Show web (Next.js) logs only (dev)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) logs -f web

dev-restart: ## Restart development services
	docker-compose -f $(DEV_COMPOSE) restart

dev-restart-web: ## Restart web service only (dev)
	docker-compose -f $(DEV_COMPOSE) restart web

dev-build-web: ## Build web image only (dev target)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) build web

dev-stop: ## Stop development services without removing containers
	docker-compose -f $(DEV_COMPOSE) stop

dev-start: ## Start stopped development services
	docker-compose -f $(DEV_COMPOSE) start

dev-down-v: ## Stop development environment and remove volumes
	docker-compose -f $(DEV_COMPOSE) down -v

# Production commands
prod-up: ## Start production environment
	@docker network inspect $(PROD_PROXY_NETWORK) >/dev/null 2>&1 || docker network create $(PROD_PROXY_NETWORK)
	docker-compose -f $(PROD_COMPOSE) up -d

prod-down: ## Stop production environment
	docker-compose -f $(PROD_COMPOSE) down

prod-build: ## Build production images
	docker-compose -f $(PROD_COMPOSE) build

prod-logs: ## Show production logs (follow mode)
	docker-compose -f $(PROD_COMPOSE) logs -f

prod-logs-backend: ## Show backend logs only (prod)
	docker-compose -f $(PROD_COMPOSE) logs -f backend

prod-logs-db: ## Show database logs only (prod)
	docker-compose -f $(PROD_COMPOSE) logs -f db

prod-logs-web: ## Show web logs only (prod)
	cd $(ROOT_DIR) && docker-compose -f $(PROD_COMPOSE) logs -f web

prod-restart: ## Restart production services
	docker-compose -f $(PROD_COMPOSE) restart

prod-restart-web: ## Restart web service only (prod)
	docker-compose -f $(PROD_COMPOSE) restart web

prod-build-web: ## Build production web image only
	cd $(ROOT_DIR) && docker-compose -f $(PROD_COMPOSE) build web

prod-stop: ## Stop production services without removing containers
	docker-compose -f $(PROD_COMPOSE) stop

prod-start: ## Start stopped production services
	docker-compose -f $(PROD_COMPOSE) start

prod-down-v: ## Stop production environment and remove volumes
	docker-compose -f $(PROD_COMPOSE) down -v

# Utility commands
ps: ## Show running containers
	@echo "Development containers:"
	@docker-compose -f $(DEV_COMPOSE) ps || true
	@echo ""
	@echo "Production containers:"
	@docker-compose -f $(PROD_COMPOSE) ps || true

clean: ## Remove containers, volumes, and images
	@echo "Cleaning development environment..."
	docker-compose -f $(DEV_COMPOSE) down -v --rmi local || true
	@echo "Cleaning production environment..."
	docker-compose -f $(PROD_COMPOSE) down -v --rmi local || true
	@echo "Cleanup complete!"

clean-dev: ## Clean only development environment
	docker-compose -f $(DEV_COMPOSE) down -v --rmi local

clean-prod: ## Clean only production environment
	docker-compose -f $(PROD_COMPOSE) down -v --rmi local

shell-backend: ## Open shell in backend container (dev)
	docker-compose -f $(DEV_COMPOSE) exec backend /bin/bash

shell-db: ## Open shell in database container (dev)
	docker-compose -f $(DEV_COMPOSE) exec db /bin/sh

shell-web: ## Open shell in web container (dev)
	docker-compose -f $(DEV_COMPOSE) exec web /bin/sh

shell-backend-prod: ## Open shell in backend container (prod)
	docker-compose -f $(PROD_COMPOSE) exec backend /bin/bash

shell-db-prod: ## Open shell in database container (prod)
	docker-compose -f $(PROD_COMPOSE) exec db /bin/sh

shell-web-prod: ## Open shell in web container (prod)
	docker-compose -f $(PROD_COMPOSE) exec web /bin/sh

frontend-install: ## Install frontend dependencies (pnpm)
	cd $(FRONTEND_DIR) && pnpm install

frontend-dev: ## Start frontend dev servers via Turbo (host)
	cd $(FRONTEND_DIR) && pnpm dev

frontend-build: ## Build all frontend packages (Turbo)
	cd $(FRONTEND_DIR) && pnpm build

frontend-lint: ## Lint frontend (Turbo)
	cd $(FRONTEND_DIR) && pnpm lint

frontend-typecheck: ## Typecheck frontend (Turbo)
	cd $(FRONTEND_DIR) && pnpm typecheck

# Database commands
db-migrate-dev: ## Run database migrations (dev)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && PYTHONPATH=/app/src uv run alembic -c alembic.ini upgrade head"

db-migrate-prod: ## Run database migrations (prod)
	cd $(ROOT_DIR) && docker-compose -f $(PROD_COMPOSE) exec backend bash -c "cd /app && PYTHONPATH=/app/src uv run alembic -c alembic.ini upgrade head"

db-shell-dev: ## Open PostgreSQL shell (dev)
	docker-compose -f $(DEV_COMPOSE) exec db psql -U bale_bot -d bale_bot

db-shell-prod: ## Open PostgreSQL shell (prod)
	docker-compose -f $(PROD_COMPOSE) exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

# Migration commands (aliases for convenience)
migrate: ## Run database migrations (dev) - upgrade to head
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && PYTHONPATH=/app/src uv run alembic -c alembic.ini upgrade head"

migrate-create: ## Create new migration (dev) - usage: make migrate-create MESSAGE='description'
	@if [ -z "$(MESSAGE)" ]; then \
		echo "Error: MESSAGE is required. Usage: make migrate-create MESSAGE='your migration description'"; \
		exit 1; \
	fi
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && export PYTHONPATH=/app/src:\$$PYTHONPATH && uv run alembic -c alembic.ini revision --autogenerate -m '$(MESSAGE)'"

migrate-current: ## Show current migration revision (dev)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && PYTHONPATH=/app/src uv run alembic -c alembic.ini current"

migrate-history: ## Show migration history (dev)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && PYTHONPATH=/app/src uv run alembic -c alembic.ini history"

migrate-downgrade: ## Downgrade one revision (dev)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && PYTHONPATH=/app/src uv run alembic -c alembic.ini downgrade -1"

migrate-upgrade: ## Upgrade to specific revision (dev) - usage: make migrate-upgrade REVISION='revision_id'
	@if [ -z "$(REVISION)" ]; then \
		echo "Error: REVISION is required. Usage: make migrate-upgrade REVISION='revision_id'"; \
		exit 1; \
	fi
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && PYTHONPATH=/app/src uv run alembic -c alembic.ini upgrade $(REVISION)"

# Test commands
test: ## Run all tests (dev)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && export PYTHONPATH=/app/src:\$$PYTHONPATH && uv run pytest tests/ -v"

test-unit: ## Run unit tests only (dev)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && export PYTHONPATH=/app/src:\$$PYTHONPATH && uv run pytest tests/unit/ -v"

test-integration: ## Run integration tests only (dev)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && export PYTHONPATH=/app/src:\$$PYTHONPATH && uv run pytest tests/integration/ -v"

test-users: ## Run user-related tests only (dev)
	cd $(ROOT_DIR) && docker-compose -f $(DEV_COMPOSE) exec backend bash -c "cd /app && export PYTHONPATH=/app/src:\$$PYTHONPATH && uv run pytest tests/unit/features/users/ tests/integration/test_start_command_saves_user.py -v"
