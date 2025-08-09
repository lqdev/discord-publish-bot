"""
Combined FastAPI Application

Integrates Discord HTTP interactions with the existing publishing API.
This creates a single FastAPI application that can handle both Discord webhooks
and direct API access, perfect for Azure Container Apps deployment.
"""

import logging
import asyncio
import sys
import os
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

# Add src to Python path to handle imports properly
if __name__ == "__main__" or "combined_app" in __name__:
    current_dir = os.path.dirname(__file__)
    src_dir = os.path.dirname(current_dir) if current_dir.endswith('src') else current_dir
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

# Import existing publishing API
from publishing_api.main import app as publishing_app

# Import Discord interactions
from discord_interactions.config import DiscordConfig
from discord_interactions.bot import DiscordInteractionsBot
from discord_interactions.api_client import InteractionsAPIClient, PostData


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Discord configuration
discord_config = DiscordConfig.from_env()
is_valid, errors = discord_config.validate()

if not is_valid:
    logger.warning(f"Discord configuration incomplete: {errors}")
    logger.warning("Discord interactions will be disabled")
    discord_bot = None
    interactions_client = None
else:
    discord_bot = DiscordInteractionsBot(discord_config)
    interactions_client = InteractionsAPIClient(
        discord_config.publishing_api_endpoint,
        discord_config.api_key
    )

# Create combined FastAPI app
app = FastAPI(
    title="Discord Publishing Bot - Combined API",
    description="Discord HTTP interactions + Publishing API for serverless deployment",
    version="2.0.0"
)

# Mount the existing publishing API
app.mount("/api", publishing_app)


@app.get("/")
async def root():
    """Root endpoint with service status."""
    return {
        "service": "Discord Publishing Bot",
        "version": "2.0.0",
        "discord_enabled": discord_bot is not None,
        "endpoints": {
            "discord_interactions": "/discord/interactions",
            "publishing_api": "/api/*",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Azure Container Apps."""
    return {
        "status": "healthy",
        "discord_configured": discord_bot is not None,
        "api_configured": True
    }


@app.post("/discord/interactions")
async def discord_interactions(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Discord HTTP interactions.
    
    This endpoint receives webhooks from Discord and processes them.
    """
    if not discord_bot:
        raise HTTPException(
            status_code=503,
            detail="Discord interactions not configured"
        )
    
    # Get signature headers
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    
    if not signature or not timestamp:
        raise HTTPException(
            status_code=401,
            detail="Missing signature headers"
        )
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify Discord signature
    if not discord_bot.verify_signature(signature, timestamp, body):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )
    
    # Parse interaction data
    try:
        interaction = await request.json()
    except Exception as e:
        logger.error(f"Error parsing interaction: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON"
        )
    
    # Handle interaction
    response = discord_bot.handle_interaction(interaction)
    
    # If this is a deferred modal submission, process it in the background
    if (interaction.get("type") == 5 and  # MODAL_SUBMIT
        "custom_id" in interaction.get("data", {}) and
        interaction["data"]["custom_id"].startswith("post_modal_")):
        
        background_tasks.add_task(
            process_post_creation,
            interaction,
            discord_config.application_id
        )
    
    return JSONResponse(content=response)


async def process_post_creation(interaction: Dict[str, Any], application_id: str):
    """
    Process post creation in the background after deferred response.
    
    Args:
        interaction: Discord modal submit interaction
        application_id: Discord application ID for followup
    """
    if not interactions_client:
        logger.error("Interactions client not configured")
        return
    
    try:
        # Extract post type and form data
        custom_id = interaction["data"]["custom_id"]
        post_type = custom_id.replace("post_modal_", "")
        
        # Extract form data
        form_data = {}
        for action_row in interaction["data"]["components"]:
            for component in action_row["components"]:
                if component["type"] == 4:  # TEXT_INPUT
                    custom_id = component["custom_id"]
                    value = component.get("value", "")
                    form_data[custom_id] = value
        
        # Create PostData object
        post_data = PostData(
            title=form_data.get("title", ""),
            content=form_data.get("content", ""),
            post_type=post_type,
            tags=form_data.get("tags"),
            reply_to_url=form_data.get("reply_to_url"),
            bookmark_url=form_data.get("bookmark_url"),
            media_url=form_data.get("media_url")
        )
        
        # Validate required fields
        if not post_data.title or not post_data.content:
            await interactions_client.send_followup_message(
                application_id,
                interaction["token"],
                "❌ Title and content are required."
            )
            return
        
        # Create the post
        result = await interactions_client.create_post(post_data)
        
        # Send followup message
        if result["success"]:
            message = f"✅ {post_type.title()} post created successfully!\n🔗 {result['url']}"
        else:
            message = f"❌ Error creating post: {result['error']}"
        
        await interactions_client.send_followup_message(
            application_id,
            interaction["token"],
            message
        )
        
    except Exception as e:
        logger.error(f"Error processing post creation: {e}")
        if interactions_client:
            await interactions_client.send_followup_message(
                application_id,
                interaction["token"],
                f"❌ Error processing post: {str(e)}"
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    """Entry point for UV script."""
    import uvicorn
    uvicorn.run("src.combined_app:app", host="0.0.0.0", port=8000, reload=True)
