"""
API module for Discord Publish Bot.

Provides HTTP API functionality with FastAPI.
"""

from .app import app, create_app
from .dependencies import get_github_client, get_publishing_service, get_discord_handler
from .models import *

__all__ = [
    "app",
    "create_app", 
    "get_github_client",
    "get_publishing_service",
    "get_discord_handler",
    # Models
    "PublishRequest",
    "PublishResponse",
    "DiscordMessageRequest",
    "HealthResponse",
    "PostListResponse",
    "ErrorResponse",
]
