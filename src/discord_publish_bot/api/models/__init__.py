"""
Pydantic models for API requests and responses.

Defines data structures for API communication.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ...shared import PostType


class PublishRequest(BaseModel):
    """Request model for publishing posts."""
    
    title: str = Field(..., description="Post title", min_length=1, max_length=200)
    content: str = Field(..., description="Post content", min_length=1)
    post_type: PostType = Field(..., description="Type of post")
    tags: Optional[List[str]] = Field(None, description="Post tags")
    target_url: Optional[str] = Field(None, description="Target URL for responses/bookmarks")
    media_url: Optional[str] = Field(None, description="Media URL for media posts")


class PublishResponse(BaseModel):
    """Response model for publish operations."""
    
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
    
    # Error information
    error_code: Optional[str] = Field(None, description="Error code if publishing failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error information")


class DiscordMessageRequest(BaseModel):
    """Request model for Discord message format publishing."""
    
    message: str = Field(..., description="Discord command message with content", min_length=1)
    user_id: str = Field(..., description="Discord user ID", min_length=1)


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Application environment")
    
    # Component health
    discord_configured: bool = Field(..., description="Whether Discord is configured")
    github_configured: bool = Field(..., description="Whether GitHub is configured")
    github_connectivity: Optional[bool] = Field(None, description="GitHub connectivity status")
    
    # Timestamps
    timestamp: str = Field(..., description="Health check timestamp")


class PostListResponse(BaseModel):
    """Response model for listing posts."""
    
    posts: List[Dict[str, Any]] = Field(..., description="List of recent posts")
    total: int = Field(..., description="Total number of posts returned")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
