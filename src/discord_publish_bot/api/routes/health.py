"""
Health check routes for API monitoring.

Provides endpoints for health monitoring and status checking.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends

from ...config import AppSettings
from ...publishing import GitHubClient
from ..models import HealthResponse
from ..dependencies import get_settings_dependency, get_github_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: AppSettings = Depends(get_settings_dependency)
):
    """
    Basic health check endpoint.
    
    Returns application health status without external dependencies.
    """
    return HealthResponse(
        status="healthy",
        version=settings.version,
        environment=settings.environment,
        discord_configured=bool(settings.discord.bot_token),
        github_configured=bool(settings.github.token and settings.github.repository),
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/health/detailed", response_model=HealthResponse)
async def detailed_health_check(
    settings: AppSettings = Depends(get_settings_dependency),
    github_client: GitHubClient = Depends(get_github_client)
):
    """
    Detailed health check with external service connectivity.
    
    Tests connections to external services like GitHub.
    """
    # Test GitHub connectivity
    github_connectivity = None
    try:
        github_connectivity = await github_client.check_connectivity()
    except Exception as e:
        logger.warning(f"GitHub connectivity check failed: {e}")
        github_connectivity = False
    
    return HealthResponse(
        status="healthy" if github_connectivity else "degraded",
        version=settings.version,
        environment=settings.environment,
        discord_configured=bool(settings.discord.bot_token),
        github_configured=bool(settings.github.token and settings.github.repository),
        github_connectivity=github_connectivity,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/ready")
async def readiness_check(
    settings: AppSettings = Depends(get_settings_dependency)
):
    """
    Kubernetes readiness probe endpoint.
    
    Returns 200 if service is ready to accept traffic.
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Returns 200 if service is alive.
    """
    return {"status": "alive"}
