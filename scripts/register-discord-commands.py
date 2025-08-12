#!/usr/bin/env python3
"""
Register Discord slash commands with proper choices for HTTP interactions.

This script registers the /post command with Discord's API so that users see
the proper dropdown choices for post_type and response_type parameters.
"""

import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Any

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Discord API configuration
DISCORD_API_BASE = "https://discord.com/api/v10"
APPLICATION_ID = os.getenv("DISCORD_APPLICATION_ID")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")  # Optional - for faster testing

def get_headers() -> Dict[str, str]:
    """Get headers for Discord API requests."""
    return {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }

def create_command_definitions() -> List[Dict[str, Any]]:
    """Create command definitions for Discord API."""
    return [
        {
            "name": "ping",
            "description": "Check if the bot is responsive",
            "type": 1  # CHAT_INPUT
        },
        {
            "name": "post",
            "description": "Create a new post",
            "type": 1,  # CHAT_INPUT
            "options": [
                {
                    "name": "post_type",
                    "description": "Type of post to create",
                    "type": 3,  # STRING
                    "required": True,
                    "choices": [
                        {"name": "note", "value": "note"},
                        {"name": "response", "value": "response"},
                        {"name": "bookmark", "value": "bookmark"},
                        {"name": "media", "value": "media"}
                    ]
                },
                {
                    "name": "response_type",
                    "description": "Type of response (only for response posts)",
                    "type": 3,  # STRING
                    "required": False,
                    "choices": [
                        {"name": "reply", "value": "reply"},
                        {"name": "repost", "value": "reshare"},  # User sees "repost", maps to "reshare" in frontmatter
                        {"name": "like", "value": "star"}       # User sees "like", maps to "star" in frontmatter
                    ]
                },
                {
                    "name": "attachment",
                    "description": "Upload an image file (for media posts)",
                    "type": 11,  # ATTACHMENT
                    "required": False
                }
            ]
        }
    ]

async def register_global_commands(client: httpx.AsyncClient) -> bool:
    """Register commands globally (takes up to 1 hour to propagate)."""
    url = f"{DISCORD_API_BASE}/applications/{APPLICATION_ID}/commands"
    commands = create_command_definitions()
    
    try:
        logger.info("Registering global commands...")
        response = await client.put(url, headers=get_headers(), json=commands)
        
        if response.status_code == 200:
            registered_commands = response.json()
            logger.info(f"Successfully registered {len(registered_commands)} global commands")
            for cmd in registered_commands:
                logger.info(f"  - {cmd['name']}: {cmd['description']}")
            return True
        else:
            logger.error(f"Failed to register global commands: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error registering global commands: {e}")
        return False

async def register_guild_commands(client: httpx.AsyncClient, guild_id: str) -> bool:
    """Register commands for a specific guild (immediate effect for testing)."""
    url = f"{DISCORD_API_BASE}/applications/{APPLICATION_ID}/guilds/{guild_id}/commands"
    commands = create_command_definitions()
    
    try:
        logger.info(f"Registering guild commands for guild {guild_id}...")
        response = await client.put(url, headers=get_headers(), json=commands)
        
        if response.status_code == 200:
            registered_commands = response.json()
            logger.info(f"Successfully registered {len(registered_commands)} guild commands")
            for cmd in registered_commands:
                logger.info(f"  - {cmd['name']}: {cmd['description']}")
            return True
        else:
            logger.error(f"Failed to register guild commands: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error registering guild commands: {e}")
        return False

async def list_existing_commands(client: httpx.AsyncClient, guild_id: str = None) -> None:
    """List existing commands for debugging."""
    if guild_id:
        url = f"{DISCORD_API_BASE}/applications/{APPLICATION_ID}/guilds/{guild_id}/commands"
        scope = f"guild {guild_id}"
    else:
        url = f"{DISCORD_API_BASE}/applications/{APPLICATION_ID}/commands"
        scope = "global"
    
    try:
        logger.info(f"Listing existing {scope} commands...")
        response = await client.get(url, headers=get_headers())
        
        if response.status_code == 200:
            commands = response.json()
            if commands:
                logger.info(f"Found {len(commands)} existing {scope} commands:")
                for cmd in commands:
                    options_info = ""
                    if "options" in cmd:
                        option_names = [opt["name"] for opt in cmd["options"]]
                        options_info = f" (options: {', '.join(option_names)})"
                    logger.info(f"  - {cmd['name']}: {cmd['description']}{options_info}")
            else:
                logger.info(f"No existing {scope} commands found")
        else:
            logger.error(f"Failed to list {scope} commands: {response.status_code} {response.text}")
            
    except Exception as e:
        logger.error(f"Error listing {scope} commands: {e}")

async def validate_configuration() -> bool:
    """Validate required configuration."""
    missing = []
    
    if not APPLICATION_ID:
        missing.append("DISCORD_APPLICATION_ID")
    if not BOT_TOKEN:
        missing.append("DISCORD_BOT_TOKEN")
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please ensure your .env file contains all required Discord credentials")
        return False
    
    logger.info("Configuration validated successfully")
    logger.info(f"Application ID: {APPLICATION_ID}")
    logger.info(f"Guild ID: {GUILD_ID if GUILD_ID else 'Not set (global registration)'}")
    
    return True

async def main():
    """Main command registration process."""
    print("🚀 Discord Command Registration Tool")
    print("=" * 50)
    
    # Validate configuration
    if not await validate_configuration():
        sys.exit(1)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # List existing commands for debugging
        if GUILD_ID:
            await list_existing_commands(client, GUILD_ID)
        await list_existing_commands(client)
        
        print("\n" + "=" * 50)
        
        # Register commands
        success = False
        
        if GUILD_ID:
            # Register to guild first for immediate testing
            logger.info("GUILD_ID provided - registering guild commands for immediate effect")
            success = await register_guild_commands(client, GUILD_ID)
            
            if success:
                print("\n✅ Guild commands registered successfully!")
                print("Commands are now available immediately in your test server.")
                print("You should see the dropdown choices for post_type and response_type.")
        
        # Always register globally for production
        logger.info("Registering global commands for production...")
        global_success = await register_global_commands(client)
        
        if global_success:
            print("\n✅ Global commands registered successfully!")
            print("Global commands will be available in ~1 hour across all servers.")
        
        if success or global_success:
            print("\n🎯 Next steps:")
            print("1. Try the /post command in Discord")
            print("2. You should see dropdown choices for:")
            print("   - post_type: note, response, bookmark, media")
            print("   - response_type: reply, repost, like (for response posts)")
            print("   - attachment: Upload file option (for media posts)")
            print("3. The response_type dropdown should appear when you select 'response' as post_type")
            print("4. The attachment option allows file uploads for media posts")
        else:
            print("\n❌ Command registration failed!")
            print("Please check your Discord credentials and try again.")
            sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nRegistration cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
