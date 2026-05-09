# Bale Bot Backend

Backend system for Bale messenger bot (Telegram-compatible API).

## Features

- Phone-based authorization and identity
- Invite-only join flow via secure links
- Role-based access control
- Contest lifecycle management
- Admin-level observability and reporting
- Bot-first interaction model
- **Bale Bot Integration** - Automated bot service with command handling (`/start`, `/echo`)

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy / SQLModel
- **Migrations**: Alembic
- **Database**: PostgreSQL
- **API Specification**: OpenAPI 3.x

## Project Structure

```
backend/
├── src/
│   ├── app/              # Application core
│   ├── features/          # Feature modules
│   ├── integrations/     # External integrations
│   └── common/           # Shared utilities
├── tests/                # Test suite
├── scripts/              # Utility scripts
```

## Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker and Docker Compose

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bale_bot
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   # Required for bot: BALE_BOT_TOKEN=your_bot_token_here
   ```
   
   **Bot Configuration:**
   - `BALE_BOT_TOKEN` - Your Bale bot token (required for bot service)
   - `BALE_API_URL` - Bale API endpoint (defaults to `https://tapi.bale.ai/bot{0}/{1}`)
   
   The bot service starts automatically when the application starts if `BALE_BOT_TOKEN` is configured.

3. **Start with Docker Compose (Development)**
   ```bash
   cd /root/Documents/bale_bot
   docker-compose -f docker/docker-compose.dev.yml up
   ```
   See [DOCUMENTATION.md](./DOCUMENTATION.md) for detailed Docker setup instructions.

4. **Or run locally**
   ```bash
   # Install dependencies
   uv sync

   # Set up database
   # Run migrations (see DOCUMENTATION.md for details)
   export PYTHONPATH=$(pwd)/src:$PYTHONPATH
   uv run alembic upgrade head

   # Run the application
   uv run uvicorn src.app.main:app --reload
   ```

## Documentation

- **[DOCUMENTATION.md](./DOCUMENTATION.md)** - Complete setup, development, and deployment guide
  - Docker setup and usage
  - Local development (without Docker)
  - Database migrations (local and Docker)
  - Troubleshooting
- **[BOT_TESTING.md](../BOT_TESTING.md)** - How to test the bot and view logs

## Bot Service

The bot service is integrated into the FastAPI application and starts automatically.

**Bot Commands:**
- `/start` - Get a greeting message
- `/echo <text>` - Echo back the provided text

**Bot Status:**
- Check bot status: `http://localhost:8000/bot/status`
- View bot logs: `make dev-logs-backend` (look for bot status messages)

**Configuration:**
- Set `BALE_BOT_TOKEN` in your `.env` file
- Bot starts automatically when the application starts
- See [BOT_TESTING.md](../BOT_TESTING.md) for testing instructions

## API Documentation

- Bot API: `http://localhost:8000/api/bot`
- Admin API: `http://localhost:8000/api/admin`
- Bot Status: `http://localhost:8000/bot/status`
- OpenAPI docs: `http://localhost:8000/docs`

## Database Migrations

See **[DOCUMENTATION.md](./DOCUMENTATION.md)** for complete migration guide.

**Quick commands:**
```bash
# Set PYTHONPATH
export PYTHONPATH=$(pwd)/src:$PYTHONPATH

# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

## Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src
```

## Production Deployment

1. **Build production image**
   ```bash
   docker build -f docker/Dockerfile -t bale-bot-backend .
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.prod.yml up -d
   ```

## License

[Your License Here]
