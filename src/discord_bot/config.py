"""
Configuration management for Discord bot.

Handles environment variable loading and validation.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BotConfig:
    """Configuration class for Discord bot settings."""

    discord_bot_token: str
    discord_user_id: str
    api_key: str
    fastapi_endpoint: str
    discord_guild_id: Optional[str] = None
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "BotConfig":
        """Create configuration from environment variables."""
        # Required configuration
        discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
        discord_user_id = os.getenv("DISCORD_USER_ID")
        api_key = os.getenv("API_KEY")
        fastapi_endpoint = os.getenv("FASTAPI_ENDPOINT")

        # Validate required configuration
        if not discord_bot_token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
        if not discord_user_id:
            raise ValueError("DISCORD_USER_ID environment variable is required")
        if not api_key:
            raise ValueError("API_KEY environment variable is required")
        if not fastapi_endpoint:
            raise ValueError("FASTAPI_ENDPOINT environment variable is required")

        # Optional configuration
        discord_guild_id = os.getenv("DISCORD_GUILD_ID")
        log_level = os.getenv("LOG_LEVEL", "INFO")

        return cls(
            discord_bot_token=discord_bot_token,
            discord_user_id=discord_user_id,
            api_key=api_key,
            fastapi_endpoint=fastapi_endpoint,
            discord_guild_id=discord_guild_id,
            log_level=log_level,
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if not self.discord_bot_token.startswith(("MTAx", "OTk")):
            raise ValueError("Invalid Discord bot token format")

        if not self.discord_user_id.isdigit():
            raise ValueError("Discord user ID must be numeric")

        if len(self.api_key) < 16:
            raise ValueError("API key must be at least 16 characters")

        if not self.fastapi_endpoint.startswith(("http://", "https://")):
            raise ValueError("FastAPI endpoint must be a valid URL")
