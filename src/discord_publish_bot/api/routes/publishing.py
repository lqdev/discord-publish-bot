"""
Publishing API routes.

Provides HTTP endpoints for content publishing functionality.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from ...shared import PostData, ValidationError as AppValidationError
from ...publishing import PublishingService
from ..models import PublishRequest, PublishResponse, DiscordMessageRequest, PostListResponse
from ..dependencies import get_publishing_service, verify_api_key, verify_discord_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/publish", response_model=PublishResponse)
async def publish_post(
    request: PublishRequest,
    api_key: str = Depends(verify_api_key),
    publishing_service: PublishingService = Depends(get_publishing_service)
):
    """
    Publish a structured post to GitHub.
    
    This endpoint accepts structured post data and publishes it to the configured repository.
    """
    try:
        # Convert request to PostData
        post_data = PostData(
            title=request.title,
            content=request.content,
            post_type=request.post_type,
            tags=request.tags,
            target_url=request.target_url,
            media_url=request.media_url
        )
        
        # Publish the post
        result = await publishing_service.publish_post(post_data)
        
        # Convert result to response model
        return PublishResponse(
            success=result.success,
            message=result.message,
            filename=result.filename,
            filepath=result.filepath,
            commit_sha=result.commit_sha,
            branch_name=result.branch_name,
            file_url=result.file_url,
            site_url=result.site_url,
            error_code=result.error_code,
            error_details=result.error_details
        )
        
    except AppValidationError as e:
        logger.warning(f"Validation error in publish_post: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in publish_post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish/discord", response_model=PublishResponse)
async def publish_from_discord_message(
    request: DiscordMessageRequest,
    publishing_service: PublishingService = Depends(get_publishing_service)
):
    """
    Publish content from Discord message format.
    
    This endpoint provides backward compatibility for Discord bot integration
    by accepting Discord command message format.
    """
    try:
        # Verify user authorization
        verify_discord_user(request.user_id)
        
        # Publish using Discord message format
        result = await publishing_service.publish_from_discord_message(
            message=request.message,
            user_id=request.user_id
        )
        
        # Convert result to response model
        return PublishResponse(
            success=result.success,
            message=result.message,
            filename=result.filename,
            filepath=result.filepath,
            commit_sha=result.commit_sha,
            branch_name=result.branch_name,
            file_url=result.file_url,
            site_url=result.site_url,
            error_code=result.error_code,
            error_details=result.error_details
        )
        
    except Exception as e:
        logger.error(f"Error in publish_from_discord_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts", response_model=PostListResponse)
async def list_recent_posts(
    limit: int = 10,
    api_key: str = Depends(verify_api_key),
    publishing_service: PublishingService = Depends(get_publishing_service)
):
    """
    List recent posts from the repository.
    
    Returns a list of recently published posts with metadata.
    """
    try:
        if limit > 100:
            raise HTTPException(status_code=400, detail="Limit cannot exceed 100")
        
        posts = await publishing_service.list_recent_posts(limit=limit)
        
        return PostListResponse(
            posts=posts,
            total=len(posts)
        )
        
    except Exception as e:
        logger.error(f"Error listing posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
