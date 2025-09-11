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


class AzureStorageSettings(BaseModel):
    """Azure Storage configuration for permanent media hosting."""
    
    model_config = ConfigDict(extra='ignore')
    
    # Storage Account Configuration
    account_name: Optional[str] = Field(None, description="Azure Storage Account name")
    container_name: str = Field(default="discord-media", description="Blob container for Discord media")
    cdn_endpoint: Optional[str] = Field(None, description="Azure CDN endpoint for improved performance")
    
    # Custom Domain Configuration (for compatibility with Linode)
    custom_domain: Optional[str] = Field(None, description="Custom domain for Azure CDN")
    use_custom_domain: bool = Field(default=False, description="Use custom domain instead of direct blob URLs")
    
    # Authentication Configuration
    use_managed_identity: bool = Field(default=True, description="Use Azure Managed Identity for authentication")
    
    # Media Type Folder Configuration
    images_folder: str = Field(default="images", description="Folder for image files")
    videos_folder: str = Field(default="videos", description="Folder for video files")
    audio_folder: str = Field(default="audio", description="Folder for audio files")
    documents_folder: str = Field(default="documents", description="Folder for document files")
    other_folder: str = Field(default="other", description="Folder for other file types")
    
    # Feature Flags
    enabled: bool = Field(default=False, description="Enable Azure Storage for media hosting")
    use_relative_paths: bool = Field(default=True, description="Use relative paths for domain-mapped containers")
    use_sas_tokens: bool = Field(default=True, description="Use SAS tokens for secure access (recommended)")
    sas_expiry_hours: int = Field(default=8760, description="SAS token expiry in hours (default: 1 year)")
    
    @validator('account_name')
    def validate_account_name(cls, v):
        if v is not None and not v.islower():
            raise ValueError('Azure Storage account name must be lowercase')
        return v
    
    @validator('container_name')
    def validate_container_name(cls, v):
        if not v.islower() or not v.replace('-', '').isalnum():
            raise ValueError('Container name must be lowercase alphanumeric with hyphens')
        return v
    
    @validator('images_folder', 'videos_folder', 'audio_folder', 'documents_folder', 'other_folder')
    def validate_folder_names(cls, v):
        if not v.islower() or not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Folder names must be lowercase alphanumeric with hyphens or underscores')
        return v


class LinodeStorageSettings(BaseModel):
    """Linode Object Storage configuration for permanent media hosting."""
    
    model_config = ConfigDict(extra='ignore')
    
    # Linode Object Storage Credentials (S3-compatible)
    access_key_id: Optional[str] = Field(None, description="Linode Object Storage access key ID")
    secret_access_key: Optional[str] = Field(None, description="Linode Object Storage secret access key")
    endpoint_url: str = Field(default="https://us-east-1.linodeobjects.com", description="Linode Object Storage endpoint URL")
    bucket_name: Optional[str] = Field(None, description="S3-compatible bucket for Discord media")
    region: str = Field(default="us-east-1", description="Linode Object Storage region")
    
    # Custom Domain Configuration
    custom_domain: str = Field(default="https://your-cdn-domain.com", description="Custom CDN domain for media URLs")
    use_custom_domain: bool = Field(default=True, description="Use custom domain instead of direct bucket URLs")
    base_path: str = Field(default="files", description="Base path for media organization")
    
    # Media Type Folder Configuration (matching Azure structure)
    images_folder: str = Field(default="images", description="Folder for image files")
    videos_folder: str = Field(default="videos", description="Folder for video files") 
    audio_folder: str = Field(default="audio", description="Folder for audio files")
    documents_folder: str = Field(default="documents", description="Folder for document files")
    other_folder: str = Field(default="other", description="Folder for other file types")
    
    # Feature Flags
    enabled: bool = Field(default=False, description="Enable Linode Object Storage for media hosting")
    use_signed_urls: bool = Field(default=False, description="Use signed URLs for private access")
    url_expiry_hours: int = Field(default=8760, description="Signed URL expiry in hours (default: 1 year)")
    
    @validator('bucket_name')
    def validate_bucket_name(cls, v):
        if v is not None and (not v.islower() or not v.replace('-', '').replace('.', '').isalnum()):
            raise ValueError('Bucket name must be lowercase alphanumeric with hyphens or dots')
        return v
    
    @validator('custom_domain')
    def validate_custom_domain(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Custom domain must be a valid URL')
        return v
    
    @validator('images_folder', 'videos_folder', 'audio_folder', 'documents_folder', 'other_folder')
    def validate_folder_names(cls, v):
        if not v.islower() or not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Folder names must be lowercase alphanumeric with hyphens or underscores')
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
    
    # Storage Provider Configuration
    storage_provider: Literal["azure", "linode"] = Field(
        default="azure",
        description="Storage provider selection (azure or linode)"
    )
    
    # Component Settings
    discord: DiscordSettings
    github: GitHubSettings  
    api: APISettings
    publishing: PublishingSettings
    azure_storage: AzureStorageSettings = Field(default_factory=AzureStorageSettings)
    linode_storage: LinodeStorageSettings = Field(default_factory=LinodeStorageSettings)
    
    @classmethod
    def from_env(cls) -> "AppSettings":
        """
        Create settings from environment variables.
        
        Maps environment variables to nested configuration structure.
        """
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            storage_provider=os.getenv("STORAGE_PROVIDER", "azure"),
            
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
            ),
            
            azure_storage=AzureStorageSettings(
                account_name=os.getenv("AZURE_STORAGE_ACCOUNT_NAME"),
                container_name=os.getenv("AZURE_STORAGE_CONTAINER_NAME", "discord-media"),
                cdn_endpoint=os.getenv("AZURE_STORAGE_CDN_ENDPOINT"),
                custom_domain=os.getenv("AZURE_STORAGE_CUSTOM_DOMAIN"),
                use_custom_domain=os.getenv("AZURE_STORAGE_USE_CUSTOM_DOMAIN", "false").lower() == "true",
                use_managed_identity=os.getenv("AZURE_STORAGE_USE_MANAGED_IDENTITY", "true").lower() == "true",
                images_folder=os.getenv("AZURE_STORAGE_IMAGES_FOLDER", "images"),
                videos_folder=os.getenv("AZURE_STORAGE_VIDEOS_FOLDER", "videos"),
                audio_folder=os.getenv("AZURE_STORAGE_AUDIO_FOLDER", "audio"),
                documents_folder=os.getenv("AZURE_STORAGE_DOCUMENTS_FOLDER", "documents"),
                other_folder=os.getenv("AZURE_STORAGE_OTHER_FOLDER", "other"),
                enabled=os.getenv("ENABLE_AZURE_STORAGE", "false").lower() == "true",
                use_relative_paths=os.getenv("AZURE_STORAGE_USE_RELATIVE_PATHS", "true").lower() == "true",
                use_sas_tokens=os.getenv("AZURE_STORAGE_USE_SAS_TOKENS", "true").lower() == "true",
                sas_expiry_hours=int(os.getenv("AZURE_STORAGE_SAS_EXPIRY_HOURS", "8760")),
            ),
            
            linode_storage=LinodeStorageSettings(
                access_key_id=os.getenv("LINODE_STORAGE_ACCESS_KEY_ID"),
                secret_access_key=os.getenv("LINODE_STORAGE_SECRET_ACCESS_KEY"),
                endpoint_url=os.getenv("LINODE_STORAGE_ENDPOINT_URL", "https://us-east-1.linodeobjects.com"),
                bucket_name=os.getenv("LINODE_STORAGE_BUCKET_NAME"),
                region=os.getenv("LINODE_STORAGE_REGION", "us-east-1"),
                custom_domain=os.getenv("LINODE_STORAGE_CUSTOM_DOMAIN", "https://cdn.lqdev.tech"),
                use_custom_domain=os.getenv("LINODE_STORAGE_USE_CUSTOM_DOMAIN", "true").lower() == "true",
                base_path=os.getenv("LINODE_STORAGE_BASE_PATH", "files"),
                images_folder=os.getenv("LINODE_STORAGE_IMAGES_FOLDER", "images"),
                videos_folder=os.getenv("LINODE_STORAGE_VIDEOS_FOLDER", "videos"),
                audio_folder=os.getenv("LINODE_STORAGE_AUDIO_FOLDER", "audio"),
                documents_folder=os.getenv("LINODE_STORAGE_DOCUMENTS_FOLDER", "documents"),
                other_folder=os.getenv("LINODE_STORAGE_OTHER_FOLDER", "other"),
                enabled=os.getenv("ENABLE_LINODE_STORAGE", "false").lower() == "true",
                use_signed_urls=os.getenv("LINODE_STORAGE_USE_SIGNED_URLS", "false").lower() == "true",
                url_expiry_hours=int(os.getenv("LINODE_STORAGE_URL_EXPIRY_HOURS", "8760")),
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
