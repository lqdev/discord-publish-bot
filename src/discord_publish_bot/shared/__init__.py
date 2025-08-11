"""
Shared module for Discord Publish Bot.

Provides common utilities, types, and exceptions used across the application.
"""

from .exceptions import *
from .types import *
from .utils import *

__all__ = [
    # Exceptions
    "DiscordPublishBotError",
    "ConfigurationError", 
    "DiscordError",
    "DiscordAuthenticationError",
    "DiscordSignatureError",
    "DiscordCommandError",
    "DiscordModalError",
    "PublishingError",
    "GitHubError",
    "GitHubAuthenticationError",
    "GitHubRepositoryError",
    "ContentValidationError",
    "FrontmatterError",
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "RateLimitError",
    "ExternalServiceError",
    
    # Types
    "PostType",
    "ResponseType",
    "DeploymentMode",
    "Environment",
    "LogLevel",
    "PostData",
    "PublishResult",
    "DiscordInteraction",
    "DiscordResponse",
    "ConfigDict",
    "EnvironmentVars",
    "HTTPHeaders",
    "JSONData",
    "StrOrInt",
    "OptionalStr",
    
    # Utils
    "setup_logging",
    "slugify",
    "generate_filename",
    "validate_url",
    "extract_domain",
    "sanitize_content",
    "parse_tags",
    "format_frontmatter",
    "calculate_content_hash",
    "truncate_text",
    "ensure_directory",
    "format_datetime",
    "mask_sensitive_data",
]
