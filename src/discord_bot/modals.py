"""
Discord modal implementations for different post types.

Based on Technical Specification v1.0 - Modal Dialog Implementations
"""

import logging
from typing import Optional

import discord
from discord import ui

from .api_client import PublishingAPIClient

logger = logging.getLogger(__name__)


class BasePostModal(ui.Modal):
    """Base class for all post modals with common functionality."""

    def __init__(self, api_client: PublishingAPIClient, title: str):
        super().__init__(title=title)
        self.api_client = api_client

    async def send_to_api(self, interaction: discord.Interaction, message: str) -> None:
        """Send formatted message to publishing API."""
        try:
            # Defer response to avoid timeout
            await interaction.response.defer(ephemeral=True)

            # Make API call
            success, response = await self.api_client.publish_post(
                message=message, user_id=str(interaction.user.id)
            )

            if success:
                filepath = response.get("filepath", "unknown")
                site_url = response.get("site_url")

                success_msg = f"✅ Post published successfully!\n📁 File: `{filepath}`"
                if site_url:
                    success_msg += f"\n🔗 View: {site_url}"

                await interaction.followup.send(success_msg, ephemeral=True)
                logger.info(
                    f"Successfully published {self.title.lower()} for user {interaction.user.id}"
                )

            else:
                error_msg = response.get("error", "Unknown error occurred")
                await interaction.followup.send(
                    f"❌ Failed to publish post:\n{error_msg}", ephemeral=True
                )
                logger.error(f"Failed to publish {self.title.lower()}: {error_msg}")

        except Exception as e:
            logger.error(f"Error in send_to_api: {e}")
            try:
                await interaction.followup.send(
                    "❌ An unexpected error occurred while publishing your post.",
                    ephemeral=True,
                )
            except:
                pass  # If even the error message fails, log and move on


class NoteModal(BasePostModal, title="Create Note Post"):
    """Modal for creating note posts."""

    def __init__(self, api_client: PublishingAPIClient):
        super().__init__(api_client, "Create Note Post")

    content = ui.TextInput(
        label="Content (Markdown)",
        style=discord.TextStyle.paragraph,
        placeholder="Enter your note content using markdown formatting...",
        required=True,
        max_length=2000,
    )

    title = ui.TextInput(
        label="Title (Optional)",
        style=discord.TextStyle.short,
        placeholder="Auto-generated from content if not provided",
        required=False,
        max_length=100,
    )

    tags = ui.TextInput(
        label="Tags (Optional)",
        style=discord.TextStyle.short,
        placeholder="Comma-separated tags: development, thoughts, project",
        required=False,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle note modal submission."""
        # Build frontmatter
        frontmatter_lines = []
        if self.title.value.strip():
            frontmatter_lines.append(f"title: {self.title.value.strip()}")

        if self.tags.value.strip():
            # Parse tags and format as YAML array
            tags = [tag.strip() for tag in self.tags.value.split(",") if tag.strip()]
            if tags:
                tags_yaml = ", ".join(f'"{tag}"' for tag in tags)
                frontmatter_lines.append(f"tags: [{tags_yaml}]")

        # Format message
        message_parts = ["/post note"]

        if frontmatter_lines:
            message_parts.extend(["---", *frontmatter_lines, "---"])

        message_parts.append(self.content.value.strip())

        message = "\n".join(message_parts)
        await self.send_to_api(interaction, message)


class ResponseModal(BasePostModal, title="Create Response Post"):
    """Modal for creating response posts."""

    def __init__(self, api_client: PublishingAPIClient):
        super().__init__(api_client, "Create Response Post")

    response_type = ui.TextInput(
        label="Response Type",
        style=discord.TextStyle.short,
        placeholder="reply, like, or reshare",
        required=True,
        max_length=20,
    )

    content = ui.TextInput(
        label="Response Content",
        style=discord.TextStyle.paragraph,
        placeholder="Your response or comment...",
        required=True,
        max_length=2000,
    )

    original_url = ui.TextInput(
        label="Original URL (Optional)",
        style=discord.TextStyle.short,
        placeholder="https://example.com/original-post",
        required=False,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle response modal submission."""
        # Validate response type
        valid_types = ["reply", "like", "reshare"]
        resp_type = self.response_type.value.strip().lower()

        if resp_type not in valid_types:
            await interaction.response.send_message(
                f"❌ Invalid response type. Must be one of: {', '.join(valid_types)}",
                ephemeral=True,
            )
            return

        # Build frontmatter
        frontmatter_lines = [f"response_type: {resp_type}"]

        if self.original_url.value.strip():
            frontmatter_lines.append(f"in_reply_to: {self.original_url.value.strip()}")

        # Format message
        message = "\n".join(
            [
                "/post response",
                "---",
                *frontmatter_lines,
                "---",
                self.content.value.strip(),
            ]
        )

        await self.send_to_api(interaction, message)


class BookmarkModal(BasePostModal, title="Create Bookmark Post"):
    """Modal for creating bookmark posts."""

    def __init__(self, api_client: PublishingAPIClient):
        super().__init__(api_client, "Create Bookmark Post")

    url = ui.TextInput(
        label="URL",
        style=discord.TextStyle.short,
        placeholder="https://example.com/article-to-bookmark",
        required=True,
        max_length=500,
    )

    title = ui.TextInput(
        label="Title (Optional)",
        style=discord.TextStyle.short,
        placeholder="Custom title for the bookmark",
        required=False,
        max_length=200,
    )

    notes = ui.TextInput(
        label="Notes (Optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Your thoughts about this bookmark...",
        required=False,
        max_length=1000,
    )

    tags = ui.TextInput(
        label="Tags (Optional)",
        style=discord.TextStyle.short,
        placeholder="Comma-separated tags: web, development, tools",
        required=False,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle bookmark modal submission."""
        # Basic URL validation
        url = self.url.value.strip()
        if not url.startswith(("http://", "https://")):
            await interaction.response.send_message(
                "❌ Please provide a valid URL starting with http:// or https://",
                ephemeral=True,
            )
            return

        # Build frontmatter
        frontmatter_lines = [f"url: {url}"]

        if self.title.value.strip():
            frontmatter_lines.append(f"title: {self.title.value.strip()}")

        if self.tags.value.strip():
            tags = [tag.strip() for tag in self.tags.value.split(",") if tag.strip()]
            if tags:
                tags_yaml = ", ".join(f'"{tag}"' for tag in tags)
                frontmatter_lines.append(f"tags: [{tags_yaml}]")

        # Format message
        message_parts = ["/post bookmark", "---", *frontmatter_lines, "---"]

        # Add notes if provided
        if self.notes.value.strip():
            message_parts.append(self.notes.value.strip())
        else:
            message_parts.append("")  # Empty content is allowed for bookmarks

        message = "\n".join(message_parts)
        await self.send_to_api(interaction, message)


class MediaModal(BasePostModal, title="Create Media Post"):
    """Modal for creating media posts."""

    def __init__(self, api_client: PublishingAPIClient):
        super().__init__(api_client, "Create Media Post")

    media_url = ui.TextInput(
        label="Media URL",
        style=discord.TextStyle.short,
        placeholder="https://example.com/image.jpg or attachment URL",
        required=True,
        max_length=500,
    )

    caption = ui.TextInput(
        label="Caption/Description",
        style=discord.TextStyle.paragraph,
        placeholder="Caption or description for the media...",
        required=True,
        max_length=1000,
    )

    alt_text = ui.TextInput(
        label="Alt Text (Optional)",
        style=discord.TextStyle.short,
        placeholder="Alternative text for accessibility",
        required=False,
        max_length=200,
    )

    tags = ui.TextInput(
        label="Tags (Optional)",
        style=discord.TextStyle.short,
        placeholder="Comma-separated tags: photo, screenshot, diagram",
        required=False,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle media modal submission."""
        # Build frontmatter
        frontmatter_lines = [f"media_url: {self.media_url.value.strip()}"]

        if self.alt_text.value.strip():
            frontmatter_lines.append(f"alt_text: {self.alt_text.value.strip()}")

        if self.tags.value.strip():
            tags = [tag.strip() for tag in self.tags.value.split(",") if tag.strip()]
            if tags:
                tags_yaml = ", ".join(f'"{tag}"' for tag in tags)
                frontmatter_lines.append(f"tags: [{tags_yaml}]")

        # Format message
        message = "\n".join(
            [
                "/post media",
                "---",
                *frontmatter_lines,
                "---",
                self.caption.value.strip(),
            ]
        )

        await self.send_to_api(interaction, message)
