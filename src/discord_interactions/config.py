"""
Discord HTTP Interactions Configuration

Handles Discord application configuration for HTTP interactions.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DiscordConfig:
    """Configuration for Discord HTTP interactions."""
    
    # Discord Application Settings
    application_id: str
    public_key: str
    bot_token: str
    
    # Authorization
    authorized_user_id: str
    
    # API Integration
    publishing_api_endpoint: str
    api_key: str
    
    @classmethod
    def from_env(cls) -> "DiscordConfig":
        """Create configuration from environment variables."""
        return cls(
            application_id=os.getenv("DISCORD_APPLICATION_ID", ""),
            public_key=os.getenv("DISCORD_PUBLIC_KEY", ""),
            bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
            authorized_user_id=os.getenv("DISCORD_USER_ID", ""),
            publishing_api_endpoint=os.getenv("FASTAPI_ENDPOINT", "http://localhost:8000"),
            api_key=os.getenv("API_KEY", ""),
        )
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration and return any missing values."""
        errors = []
        
        if not self.application_id:
            errors.append("DISCORD_APPLICATION_ID is required")
        if not self.public_key:
            errors.append("DISCORD_PUBLIC_KEY is required")
        if not self.bot_token:
            errors.append("DISCORD_BOT_TOKEN is required")
        if not self.authorized_user_id:
            errors.append("DISCORD_USER_ID is required")
        if not self.api_key:
            errors.append("API_KEY is required")
            
        return len(errors) == 0, errors
