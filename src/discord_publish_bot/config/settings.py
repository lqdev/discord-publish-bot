"""
Unified Configuration System for Discord Publish Bot

Uses Pydantic for validation and type safety.
Consolidates all configuration concerns into a single, well-structured system.
"""

import os
from typing import Optional, Literal
from pathlib import Path

from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DiscordSettings(BaseModel):
    """Discord-specific configuration settings."""
    
    model_config = ConfigDict(extra='ignore')
    
    # Bot Authentication
    bot_token: str = Field(..., description="Discord bot token")
    
    # HTTP Interactions (for serverless deployment)
    application_id: Optional[str] = Field(None, description="Discord application ID for HTTP interactions")
    public_key: Optional[str] = Field(None, description="Discord public key for signature verification")
    
    # Authorization
    authorized_user_id: str = Field(..., description="Discord user ID authorized to use the bot")
    
    # Development Settings
    guild_id: Optional[str] = Field(None, description="Discord guild ID for development testing")
    
    @validator('bot_token')
    def validate_bot_token(cls, v):
        if not v or len(v) < 50:  # Discord tokens are typically 70+ chars
            raise ValueError('Invalid Discord bot token format')
        return v
    
    @validator('authorized_user_id')
    def validate_user_id(cls, v):
        if not v.isdigit():
            raise ValueError('Discord user ID must be numeric')
        return v
    
    @validator('application_id')
    def validate_application_id(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError('Discord application ID must be numeric')
        return v


class GitHubSettings(BaseModel):
    """GitHub-specific configuration settings."""
    
    model_config = ConfigDict(extra='ignore')
    
    token: str = Field(..., description="GitHub personal access token")
    repository: str = Field(..., description="GitHub repository in format 'owner/repo'")
    branch: str = Field(default="main", description="Target branch for commits")
    
    @validator('token')
    def validate_token(cls, v):
        if not v.startswith(('ghp_', 'github_pat_', 'gho_', 'ghu_')):
            raise ValueError('Invalid GitHub token format')
        return v
    
    @validator('repository')
    def validate_repository(cls, v):
        if '/' not in v or v.count('/') != 1:
            raise ValueError('Repository must be in format "owner/repo"')
        return v
    
    @property
    def owner(self) -> str:
        """Extract repository owner."""
        return self.repository.split('/')[0]
    
    @property
    def name(self) -> str:
        """Extract repository name."""
        return self.repository.split('/')[1]


class APISettings(BaseModel):
    """API-specific configuration settings."""
    
    model_config = ConfigDict(extra='ignore')
    
    key: str = Field(..., description="API key for authentication")
    host: str = Field(default="0.0.0.0", description="API host address")
    port: int = Field(default=8000, description="API port number")
    endpoint: Optional[str] = Field(None, description="External API endpoint URL")
    
    @validator('key')
    def validate_key(cls, v):
        if len(v) < 16:
            raise ValueError('API key must be at least 16 characters')
        return v
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('API endpoint must be a valid URL')
        return v


class PublishingSettings(BaseModel):
    """Publishing-specific configuration settings."""
    
    model_config = ConfigDict(extra='ignore')
    
    site_base_url: Optional[str] = Field(None, description="Base URL for the published site")
    default_author: Optional[str] = Field(None, description="Default author for posts")
    
    @validator('site_base_url')
    def validate_site_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('Site base URL must be a valid URL')
        return v


class AppSettings(BaseSettings):
    """
    Main application settings.
    
    Consolidates all configuration concerns with proper validation and type safety.
    """
    
    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Ignore extra environment variables
    )
    
    # Application Metadata
    app_name: str = Field(default="Discord Publish Bot", description="Application name")
    version: str = Field(default="2.0.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", 
        description="Application environment"
    )
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", 
        description="Logging level"
    )
    
    # Component Settings
    discord: DiscordSettings
    github: GitHubSettings  
    api: APISettings
    publishing: PublishingSettings
    
    @classmethod
    def from_env(cls) -> "AppSettings":
        """
        Create settings from environment variables.
        
        Maps environment variables to nested configuration structure.
        """
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            
            discord=DiscordSettings(
                bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
                application_id=os.getenv("DISCORD_APPLICATION_ID"),
                public_key=os.getenv("DISCORD_PUBLIC_KEY"),
                authorized_user_id=os.getenv("DISCORD_USER_ID", ""),
                guild_id=os.getenv("DISCORD_GUILD_ID"),
            ),
            
            github=GitHubSettings(
                token=os.getenv("GITHUB_TOKEN", ""),
                repository=os.getenv("GITHUB_REPO", ""),
                branch=os.getenv("GITHUB_BRANCH", "main"),
            ),
            
            api=APISettings(
                key=os.getenv("API_KEY", ""),
                host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("API_PORT", "8000")),
                endpoint=os.getenv("FASTAPI_ENDPOINT"),
            ),
            
            publishing=PublishingSettings(
                site_base_url=os.getenv("SITE_BASE_URL"),
                default_author=os.getenv("DEFAULT_AUTHOR"),
            )
        )
    
    def validate_all(self) -> tuple[bool, list[str]]:
        """
        Validate all configuration and return validation results.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            # Pydantic validation happens automatically during construction
            return True, []
        except Exception as e:
            return False, [str(e)]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def discord_interactions_enabled(self) -> bool:
        """Check if Discord HTTP interactions are properly configured."""
        return (
            self.discord.application_id is not None and 
            self.discord.public_key is not None
        )


# Global settings instance
settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """
    Get global settings instance.
    
    Creates settings from environment if not already initialized.
    """
    global settings
    if settings is None:
        settings = AppSettings.from_env()
    return settings


def reset_settings() -> None:
    """Reset global settings instance (useful for testing)."""
    global settings
    settings = None
