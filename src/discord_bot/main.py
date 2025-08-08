"""
Discord Publish Bot - Main Entry Point

Based on Technical Specification v1.0
Implements Discord bot with slash commands for content publishing.
"""

import asyncio
import logging
import os
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from .api_client import PublishingAPIClient
from .config import BotConfig
from .modals import BookmarkModal, MediaModal, NoteModal, ResponseModal

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("discord_bot.log")],
)

logger = logging.getLogger(__name__)


class DiscordPublishBot(commands.Bot):
    """
    Main Discord bot class for handling publish commands.

    Implements slash commands for four post types:
    - /post note
    - /post response
    - /post bookmark
    - /post media
    """

    def __init__(self, config: BotConfig):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message processing

        super().__init__(
            command_prefix="!",  # Fallback prefix, mainly using slash commands
            intents=intents,
            help_command=None,
        )

        self.config = config
        self.api_client = PublishingAPIClient(
            base_url=config.fastapi_endpoint, api_key=config.api_key
        )

        logger.info("Discord bot initialized with configuration")

    async def setup_hook(self):
        """Set up slash commands and sync with Discord."""
        try:
            if self.config.discord_guild_id:
                # Development: Sync to specific guild for faster testing
                guild = discord.Object(id=self.config.discord_guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Commands synced to guild {self.config.discord_guild_id}")
            else:
                # Production: Sync globally (takes up to 1 hour)
                await self.tree.sync()
                logger.info("Commands synced globally")

        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Bot ready event handler."""
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")

        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="for /post commands"
            )
        )

    async def on_error(self, event, *args, **kwargs):
        """Global error handler."""
        logger.error(f"Error in event {event}", exc_info=True)

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot."""
        return str(user_id) == self.config.discord_user_id


# Initialize bot instance
bot = None


def create_bot() -> DiscordPublishBot:
    """Create and configure the bot instance."""
    config = BotConfig.from_env()
    return DiscordPublishBot(config)


@app_commands.command(name="post", description="Publish content to your static site")
@app_commands.describe(post_type="Type of post to create")
@app_commands.choices(
    post_type=[
        app_commands.Choice(name="note", value="note"),
        app_commands.Choice(name="response", value="response"),
        app_commands.Choice(name="bookmark", value="bookmark"),
        app_commands.Choice(name="media", value="media"),
    ]
)
async def post_command(interaction: discord.Interaction, post_type: str):
    """
    Main post command handler.

    Routes to appropriate modal based on post type.
    """
    # Check authorization
    if not bot.is_authorized(interaction.user.id):
        await interaction.response.send_message(
            "❌ You are not authorized to use this bot.", ephemeral=True
        )
        return

    # Route to appropriate modal
    modal_map = {
        "note": NoteModal,
        "response": ResponseModal,
        "bookmark": BookmarkModal,
        "media": MediaModal,
    }

    try:
        modal_class = modal_map.get(post_type)
        if not modal_class:
            await interaction.response.send_message(
                f"❌ Unknown post type: {post_type}", ephemeral=True
            )
            return

        modal = modal_class(bot.api_client)
        await interaction.response.send_modal(modal)

        logger.info(f"User {interaction.user.id} opened {post_type} modal")

    except Exception as e:
        logger.error(f"Error in post command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while processing your request.", ephemeral=True
        )


@app_commands.command(name="ping", description="Check if the bot is responsive")
async def ping_command(interaction: discord.Interaction):
    """Simple ping command for health checking."""
    if not bot.is_authorized(interaction.user.id):
        await interaction.response.send_message(
            "❌ You are not authorized to use this bot.", ephemeral=True
        )
        return

    # Check API connectivity
    try:
        health_status = await bot.api_client.check_health()
        if health_status:
            message = "🟢 Bot and API are healthy!"
        else:
            message = "🟡 Bot is healthy, but API is unreachable."
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        message = "🔴 Bot is healthy, but API check failed."

    await interaction.response.send_message(message, ephemeral=True)


async def main():
    """Main entry point for the Discord bot."""
    global bot

    try:
        # Create bot instance
        bot = create_bot()

        # Register commands
        bot.tree.add_command(post_command)
        bot.tree.add_command(ping_command)

        # Start bot
        logger.info("Starting Discord bot...")
        await bot.start(bot.config.discord_bot_token)

    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if bot:
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
