# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Configure Debian mirror
RUN sed -i 's|http://deb.debian.org/debian|http://mirror-linux.runflare.com/debian|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://security.debian.org/debian-security|http://mirror-linux.runflare.com/debian-security|g' /etc/apt/sources.list.d/debian.sources


# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy backend project metadata and install dependencies (lock keeps images reproducible)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Configure Debian mirror
RUN sed -i 's|http://deb.debian.org/debian|http://mirror-linux.runflare.com/debian|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://security.debian.org/debian-security|http://mirror-linux.runflare.com/debian-security|g' /etc/apt/sources.list.d/debian.sources

# Runtime dependency for psycopg2/libpq
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install uv in runtime image
RUN pip install --no-cache-dir uv

# Copy Python virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code (backend directory contents to /app)
COPY backend/ ./

# Copy docker scripts to a location that won't be overwritten by volume mounts
RUN mkdir -p /docker-scripts
COPY infrastructure/scripts/entrypoint.sh /docker-scripts/entrypoint.sh
COPY infrastructure/scripts/wait_for_db.sh /docker-scripts/wait_for_db.sh

# Strip Windows CRLF so shebang and `set -e` work under Linux
RUN sed -i 's/\r$//' /docker-scripts/*.sh

# Make sure scripts are executable
RUN chmod +x /docker-scripts/*.sh

# Add virtualenv to PATH
ENV PATH=/app/.venv/bin:$PATH

# Working directory is /app (contains backend code)
# No need to change since we copied backend/ to ./

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Use entrypoint script (in /docker-scripts to avoid volume mount conflicts)
ENTRYPOINT ["/docker-scripts/entrypoint.sh"]

# Default command
CMD ["uv", "run", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
