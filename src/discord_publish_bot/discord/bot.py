"""
Discord WebSocket bot implementation for development and testing.

Traditional Discord bot using WebSocket connections for real-time interaction.
Suitable for development environments where persistent connections are acceptable.
"""

import asyncio
import logging
from typing import Optional, Callable, Awaitable

import discord
from discord import app_commands
from discord.ext import commands

from ..config import DiscordSettings
from ..shared import (
    DiscordAuthenticationError,
    DiscordCommandError,
    PostData,
    PostType,
    parse_tags
)

logger = logging.getLogger(__name__)


class DiscordBot(commands.Bot):
    """
    WebSocket-based Discord bot for development and testing.
    
    Provides full Discord bot functionality with persistent connection,
    suitable for development environments.
    """

    def __init__(
        self, 
        settings: DiscordSettings,
        post_handler: Optional[Callable[[PostData], Awaitable[str]]] = None
    ):
        """
        Initialize Discord bot.
        
        Args:
            settings: Discord configuration settings
            post_handler: Optional async function to handle post creation
        """
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message processing

        super().__init__(
            command_prefix="!",  # Fallback prefix, mainly using slash commands
            intents=intents,
            help_command=None,
        )

        self.settings = settings
        self.post_handler = post_handler
        
        logger.info("Initialized Discord WebSocket bot")

    async def setup_hook(self):
        """Set up slash commands and sync with Discord."""
        try:
            # Add commands
            self.tree.add_command(ping_command)
            self.tree.add_command(post_command)
            
            if self.settings.guild_id:
                # Development: Sync to specific guild for faster testing
                guild = discord.Object(id=int(self.settings.guild_id))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Commands synced to guild {self.settings.guild_id}")
            else:
                # Production: Sync globally (takes up to 1 hour)
                await self.tree.sync()
                logger.info("Commands synced globally")

        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
            raise DiscordAuthenticationError(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Bot ready event handler."""
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")

        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name="for /post commands"
            )
        )

    async def on_error(self, event, *args, **kwargs):
        """Global error handler."""
        logger.error(f"Error in event {event}", exc_info=True)

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot."""
        return str(user_id) == self.settings.authorized_user_id

    async def start_bot(self) -> None:
        """Start the bot with error handling."""
        try:
            logger.info("Starting Discord WebSocket bot...")
            await self.start(self.settings.bot_token)
        except discord.LoginFailure as e:
            logger.error(f"Discord login failed: {e}")
            raise DiscordAuthenticationError(f"Discord login failed: {e}")
        except Exception as e:
            logger.error(f"Bot startup failed: {e}")
            raise DiscordCommandError(f"Bot startup failed: {e}")

    async def handle_post_creation(self, post_data: PostData) -> str:
        """
        Handle post creation with optional external handler.
        
        Args:
            post_data: Post data to process
            
        Returns:
            Result message
        """
        if self.post_handler:
            try:
                return await self.post_handler(post_data)
            except Exception as e:
                logger.error(f"Post handler failed: {e}")
                return f"❌ Failed to create post: {str(e)}"
        else:
            # Default behavior - just acknowledge
            return f"✅ {post_data.post_type.value.title()} post would be created: {post_data.title}"


# Modal classes for different post types
class BasePostModal(discord.ui.Modal):
    """Base modal for post creation."""
    
    def __init__(self, bot: DiscordBot, post_type: PostType):
        super().__init__(title=f"Create {post_type.value.title()} Post")
        self.bot = bot
        self.post_type = post_type
        
        # Common fields
        self.title_input = discord.ui.TextInput(
            label="Title",
            placeholder="Enter post title...",
            max_length=200,
            required=True
        )
        self.add_item(self.title_input)
        
        self.content_input = discord.ui.TextInput(
            label="Content",
            placeholder="Enter post content...",
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=True
        )
        self.add_item(self.content_input)
        
        self.tags_input = discord.ui.TextInput(
            label="Tags (comma-separated)",
            placeholder="tag1, tag2, tag3",
            max_length=200,
            required=False
        )
        self.add_item(self.tags_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            # Build post data
            tags = parse_tags(self.tags_input.value) if self.tags_input.value else None
            
            post_data = PostData(
                title=self.title_input.value.strip(),
                content=self.content_input.value.strip(),
                post_type=self.post_type,
                tags=tags,
                created_by=str(interaction.user.id)
            )
            
            # Add type-specific data
            await self._add_type_specific_data(post_data)
            
            # Defer response
            await interaction.response.defer(ephemeral=True)
            
            # Handle post creation
            result = await self.bot.handle_post_creation(post_data)
            
            # Send followup
            await interaction.followup.send(result, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in modal submission: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Error creating post: {str(e)}", 
                    ephemeral=True
                )
    
    async def _add_type_specific_data(self, post_data: PostData):
        """Add type-specific data to post. Override in subclasses."""
        pass


class NoteModal(BasePostModal):
    """Modal for creating note posts."""
    
    def __init__(self, bot: DiscordBot):
        super().__init__(bot, PostType.NOTE)


class ResponseModal(BasePostModal):
    """Modal for creating response posts."""
    
    def __init__(self, bot: DiscordBot):
        super().__init__(bot, PostType.RESPONSE)
        
        self.target_url_input = discord.ui.TextInput(
            label="Reply to URL",
            placeholder="https://example.com/original-post",
            max_length=500,
            required=True
        )
        self.add_item(self.target_url_input)
    
    async def _add_type_specific_data(self, post_data: PostData):
        """Add target URL for response posts."""
        post_data.target_url = self.target_url_input.value.strip()


class BookmarkModal(BasePostModal):
    """Modal for creating bookmark posts."""
    
    def __init__(self, bot: DiscordBot):
        super().__init__(bot, PostType.BOOKMARK)
        
        self.target_url_input = discord.ui.TextInput(
            label="Bookmark URL",
            placeholder="https://example.com/article",
            max_length=500,
            required=True
        )
        self.add_item(self.target_url_input)
    
    async def _add_type_specific_data(self, post_data: PostData):
        """Add target URL for bookmark posts."""
        post_data.target_url = self.target_url_input.value.strip()


class MediaModal(BasePostModal):
    """Modal for creating media posts."""
    
    def __init__(self, bot: DiscordBot):
        super().__init__(bot, PostType.MEDIA)
        
        self.media_url_input = discord.ui.TextInput(
            label="Media URL",
            placeholder="https://example.com/image.jpg",
            max_length=500,
            required=False
        )
        self.add_item(self.media_url_input)
    
    async def _add_type_specific_data(self, post_data: PostData):
        """Add media URL for media posts."""
        if self.media_url_input.value:
            post_data.media_url = self.media_url_input.value.strip()


# Global commands
@app_commands.command(name="ping", description="Check if the bot is responsive")
async def ping_command(interaction: discord.Interaction):
    """Simple ping command for health checking."""
    bot = interaction.client
    
    if not bot.is_authorized(interaction.user.id):
        await interaction.response.send_message(
            "❌ You are not authorized to use this bot.", 
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "🟢 Bot is healthy and responsive!", 
        ephemeral=True
    )


@app_commands.command(name="post", description="Create a new post")
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
    """Main post command handler."""
    bot = interaction.client
    
    # Check authorization
    if not bot.is_authorized(interaction.user.id):
        await interaction.response.send_message(
            "❌ You are not authorized to use this bot.", 
            ephemeral=True
        )
        return

    # Route to appropriate modal
    modal_map = {
        PostType.NOTE.value: NoteModal,
        PostType.RESPONSE.value: ResponseModal,
        PostType.BOOKMARK.value: BookmarkModal,
        PostType.MEDIA.value: MediaModal,
    }

    try:
        post_type_enum = PostType(post_type)
        modal_class = modal_map[post_type_enum.value]
        modal = modal_class(bot)
        await interaction.response.send_modal(modal)

        logger.info(f"User {interaction.user.id} opened {post_type} modal")

    except Exception as e:
        logger.error(f"Error in post command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while processing your request.", 
            ephemeral=True
        )
