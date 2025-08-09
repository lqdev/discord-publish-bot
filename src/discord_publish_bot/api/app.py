"""
FastAPI application for Discord Publish Bot.

Provides HTTP API endpoints for publishing and Discord webhook integration.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings, AppSettings
from ..shared import (
    PostData,
    PublishResult,
    DiscordSignatureError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    setup_logging
)
from ..discord import DiscordInteractionsHandler
from ..publishing import GitHubClient, PublishingService
from .models import PublishRequest, PublishResponse, HealthResponse
from .dependencies import get_github_client, get_publishing_service, get_discord_handler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown logic.
    """
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Test GitHub connectivity if configured
    try:
        github_client = get_github_client()
        if await github_client.check_connectivity():
            logger.info("GitHub connectivity verified")
        else:
            logger.warning("GitHub connectivity check failed")
    except Exception as e:
        logger.warning(f"GitHub connectivity check error: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    settings = get_settings()
    
    app = FastAPI(
        title="Discord Publish Bot API",
        description="HTTP API for Discord publishing bot with webhook integration",
        version=settings.version,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )
    
    # Add CORS middleware for development
    if settings.is_development:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Include routes
    from .routes import health, discord, publishing
    app.include_router(health.router, tags=["health"])
    app.include_router(discord.router, prefix="/discord", tags=["discord"])
    app.include_router(publishing.router, prefix="/api", tags=["publishing"])
    
    return app


# Create application instance
app = create_app()


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with service information."""
    settings = get_settings()
    
    return {
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "discord_interactions_enabled": settings.discord_interactions_enabled,
        "endpoints": {
            "health": "/health",
            "discord_interactions": "/discord/interactions",
            "publishing": "/api/publish",
            "docs": "/docs" if settings.is_development else None,
        }
    }


# Global exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    logger.warning(f"Authentication failed: {exc.message}")
    return JSONResponse(
        status_code=401,
        content=exc.to_dict()
    )


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors."""
    logger.warning(f"Authorization failed: {exc.message}")
    return JSONResponse(
        status_code=403,
        content=exc.to_dict()
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation failed: {exc.message}")
    return JSONResponse(
        status_code=400,
        content=exc.to_dict()
    )


@app.exception_handler(DiscordSignatureError)
async def discord_signature_error_handler(request: Request, exc: DiscordSignatureError):
    """Handle Discord signature verification errors."""
    logger.warning(f"Discord signature verification failed: {exc.message}")
    return JSONResponse(
        status_code=401,
        content=exc.to_dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
        }
    )
