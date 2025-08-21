"""
Discord Publish Bot - Modern content publishing system.

A unified Discord bot and HTTP API for publishing content to GitHub repositories
with support for multiple post types and deployment modes.
"""

__version__ = "2.2.2"

from .config import get_settings
from .shared import PostType, PostData, PublishResult
from .discord import DiscordBot, DiscordInteractionsHandler
from .publishing import GitHubClient, PublishingService
from .api import app, create_app

__all__ = [
    # Version
    "__version__",
    
    # Configuration
    "get_settings",
    
    # Shared types
    "PostType",
    "PostData", 
    "PublishResult",
    
    # Discord components
    "DiscordBot",
    "DiscordInteractionsHandler",
    
    # Publishing components
    "GitHubClient",
    "PublishingService",
    
    # API components
    "app",
    "create_app",
]
