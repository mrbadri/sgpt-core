# Bale Bot Backend Documentation

Complete guide for setting up, developing, and deploying the Bale Bot Backend.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Setup](#docker-setup)
3. [Local Development](#local-development)
4. [Database Migrations](#database-migrations)
5. [Docker Migrations](#docker-migrations)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker and Docker Compose (for Docker setup)

### Development with Docker (Recommended)

```bash
cd /root/Documents/bale_bot
docker-compose -f docker/docker-compose.dev.yml up
```

The API will be available at `http://localhost:8000` with auto-reload enabled.

### Local Development (Without Docker)

```bash
# Install dependencies
uv sync

# Set up database and run migrations
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
uv run alembic upgrade head

# Run the application
uv run uvicorn src.app.main:app --reload
```

---

## Docker Setup

### Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose 2.0+ (or docker-compose 1.29+)

### Quick Start

#### Development Environment

```bash
cd /root/Documents/bale_bot
docker-compose -f docker/docker-compose.dev.yml up
```

This will:
- Start PostgreSQL database
- Build and start the backend application
- Enable hot-reload for code changes
- Expose API on http://localhost:8000
- Run migrations automatically

#### Production Environment

```bash
cd /root/Documents/bale_bot
docker-compose -f docker/docker-compose.prod.yml up -d
```

**Note:** Make sure to set all required environment variables before running production.

### Docker Compose Files

#### Development (`docker-compose.dev.yml`)

**Features:**
- Hot-reload enabled (code changes reflect immediately)
- Volume mounts for live editing
- Debug logging enabled
- Development database with seed data support
- Port 5433 exposed for direct database access (mapped from container's 5432)

**Usage:**
```bash
docker-compose -f docker/docker-compose.dev.yml up
docker-compose -f docker/docker-compose.dev.yml down
docker-compose -f docker/docker-compose.dev.yml logs -f
```

#### Production (`docker-compose.prod.yml`)

**Features:**
- Optimized production builds
- Security hardening
- Resource limits configured
- No volume mounts (code baked into image)
- JSON logging for production monitoring
- Health checks enabled

**Usage:**
```bash
# Build and start
docker-compose -f docker/docker-compose.prod.yml up -d

# View logs
docker-compose -f docker/docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.prod.yml down

# Rebuild after code changes
docker-compose -f docker/docker-compose.prod.yml up -d --build
```

### Environment Variables

#### Development

Create a `.env` file in the project root:

```bash
DATABASE_URL=postgresql://bale_bot:dev_password@db:5432/bale_bot
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
LOG_FORMAT=text
BALE_BOT_TOKEN=your_bot_token_here
BALE_API_URL=https://tapi.bale.ai/bot{0}/{1}
```

#### Production

**Required variables:**
```bash
DATABASE_URL=postgresql://user:password@db:5432/bale_bot
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=bale_bot
BALE_BOT_TOKEN=your_bot_token
ADMIN_SECRET_KEY=your_admin_secret_key
SECRET_KEY=your_secret_key
```

Set these in your environment or use Docker secrets for production.

### Building Images

```bash
# Build backend image
cd /root/Documents/bale_bot
docker build -f docker/Dockerfile -t bale-bot-backend:latest .

# Build with specific tag
docker build -f docker/Dockerfile -t bale-bot-backend:v1.0.0 .
```

### Database Access

```bash
# Connect to database container (development)
docker-compose -f docker/docker-compose.dev.yml exec db psql -U bale_bot -d bale_bot

# Or connect from host (using mapped port 5433)
psql -h localhost -p 5433 -U bale_bot -d bale_bot
# Password: dev_password

# Production
docker-compose -f docker/docker-compose.prod.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

### Viewing Logs

```bash
# All services
docker-compose -f docker/docker-compose.dev.yml logs

# Specific service
docker-compose -f docker/docker-compose.dev.yml logs backend
docker-compose -f docker/docker-compose.dev.yml logs db

# Follow logs (real-time)
docker-compose -f docker/docker-compose.dev.yml logs -f backend

# Last N lines
docker-compose -f docker/docker-compose.dev.yml logs --tail=100 backend
```

### Executing Commands in Containers

```bash
# Run shell in backend container
docker-compose -f docker/docker-compose.dev.yml exec backend bash

# Run Python commands
docker-compose -f docker/docker-compose.dev.yml exec backend python -c "from app.settings import settings; print(settings.app_name)"

# Run tests
docker-compose -f docker/docker-compose.dev.yml exec backend uv run pytest tests/
```

---

## Local Development

### Setup Without Docker

If Docker isn't available or you prefer local development:

#### 1. Install Python Dependencies

```bash
cd /root/Documents/bale_bot
uv sync
```

#### 2. Set Up PostgreSQL Database

```bash
# Create database
createdb bale_bot

# Or use psql
psql -U postgres -c "CREATE DATABASE bale_bot;"
```

#### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cat > .env << EOF
DATABASE_URL=postgresql://user:password@localhost:5432/bale_bot
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
LOG_FORMAT=text
BALE_BOT_TOKEN=your_token_here
BALE_API_URL=https://tapi.bale.ai/bot{0}/{1}
SECRET_KEY=dev-secret-key-change-in-production
ADMIN_SECRET_KEY=dev-admin-secret
EOF
```

**Note:** The `BALE_BOT_TOKEN` is required for the bot service to start.

#### 4. Run Database Migrations

```bash
cd backend
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
uv run alembic upgrade head
```

#### 5. Run the Application

```bash
cd backend
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Bot API: http://localhost:8000/api/bot
- Admin API: http://localhost:8000/api/admin

**Bot Service:** The bot service starts automatically when the application starts (if `BALE_BOT_TOKEN` is configured).

### Setting PYTHONPATH Permanently

Add to your `.bashrc`/`.zshrc`:

```bash
echo 'export PYTHONPATH=/root/Documents/bale_bot/backend/src:$PYTHONPATH' >> ~/.zshrc
```

### Running Tests

```bash
cd backend
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
uv run pytest tests/
```

### Code Quality

```bash
# Format code
black backend/src/

# Lint code
ruff check backend/src/
```

---

## Database Migrations

### Overview

We use [Alembic](https://alembic.sqlalchemy.org/) for database migrations. Alembic tracks database schema changes and allows you to version control your database structure.

### Migration Files Location

Migrations are stored in: `backend/src/app/db/migrations/versions/`

### Quick Start

#### Running Migrations

```bash
# Navigate to backend directory
cd backend

# Set PYTHONPATH
export PYTHONPATH=$(pwd)/src:$PYTHONPATH

# Run all pending migrations
uv run alembic upgrade head
```

#### Creating a New Migration

```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "add user table"

# Create empty migration (manual)
uv run alembic revision -m "add user table"
```

### Common Commands

```bash
# Check current migration status
uv run alembic current

# View migration history
uv run alembic history

# View detailed history
uv run alembic history --verbose

# Upgrade to latest
uv run alembic upgrade head

# Upgrade to specific revision
uv run alembic upgrade <revision_id>

# Downgrade one revision
uv run alembic downgrade -1

# Downgrade to specific revision
uv run alembic downgrade <revision_id>

# Downgrade to base (removes all migrations - WARNING: deletes all data!)
uv run alembic downgrade base
```

### Creating Migrations

#### Auto-Generate Migration

Alembic can automatically detect model changes:

```bash
uv run alembic revision --autogenerate -m "add groups table"
```

**How it works:**
1. Compares current models with database schema
2. Generates migration script with differences
3. You should review and edit the generated migration

**Important:** Always review auto-generated migrations before applying!

#### Manual Migration

For complex changes or data migrations:

```bash
uv run alembic revision -m "migrate user data"
```

Then edit the generated file in `versions/` directory.

### Best Practices

1. **Always Review Auto-Generated Migrations** - Review the generated file before applying
2. **Test Migrations** - Test both upgrade and downgrade paths
3. **Use Descriptive Messages** - Use clear, descriptive migration messages
4. **Keep Migrations Small and Focused** - One logical change per migration
5. **Never Edit Applied Migrations** - If a migration has been applied, create a new one to fix issues
6. **Include Data Migrations When Needed** - Update data alongside schema changes

### Troubleshooting

#### Migration Conflicts

```bash
# Check current state
uv run alembic current

# View history
uv run alembic history

# Merge branches (if needed)
uv run alembic merge -m "merge branches" <rev1> <rev2>
```

#### "Target database is not up to date"

```bash
# Check what's pending
uv run alembic current
uv run alembic history

# Apply pending migrations
uv run alembic upgrade head
```

#### "Can't locate revision identified by 'xyz'"

```bash
# Check what database thinks is current
uv run alembic current

# Compare with migration files
uv run alembic history

# If needed, stamp database to specific revision
uv run alembic stamp <revision_id>
```

---

## Docker Migrations

### Automatic Migrations

When using Docker, migrations run automatically when containers start. The Docker entrypoint script (`docker/scripts/entrypoint.sh`) automatically runs migrations when the backend container starts.

#### How It Works

```bash
# From entrypoint.sh
uv run alembic upgrade head || echo "Migrations failed or no migrations to run"
```

This ensures your database schema is always up-to-date when you start the application.

#### When Migrations Run

1. **Container Start**: Migrations run automatically via the entrypoint script
2. **After Database Ready**: The script waits for the database to be healthy before running migrations
3. **On Failure**: If migrations fail, the container continues to start (you'll see a warning message)

### Manual Migration Execution

Sometimes you may want to run migrations manually:

#### Development

```bash
# Run all pending migrations
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic upgrade head

# Run migrations to a specific revision
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic upgrade <revision_id>

# Check current migration status
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic current

# View migration history
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic history
```

#### Production

```bash
# Run all pending migrations
docker-compose -f docker/docker-compose.prod.yml exec backend uv run alembic upgrade head

# Check current migration status
docker-compose -f docker/docker-compose.prod.yml exec backend uv run alembic current
```

### Creating New Migrations in Docker

```bash
# Auto-generate migration
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic revision --autogenerate -m "add users table"

# Create empty migration file
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic revision -m "custom migration"
```

The migration file will be created in: `backend/src/app/db/migrations/versions/`

### Migration Workflow

#### Development Workflow

1. **Make model changes** in your code
2. **Create migration**: `docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic revision --autogenerate -m "description"`
3. **Review generated migration**
4. **Test migration**: Restart container or run manually
5. **Verify changes**: Connect to database and verify schema

#### Production Workflow

1. **Test migrations in staging/dev first**
2. **Backup database**: `docker-compose -f docker/docker-compose.prod.yml exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql`
3. **Deploy code** (with new migration files)
4. **Run migrations**: Let automatic migration run or run manually first
5. **Verify migration**: Check current revision and logs

### Troubleshooting Docker Migrations

#### Migration Fails on Startup

```bash
# Check logs
docker-compose -f docker/docker-compose.dev.yml logs backend

# Check database connection
docker-compose -f docker/docker-compose.dev.yml exec db pg_isready -U bale_bot

# Run migration manually
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic upgrade head

# Check migration status
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic current
```

#### Database Out of Sync

```bash
# Check current state
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic current

# View migration history
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic history

# Stamp database (if needed)
docker-compose -f docker/docker-compose.dev.yml exec backend uv run alembic stamp <revision_id>
```

#### Reset Database (Development Only)

**Warning**: This deletes all data!

```bash
# Stop containers
docker-compose -f docker/docker-compose.dev.yml down

# Remove database volume
docker-compose -f docker/docker-compose.dev.yml down -v

# Start fresh
docker-compose -f docker/docker-compose.dev.yml up
# Migrations will run automatically
```

---

## Troubleshooting

### Docker Issues

#### Container Won't Start

1. **Check logs:**
   ```bash
   docker-compose -f docker/docker-compose.dev.yml logs
   ```

2. **Check Docker daemon:**
   ```bash
   docker ps
   ```

3. **Rebuild images:**
   ```bash
   docker-compose -f docker/docker-compose.dev.yml build --no-cache
   ```

#### Database Connection Issues

1. **Verify database is running:**
   ```bash
   docker-compose -f docker/docker-compose.dev.yml ps db
   ```

2. **Check DATABASE_URL environment variable**

3. **Wait for database to be ready:**
   ```bash
   docker-compose -f docker/docker-compose.dev.yml exec db pg_isready
   ```

#### Port Already in Use

If port 8000 or 5432 is already in use:

1. **Change ports in docker-compose.yml:**
   ```yaml
   ports:
     - "8001:8000"  # Use 8001 instead of 8000
   ```

2. **Or stop the service using the port**

#### Volume Mount Issues

If code changes aren't reflecting:

1. **Check volume mounts:**
   ```bash
   docker-compose -f docker/docker-compose.dev.yml config
   ```

2. **Verify file permissions**

3. **Restart the container:**
   ```bash
   docker-compose -f docker/docker-compose.dev.yml restart backend
   ```

### Local Development Issues

#### Import Errors

If you get import errors, make sure PYTHONPATH includes the src directory:

```bash
export PYTHONPATH=/root/Documents/bale_bot/backend/src:$PYTHONPATH
```

#### Database Connection Errors

1. Check PostgreSQL is running: `pg_isready`
2. Verify DATABASE_URL in `.env` matches your database
3. Check database exists: `psql -l | grep bale_bot`

#### Alembic Migration Errors

If migrations fail:

```bash
cd backend
uv run alembic revision --autogenerate -m "initial"
uv run alembic upgrade head
```

### Clean Up

**Remove all containers and volumes:**
```bash
docker-compose -f docker/docker-compose.dev.yml down -v
docker system prune -a  # Remove unused images
```

---

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
