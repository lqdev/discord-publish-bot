"""
Custom exceptions for Discord Publish Bot.

Defines application-specific exceptions with proper error codes and context.
"""

from typing import Any, Dict, Optional


class DiscordPublishBotError(Exception):
    """
    Base exception for all Discord Publish Bot errors.
    
    Provides consistent error handling with error codes and context.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "context": self.context
        }


class ConfigurationError(DiscordPublishBotError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, missing_keys: Optional[list[str]] = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        if missing_keys:
            self.context["missing_keys"] = missing_keys


class DiscordError(DiscordPublishBotError):
    """Base class for Discord-related errors."""
    pass


class DiscordAuthenticationError(DiscordError):
    """Raised when Discord authentication fails."""
    
    def __init__(self, message: str = "Discord authentication failed"):
        super().__init__(message, "DISCORD_AUTH_ERROR")


class DiscordSignatureError(DiscordError):
    """Raised when Discord signature verification fails."""
    
    def __init__(self, message: str = "Invalid Discord signature"):
        super().__init__(message, "DISCORD_SIGNATURE_ERROR")


class DiscordCommandError(DiscordError):
    """Raised when Discord command processing fails."""
    
    def __init__(self, message: str, command: Optional[str] = None):
        super().__init__(message, "DISCORD_COMMAND_ERROR")
        if command:
            self.context["command"] = command


class DiscordModalError(DiscordError):
    """Raised when Discord modal processing fails."""
    
    def __init__(self, message: str, modal_id: Optional[str] = None):
        super().__init__(message, "DISCORD_MODAL_ERROR")
        if modal_id:
            self.context["modal_id"] = modal_id


class PublishingError(DiscordPublishBotError):
    """Base class for publishing-related errors."""
    pass


class GitHubError(PublishingError):
    """Raised when GitHub operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(message, "GITHUB_ERROR")
        if operation:
            self.context["operation"] = operation


class GitHubAuthenticationError(GitHubError):
    """Raised when GitHub authentication fails."""
    
    def __init__(self, message: str = "GitHub authentication failed"):
        super().__init__(message, "GITHUB_AUTH_ERROR")


class GitHubRepositoryError(GitHubError):
    """Raised when GitHub repository operations fail."""
    
    def __init__(self, message: str, repository: Optional[str] = None):
        super().__init__(message, "GITHUB_REPO_ERROR")
        if repository:
            self.context["repository"] = repository


class ContentValidationError(PublishingError):
    """Raised when content validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "CONTENT_VALIDATION_ERROR")
        if field:
            self.context["field"] = field


class FrontmatterError(PublishingError):
    """Raised when frontmatter processing fails."""
    
    def __init__(self, message: str, frontmatter: Optional[Dict[str, Any]] = None):
        super().__init__(message, "FRONTMATTER_ERROR")
        if frontmatter:
            self.context["frontmatter"] = frontmatter


class APIError(DiscordPublishBotError):
    """Base class for API-related errors."""
    pass


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    
    def __init__(self, message: str = "API authentication failed"):
        super().__init__(message, "API_AUTH_ERROR")


class AuthorizationError(APIError):
    """Raised when API authorization fails."""
    
    def __init__(self, message: str = "API authorization failed", user_id: Optional[str] = None):
        super().__init__(message, "API_AUTHORIZATION_ERROR")
        if user_id:
            self.context["user_id"] = user_id


class ValidationError(APIError):
    """Raised when API request validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "API_VALIDATION_ERROR")
        if field:
            self.context["field"] = field


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message, "API_RATE_LIMIT_ERROR")
        if retry_after:
            self.context["retry_after"] = retry_after


class ExternalServiceError(DiscordPublishBotError):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str, service: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        if service:
            self.context["service"] = service
        if status_code:
            self.context["status_code"] = status_code
