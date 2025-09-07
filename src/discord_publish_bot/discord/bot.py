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
        return str(user_id) == self.settings.discord.authorized_user_id

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
        
        # Add slug field for URL customization (available to all modal types)
        self.slug_input = discord.ui.TextInput(
            label="Custom Slug (optional)",
            placeholder="Leave blank to auto-generate from title",
            max_length=80,
            required=False
        )
        self.add_item(self.slug_input)
    
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
                slug=self.slug_input.value.strip() if self.slug_input.value else None,
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
    
    def __init__(self, bot: DiscordBot, response_type: str = "reply"):
        super().__init__(bot, PostType.RESPONSE)
        self.response_type = response_type
        
        self.target_url_input = discord.ui.TextInput(
            label="Target URL",
            placeholder="https://example.com/original-post",
            max_length=500,
            required=True
        )
        self.add_item(self.target_url_input)
    
    async def _add_type_specific_data(self, post_data: PostData):
        """Add target URL and response type for response posts."""
        from ..shared.types import ResponseType
        
        post_data.target_url = self.target_url_input.value.strip()
        
        # Use the response type from command parameter
        try:
            post_data.response_type = ResponseType(self.response_type)
        except ValueError:
            # Default to reply if invalid
            post_data.response_type = ResponseType.REPLY


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
    """Modal for creating media posts with optional file attachment support."""
    
    def __init__(self, bot: DiscordBot, attachment_url=None, attachment_filename=None, attachment_content_type=None, alt_text=None):
        # Don't call super().__init__() yet - we need to customize field allocation
        discord.ui.Modal.__init__(self, title=f"Create Media Post")
        self.bot = bot
        self.post_type = PostType.MEDIA
        
        # Store attachment information and alt text
        self.attachment_url = attachment_url
        self.attachment_filename = attachment_filename
        self.attachment_content_type = attachment_content_type
        self.command_alt_text = alt_text  # Alt text from command parameter
        
        # Always add core fields (4 fields: Title, Content, Media URL, Custom Slug)
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
        
        # Media URL field (3rd field)
        if attachment_url:
            self.media_url_input = discord.ui.TextInput(
                label="Media URL",
                placeholder=f"Using uploaded file: {attachment_filename or 'file'}",
                default=attachment_url,
                max_length=500,
                required=False
            )
        else:
            self.media_url_input = discord.ui.TextInput(
                label="Media URL",
                placeholder="https://example.com/image.jpg",
                max_length=500,
                required=False
            )
        self.add_item(self.media_url_input)
        
        # Always include slug field (4th field) - no more conditional logic
        self.slug_input = discord.ui.TextInput(
            label="Custom Slug (optional)",
            placeholder="Leave blank to auto-generate from title",
            max_length=80,
            required=False
        )
        self.add_item(self.slug_input)
        
        # No alt_text_input field - alt text only via command parameter
        # No tags_input field - omitted due to Discord's 5-field limit
        self.alt_text_input = None
        self.tags_input = None
    
    async def _add_type_specific_data(self, post_data: PostData):
        """Add media-specific data to post with validation."""
        # Use attachment URL if available, otherwise use manual URL input
        media_url = self.attachment_url or self.media_url_input.value
        
        if not media_url:
            raise ValueError("Media posts require either an uploaded file or a media URL. Please upload a file using `/post media [attach file]` or provide a URL.")
        
        post_data.media_url = media_url.strip()
        
        # Add alt text only if provided via command parameter
        if self.command_alt_text:
            post_data.media_alt = self.command_alt_text.strip()
        # No fallback to modal alt text - simplified approach
        
        # Add slug if available from modal input
        if self.slug_input and self.slug_input.value:
            post_data.slug = self.slug_input.value.strip()
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission for media posts with custom field handling."""
        try:
            # Build post data with available fields
            post_data = PostData(
                title=self.title_input.value.strip(),
                content=self.content_input.value.strip(),
                post_type=self.post_type,
                tags=None,  # MediaModal doesn't include tags due to field limit
                slug=self.slug_input.value.strip() if self.slug_input and self.slug_input.value else None,
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
            logger.error(f"Error in media modal submission: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Error creating post: {str(e)}", 
                    ephemeral=True
                )


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
@app_commands.describe(
    post_type="Type of post to create",
    response_type="Type of response (only for response posts)",
    attachment="Upload a file for media posts (optional)",
    alt_text="Alt text for accessibility (media posts only)"
)
@app_commands.choices(
    post_type=[
        app_commands.Choice(name="note", value="note"),
        app_commands.Choice(name="response", value="response"),
        app_commands.Choice(name="bookmark", value="bookmark"),
        app_commands.Choice(name="media", value="media"),
    ],
    response_type=[
        app_commands.Choice(name="reply", value="reply"),
        app_commands.Choice(name="repost", value="reshare"),
        app_commands.Choice(name="like", value="star"),
    ]
)
async def post_command(
    interaction: discord.Interaction, 
    post_type: str, 
    response_type: str = "reply",
    attachment: Optional[discord.Attachment] = None,
    alt_text: Optional[str] = None
):
    """Main post command handler with optional file attachment support."""
    bot = interaction.client
    
    # Debug logging for attachment
    if attachment:
        logger.info(f"Attachment received: {attachment.filename}, URL: {attachment.url}, Type: {attachment.content_type}")
    else:
        logger.info("No attachment provided")
    
    # Check authorization
    if not bot.is_authorized(interaction.user.id):
        await interaction.response.send_message(
            "❌ You are not authorized to use this bot.", 
            ephemeral=True
        )
        return

    # Validate attachment usage - only allow attachments for media posts
    if attachment and post_type != "media":
        await interaction.response.send_message(
            "❌ File attachments are only supported for media posts. Use `/post media` with your file.",
            ephemeral=True
        )
        return
    
    # For media posts with attachment, validate file type
    if post_type == "media" and attachment:
        if not attachment.content_type or not attachment.content_type.startswith(('image/', 'video/', 'audio/')):
            await interaction.response.send_message(
                f"❌ Unsupported file type: {attachment.content_type or 'unknown'}. Please upload an image, video, or audio file.",
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
        
        # Create modal with appropriate parameters
        if post_type_enum == PostType.RESPONSE:
            modal = modal_class(bot, response_type)
        elif post_type_enum == PostType.MEDIA and attachment:
            # Pass attachment information and alt_text to MediaModal
            modal = modal_class(
                bot, 
                attachment_url=attachment.url,
                attachment_filename=attachment.filename,
                attachment_content_type=attachment.content_type,
                alt_text=alt_text
            )
        elif post_type_enum == PostType.MEDIA:
            # Pass alt_text to MediaModal even without attachment
            modal = modal_class(bot, alt_text=alt_text)
        else:
            modal = modal_class(bot)
            
        await interaction.response.send_modal(modal)

        logger.info(f"User {interaction.user.id} opened {post_type} modal")

    except Exception as e:
        logger.error(f"Error in post command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while processing your request.", 
            ephemeral=True
        )
