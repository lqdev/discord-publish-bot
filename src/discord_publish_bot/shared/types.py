"""
Shared type definitions for Discord Publish Bot.

Defines common types used across multiple modules.
"""

from typing import Any, Dict, Literal, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field


class PostType(str, Enum):
    """Supported post types."""
    NOTE = "note"
    RESPONSE = "response" 
    BOOKMARK = "bookmark"
    MEDIA = "media"


class ResponseType(str, Enum):
    """Supported response types for response posts."""
    REPLY = "reply"
    REPOST = "reshare"  # Discord shows "repost", frontmatter uses "reshare"
    LIKE = "star"       # Discord shows "like", frontmatter uses "star"


class DeploymentMode(str, Enum):
    """Application deployment modes."""
    WEBSOCKET = "websocket"  # Traditional Discord bot with WebSocket
    HTTP = "http"           # Serverless HTTP interactions


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PostData(BaseModel):
    """
    Structured post data for publishing.
    
    Used to transfer post information between Discord and publishing system.
    """
    
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post content/body")
    post_type: PostType = Field(..., description="Type of post")
    tags: Optional[list[str]] = Field(None, description="Post tags")
    
    # Type-specific fields
    target_url: Optional[str] = Field(None, description="URL for responses and bookmarks")
    response_type: Optional[ResponseType] = Field(None, description="Type of response (reply, repost, like)")
    media_url: Optional[str] = Field(None, description="Media URL for media posts")
    
    # Metadata
    author: Optional[str] = Field(None, description="Post author")
    created_by: Optional[str] = Field(None, description="Discord user ID who created the post")


class PublishResult(BaseModel):
    """
    Result of publishing operation.
    
    Contains all information about the publishing process and outcome.
    """
    
    success: bool = Field(..., description="Whether publishing succeeded")
    message: str = Field(..., description="Human-readable status message")
    
    # File information
    filename: Optional[str] = Field(None, description="Generated filename")
    filepath: Optional[str] = Field(None, description="Full file path in repository")
    
    # Git information
    commit_sha: Optional[str] = Field(None, description="Git commit SHA")
    branch_name: Optional[str] = Field(None, description="Git branch name")
    
    # URLs
    file_url: Optional[str] = Field(None, description="URL to view file in GitHub")
    site_url: Optional[str] = Field(None, description="URL where post will be published")
    pull_request_url: Optional[str] = Field(None, description="URL to pull request if using PR workflow")
    
    # Error information
    error_code: Optional[str] = Field(None, description="Error code if publishing failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error information")


class DiscordInteraction(BaseModel):
    """
    Discord interaction data structure.
    
    Represents incoming Discord interaction payload.
    """
    
    type: int = Field(..., description="Interaction type")
    id: str = Field(..., description="Interaction ID")
    token: str = Field(..., description="Interaction token")
    
    # Application and user information
    application_id: str = Field(..., description="Discord application ID")
    user_id: Optional[str] = Field(None, description="User ID (from member or user)")
    
    # Command/component data
    data: Optional[Dict[str, Any]] = Field(None, description="Interaction data")
    
    # Guild information
    guild_id: Optional[str] = Field(None, description="Guild ID where interaction occurred")
    channel_id: Optional[str] = Field(None, description="Channel ID where interaction occurred")


class DiscordResponse(BaseModel):
    """
    Discord interaction response structure.
    
    Represents outgoing Discord interaction response.
    """
    
    type: int = Field(..., description="Response type")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


# Type aliases for common patterns
ConfigDict = Dict[str, Any]
EnvironmentVars = Dict[str, str]
HTTPHeaders = Dict[str, str]
JSONData = Dict[str, Any]

# Union types for flexibility
StrOrInt = Union[str, int]
OptionalStr = Optional[str]
