"""
Discord webhook routes for HTTP interactions.

Handles Discord HTTP interactions for serverless deployment.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends

from ...shared import DiscordSignatureError, PostData
from ...discord import DiscordInteractionsHandler
from ...publishing import PublishingService
from ..dependencies import get_discord_handler, get_publishing_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/interactions")
async def discord_interactions(
    request: Request,
    background_tasks: BackgroundTasks,
    discord_handler: DiscordInteractionsHandler = Depends(get_discord_handler),
    publishing_service: PublishingService = Depends(get_publishing_service)
):
    """
    Handle Discord HTTP interactions.
    
    This endpoint receives webhooks from Discord and processes them.
    """
    # Get signature headers
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    
    if not signature or not timestamp:
        logger.warning("Missing Discord signature headers")
        raise HTTPException(
            status_code=401,
            detail="Missing signature headers"
        )
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify Discord signature
    try:
        discord_handler.verify_signature(signature, timestamp, body)
    except DiscordSignatureError as e:
        logger.warning(f"Discord signature verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )
    
    # Parse interaction data
    try:
        interaction = await request.json()
    except Exception as e:
        logger.error(f"Error parsing interaction JSON: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON"
        )
    
    # Handle interaction
    try:
        response = discord_handler.handle_interaction(interaction)
        
        # If this is a deferred modal submission, process it in the background
        if (interaction.get("type") == 5 and  # MODAL_SUBMIT
            "custom_id" in interaction.get("data", {}) and
            interaction["data"]["custom_id"].startswith("post_modal_")):
            
            background_tasks.add_task(
                process_post_creation,
                interaction,
                discord_handler,
                publishing_service
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling Discord interaction: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process interaction"
        )


async def process_post_creation(
    interaction: Dict[str, Any],
    discord_handler: DiscordInteractionsHandler,
    publishing_service: PublishingService
):
    """
    Process post creation in the background after deferred response.
    
    Args:
        interaction: Discord modal submit interaction
        discord_handler: Discord interactions handler
        publishing_service: Publishing service
    """
    try:
        # Extract post data from modal submission
        post_data = discord_handler.extract_post_data_from_modal(interaction)
        
        # Validate required fields
        if not post_data.title or not post_data.content:
            await send_discord_followup(
                interaction,
                "❌ Title and content are required."
            )
            return
        
        # Publish the post
        result = await publishing_service.publish_post(post_data)
        
        # Send followup message
        if result.success:
            message = f"✅ {post_data.post_type.value.title()} post created successfully!"
            if result.site_url:
                message += f"\n🔗 {result.site_url}"
        else:
            message = f"❌ {result.message}"
        
        await send_discord_followup(interaction, message)
        
        logger.info(f"Successfully processed post creation: {result.filename}")
        
    except Exception as e:
        logger.error(f"Error processing post creation: {e}")
        await send_discord_followup(
            interaction,
            f"❌ Error processing post: {str(e)}"
        )


async def send_discord_followup(interaction: Dict[str, Any], message: str):
    """
    Send followup message to Discord interaction.
    
    Args:
        interaction: Discord interaction data
        message: Message to send
    """
    try:
        import aiohttp
        
        application_id = interaction.get("application_id")
        token = interaction.get("token")
        
        if not application_id or not token:
            logger.error("Missing application_id or token for followup message")
            return
        
        url = f"https://discord.com/api/v10/webhooks/{application_id}/{token}"
        payload = {
            "content": message,
            "flags": 64  # EPHEMERAL flag
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.debug("Followup message sent successfully")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send followup: {response.status} - {error_text}")
                    
    except Exception as e:
        logger.error(f"Error sending followup message: {e}")
