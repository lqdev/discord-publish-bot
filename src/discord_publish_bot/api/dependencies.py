"""
FastAPI dependency injection functions.

Provides shared instances and validation for API endpoints.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, Header

from ..config import get_settings, AppSettings
from ..shared import AuthenticationError, AuthorizationError
from ..discord import DiscordInteractionsHandler
from ..publishing import GitHubClient, PublishingService

logger = logging.getLogger(__name__)

# Cache instances to avoid recreating on every request
_github_client: Optional[GitHubClient] = None
_publishing_service: Optional[PublishingService] = None
_discord_handler: Optional[DiscordInteractionsHandler] = None


def get_github_client() -> GitHubClient:
    """
    Get or create GitHub client instance.
    
    Returns:
        GitHubClient instance
        
    Raises:
        HTTPException: If GitHub is not configured
    """
    global _github_client
    
    if _github_client is None:
        settings = get_settings()
        
        try:
            _github_client = GitHubClient(
                token=settings.github.token,
                repository=settings.github.repository
            )
            logger.info("GitHub client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            raise HTTPException(
                status_code=500,
                detail="GitHub client initialization failed"
            )
    
    return _github_client


def get_publishing_service(
    github_client: GitHubClient = Depends(get_github_client)
) -> PublishingService:
    """
    Get or create publishing service instance.
    
    Args:
        github_client: GitHub client dependency
        
    Returns:
        PublishingService instance
    """
    global _publishing_service
    
    if _publishing_service is None:
        settings = get_settings()
        
        try:
            _publishing_service = PublishingService(
                github_client=github_client,
                github_settings=settings.github,
                publishing_settings=settings.publishing
            )
            logger.info("Publishing service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize publishing service: {e}")
            raise HTTPException(
                status_code=500,
                detail="Publishing service initialization failed"
            )
    
    return _publishing_service


def get_discord_handler() -> DiscordInteractionsHandler:
    """
    Get or create Discord interactions handler.
    
    Returns:
        DiscordInteractionsHandler instance
        
    Raises:
        HTTPException: If Discord interactions are not configured
    """
    global _discord_handler
    
    if _discord_handler is None:
        settings = get_settings()
        
        if not settings.discord_interactions_enabled:
            raise HTTPException(
                status_code=503,
                detail="Discord interactions not configured"
            )
        
        try:
            _discord_handler = DiscordInteractionsHandler(settings)
            logger.info("Discord interactions handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Discord handler: {e}")
            raise HTTPException(
                status_code=500,
                detail="Discord interactions handler initialization failed"
            )
    
    return _discord_handler


def verify_api_key(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> str:
    """
    Verify API key from request headers.
    
    Args:
        authorization: Authorization header (Bearer token)
        x_api_key: X-API-Key header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: If authentication fails
    """
    settings = get_settings()
    expected_key = settings.api.key
    
    # Check Authorization header (Bearer token)
    if authorization:
        if authorization.startswith("Bearer "):
            provided_key = authorization[7:]  # Remove "Bearer " prefix
            if provided_key == expected_key:
                return provided_key
    
    # Check X-API-Key header
    if x_api_key:
        if x_api_key == expected_key:
            return x_api_key
    
    logger.warning("API authentication failed")
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API key"
    )


def verify_discord_user(
    user_id: str,
    api_key: str = Depends(verify_api_key)
) -> str:
    """
    Verify Discord user authorization.
    
    Args:
        user_id: Discord user ID from request
        api_key: Verified API key
        
    Returns:
        User ID if authorized
        
    Raises:
        HTTPException: If authorization fails
    """
    settings = get_settings()
    
    if user_id != settings.discord.authorized_user_id:
        logger.warning(f"Unauthorized user {user_id} attempted to use API")
        raise HTTPException(
            status_code=403,
            detail="User not authorized to publish posts"
        )
    
    return user_id


def get_settings_dependency() -> AppSettings:
    """Dependency to get application settings."""
    return get_settings()


def reset_dependencies():
    """Reset dependency cache (useful for testing)."""
    global _github_client, _publishing_service, _discord_handler
    _github_client = None
    _publishing_service = None
    _discord_handler = None
