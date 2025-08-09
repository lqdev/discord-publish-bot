# Multi-stage Docker build for Discord Publish Bot
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install uv for faster Python package management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY README.md ./

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["uv", "run", "python", "-m", "discord_publish_bot.combined_app"]

# Multi-target build for different services
FROM base as discord-bot
CMD ["uv", "run", "python", "-m", "discord_publish_bot.discord.main"]

FROM base as api-server
EXPOSE 8000
CMD ["uv", "run", "python", "-m", "discord_publish_bot.api.main"]

FROM base as combined
EXPOSE 8000
CMD ["uv", "run", "python", "-m", "discord_publish_bot.combined_app"]
