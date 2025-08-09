"""
Combined FastAPI Application

Integrates Discord HTTP interactions with the existing publishing API.
This creates a single FastAPI application that can handle both Discord webhooks
and direct API access, perfect for Azure Container Apps deployment.
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

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
from publishing_api.config import APIConfig
from publishing_api.github_client import GitHubClient
from publishing_api.publishing import PublishingService

# Import Discord interactions
from discord_interactions.config import DiscordConfig
from discord_interactions.bot import DiscordInteractionsBot
from discord_interactions.api_client import PostData

# Import publishing models for the /publish endpoint
from pydantic import BaseModel, Field
from typing import Optional


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
else:
    discord_bot = DiscordInteractionsBot(discord_config)

# Initialize publishing service separately (always try to initialize)
publishing_service = None
try:
    api_config = APIConfig.from_env()
    api_config.validate()
    github_client = GitHubClient(api_config.github_token, api_config.github_repo)
    publishing_service = PublishingService(github_client, api_config)
    logger.info("Publishing service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize publishing service: {e}")
    publishing_service = None

# Create combined FastAPI app
app = FastAPI(
    title="Discord Publishing Bot - Combined API",
    description="Discord HTTP interactions + Publishing API for serverless deployment",
    version="2.0.0"
)

# Mount the existing publishing API
app.mount("/api", publishing_app)


# Helper function for Discord followup messages
async def send_discord_followup(application_id: str, token: str, message: str):
    """Send followup message to Discord interaction."""
    if not discord_bot:
        logger.error("Discord bot not configured for followup message")
        return
        
    import aiohttp
    
    url = f"https://discord.com/api/v10/webhooks/{application_id}/{token}"
    payload = {
        "content": message,
        "flags": 64  # EPHEMERAL flag
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("Followup message sent successfully")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send followup: {response.status} - {error_text}")
    except Exception as e:
        logger.error(f"Error sending followup message: {e}")


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


# Request models for /publish endpoint compatibility
class PublishRequest(BaseModel):
    """Request model for publishing posts (Discord bot compatibility)."""
    message: str = Field(..., description="Discord command message with content", min_length=1)
    user_id: str = Field(..., description="Discord user ID", min_length=1)


class PublishResponse(BaseModel):
    """Response model for publish operations."""
    status: str
    workflow: str
    filepath: str
    branch_name: Optional[str] = None
    commit_sha: Optional[str] = None
    pr_url: Optional[str] = None
    directory: Optional[str] = None
    filename: Optional[str] = None
    site_url_after_merge: Optional[str] = None


@app.post("/publish", response_model=PublishResponse)
async def publish_post_discord_compat(request: PublishRequest):
    """
    Publish a Discord post with field mapping compatibility.
    
    This endpoint provides backward compatibility for the Discord bot
    while applying the target_url field mapping fix.
    """
    if not publishing_service:
        raise HTTPException(
            status_code=503,
            detail="Publishing service not configured"
        )
    
    try:
        # Apply field mapping fix: convert reply_to_url/bookmark_url to target_url
        message = request.message
        
        # Parse the message to extract frontmatter
        lines = message.split('\n')
        if len(lines) < 3 or lines[1] != '---':
            # Not in expected format, pass through as-is
            result = await publishing_service.publish_post(
                message=message, user_id=request.user_id
            )
            return PublishResponse(**result)
        
        # Find the end of frontmatter
        end_idx = None
        for i, line in enumerate(lines[2:], start=2):
            if line == '---':
                end_idx = i
                break
        
        if end_idx is None:
            # No closing frontmatter, pass through as-is
            result = await publishing_service.publish_post(
                message=message, user_id=request.user_id
            )
            return PublishResponse(**result)
        
        # Extract and fix frontmatter
        frontmatter_lines = lines[2:end_idx]
        content_lines = lines[end_idx+1:]
        
        # Apply field mapping fix
        fixed_frontmatter_lines = []
        target_url_found = False
        
        for line in frontmatter_lines:
            line = line.strip()
            if line.startswith('reply_to_url:') or line.startswith('bookmark_url:'):
                # Convert to target_url
                url_value = line.split(':', 1)[1].strip()
                fixed_frontmatter_lines.append(f'target_url: {url_value}')
                target_url_found = True
            else:
                fixed_frontmatter_lines.append(line)
        
        # Rebuild message with fixed frontmatter
        fixed_message = '\n'.join([
            lines[0],  # /post command line
            '---',
            *fixed_frontmatter_lines,
            '---',
            *content_lines
        ])
        
        # Publish with fixed message
        result = await publishing_service.publish_post(
            message=fixed_message, user_id=request.user_id
        )
        return PublishResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in /publish endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    if not publishing_service:
        logger.error("Publishing service not configured")
        await send_discord_followup(
            application_id,
            interaction["token"], 
            "❌ Publishing service not available"
        )
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
            await send_discord_followup(
                application_id,
                interaction["token"],
                "❌ Title and content are required."
            )
            return
        
        # Create frontmatter from structured data 
        frontmatter = {
            "title": post_data.title,
            "type": post_data.post_type,
        }
        
        # Add tags if provided
        if post_data.tags:
            # Split tags and clean them
            tag_list = [tag.strip() for tag in post_data.tags.split(',') if tag.strip()]
            if tag_list:
                frontmatter["tags"] = tag_list
                
        # Map URL fields correctly based on post type
        if post_data.post_type == "response" and post_data.reply_to_url:
            frontmatter["target_url"] = post_data.reply_to_url
        elif post_data.post_type == "bookmark" and post_data.bookmark_url:
            frontmatter["target_url"] = post_data.bookmark_url
        elif post_data.post_type == "media" and post_data.media_url:
            frontmatter["media_url"] = post_data.media_url
        
        # Convert frontmatter to target schema
        target_frontmatter = publishing_service.convert_to_target_schema(
            post_data.post_type, frontmatter, post_data.content
        )
        
        # Generate markdown content
        markdown_content = publishing_service.build_markdown_file(target_frontmatter, post_data.content)
        
        # Generate filename and commit to GitHub
        filename = publishing_service.generate_filename(post_data.post_type, target_frontmatter)
        
        # Create commit
        commit_result = await publishing_service.github_client.create_commit(
            filename=filename,
            content=markdown_content,
            message=f"Add {post_data.post_type} post: {post_data.title}"
        )
        
        # Build success message
        site_url = f"https://{publishing_service.config.github_repo.replace('/', '.github.io/')}/{filename.replace('.md', '.html')}"
        message = f"✅ {post_data.post_type.title()} post created successfully!\n🔗 {site_url}"
        
        await send_discord_followup(
            application_id,
            interaction["token"],
            message
        )
        
        logger.info(f"Successfully created post: {filename}")
        
    except Exception as e:
        logger.error(f"Error processing post creation: {e}")
        await send_discord_followup(
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
