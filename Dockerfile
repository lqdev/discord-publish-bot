# Multi-stage Docker build for Discord Publish Bot - Azure Container Apps Optimized
# Build stage: Compile and install dependencies
FROM python:3.11-slim AS builder

# Set build environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
RUN pip install uv

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies to virtual environment
RUN uv sync --frozen --no-dev

# Production base stage: Minimal runtime image
FROM python:3.11-slim AS production-base

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    ENVIRONMENT=production \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# Create non-root user for security (Azure Container Apps best practice)
RUN groupadd -r --gid 1000 appuser && \
    useradd -r --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# Create app directory with proper permissions
WORKDIR /app
RUN chown -R appuser:appuser /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser README.md ./

# Switch to non-root user (security requirement)
USER appuser

# Health check endpoint for Azure Container Apps probes
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Discord bot only stage
FROM production-base AS discord-bot
CMD ["python", "-m", "discord_publish_bot.discord.main"]

# API server only stage  
FROM production-base AS api-server
EXPOSE 8000
CMD ["python", "-m", "discord_publish_bot.api.main"]

# Default production stage: API server for Azure Container Apps
FROM production-base AS production
EXPOSE 8000
CMD ["python", "-c", "import uvicorn; from discord_publish_bot.api import app; uvicorn.run(app, host='0.0.0.0', port=8000)"]
