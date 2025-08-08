"""
Publishing API - Main FastAPI Application

Based on Technical Specification v1.0
Implements REST API for GitHub publishing with authentication.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import APIConfig
from .github_client import GitHubClient
from .publishing import PublishingService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("publishing_api.log")],
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Discord Publishing API",
    description="API for publishing Discord posts to GitHub repository",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global configuration and services
config: APIConfig = None
publishing_service: PublishingService = None


# Pydantic models
class PublishRequest(BaseModel):
    """Request model for publishing posts."""

    message: str = Field(
        ..., description="Discord command message with content", min_length=1
    )
    user_id: str = Field(..., description="Discord user ID", min_length=1)


class PublishResponse(BaseModel):
    """Response model for successful publishing."""

    status: str = Field(default="success", description="Response status")
    filepath: str = Field(..., description="Path to created file in repository")
    commit_sha: str = Field(None, description="GitHub commit SHA")
    site_url: str = Field(None, description="URL to published post on static site")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: Dict[str, Any] = Field(..., description="Error details")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="Current timestamp")
    checks: Dict[str, str] = Field(
        ..., description="Individual component health checks"
    )


# Dependency functions
async def verify_api_key(
    x_api_key: str = Header(None, description="API authentication key")
):
    """Verify API key from header."""
    if not x_api_key or x_api_key != config.api_key:
        logger.warning(
            f"Invalid API key attempt: {x_api_key[:8] if x_api_key else 'None'}..."
        )
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


async def verify_user_id(request: PublishRequest):
    """Verify Discord user ID authorization."""
    if request.user_id != config.discord_user_id:
        logger.warning(f"Unauthorized user attempt: {request.user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized user")
    return request


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_exception",
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "server_error",
            }
        },
    )


# API Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check endpoint.

    Checks API configuration and external service connectivity.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {},
    }

    # Check configuration
    try:
        config.validate()
        health_status["checks"]["config"] = "healthy"
    except Exception as e:
        health_status["checks"]["config"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check GitHub connectivity
    try:
        github_client = GitHubClient(config.github_token, config.github_repo)
        await github_client.check_connectivity()
        health_status["checks"]["github"] = "healthy"
    except Exception as e:
        health_status["checks"]["github"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.post("/publish", response_model=PublishResponse)
async def publish_post(
    request: PublishRequest,
    api_key: str = Depends(verify_api_key),
    validated_request: PublishRequest = Depends(verify_user_id),
):
    """
    Publish a Discord post to GitHub repository.

    Processes Discord message content, generates markdown with frontmatter,
    and commits to the configured GitHub repository.
    """
    try:
        logger.info(f"Publishing request from user {request.user_id}")

        # Process the post
        result = await publishing_service.publish_post(
            message=request.message, user_id=request.user_id
        )

        logger.info(f"Successfully published post: {result['filepath']}")
        return PublishResponse(**result)

    except ValueError as e:
        # Client error (bad request)
        logger.warning(f"Publishing validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Server error
        logger.error(f"Publishing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Publishing failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Discord Publishing API",
        "version": "1.0.0",
        "description": "API for publishing Discord posts to GitHub repository",
        "endpoints": {"health": "/health", "publish": "/publish", "docs": "/docs"},
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global config, publishing_service

    try:
        # Load configuration
        config = APIConfig.from_env()
        config.validate()

        # Initialize services
        github_client = GitHubClient(config.github_token, config.github_repo)
        publishing_service = PublishingService(github_client, config)

        logger.info("Publishing API started successfully")
        logger.info(f"Repository: {config.github_repo}")
        logger.info(f"Branch: {config.github_branch}")

    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Publishing API shutting down")


if __name__ == "__main__":
    import uvicorn

    # Development server
    # In production, use: uv run uvicorn src.publishing_api.main:app --host 0.0.0.0 --port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
