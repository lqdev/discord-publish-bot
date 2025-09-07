"""
Discord interactions handler for HTTP webhooks (serverless deployment).

Handles Discord interactions via HTTP webhooks instead of WebSocket gateway.
This enables serverless deployment with scale-to-zero capabilities.
"""

import logging
import os
from typing import Dict, Any, Optional
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from ..config import AppSettings
from ..shared import (
    DiscordSignatureError,
    DiscordCommandError,
    DiscordModalError,
    PostType,
    PostData
)

logger = logging.getLogger(__name__)


class InteractionType:
    """Discord interaction types."""
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class InteractionResponseType:
    """Discord interaction response types."""
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9


class ComponentType:
    """Discord component types."""
    ACTION_ROW = 1
    BUTTON = 2
    SELECT_MENU = 3
    TEXT_INPUT = 4


class DiscordInteractionsHandler:
    """
    Discord interactions handler for HTTP webhooks.
    
    Processes Discord interactions without maintaining persistent connections,
    suitable for serverless environments.
    """
    
    def __init__(self, settings: AppSettings):
        """
        Initialize interactions handler.
        
        Args:
            settings: Application configuration settings
        """
        self.settings = settings
        
        if not settings.discord.public_key:
            raise ValueError("Discord public key is required for HTTP interactions")
        
        self.verify_key = VerifyKey(bytes.fromhex(settings.discord.public_key))
        logger.info("Initialized Discord interactions handler")
    
    def verify_signature(self, signature: str, timestamp: str, body: bytes) -> bool:
        """
        Verify Discord request signature for security.
        
        Args:
            signature: X-Signature-Ed25519 header
            timestamp: X-Signature-Timestamp header
            body: Raw request body
            
        Returns:
            True if signature is valid
            
        Raises:
            DiscordSignatureError: If signature verification fails
        """
        try:
            message = f"{timestamp}{body.decode('utf-8')}"
            self.verify_key.verify(message.encode(), bytes.fromhex(signature))
            return True
        except BadSignatureError as e:
            logger.error(f"Discord signature verification failed: {e}")
            raise DiscordSignatureError("Invalid Discord signature")
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            raise DiscordSignatureError(f"Signature verification error: {e}")
    
    async def handle_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming Discord interaction.
        
        Args:
            interaction: Discord interaction payload
            
        Returns:
            Discord interaction response
            
        Raises:
            DiscordCommandError: If command processing fails
        """
        try:
            interaction_type = interaction.get("type")
            
            if interaction_type == InteractionType.PING:
                logger.debug("Handling ping interaction")
                return {"type": InteractionResponseType.PONG}
            
            if interaction_type == InteractionType.APPLICATION_COMMAND:
                return await self._handle_application_command(interaction)
            
            if interaction_type == InteractionType.MODAL_SUBMIT:
                return self._handle_modal_submit(interaction)
            
            # Unknown interaction type
            logger.warning(f"Unknown interaction type: {interaction_type}")
            return {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": "Unknown interaction type",
                    "flags": 64  # Ephemeral
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling interaction: {e}")
            raise DiscordCommandError(f"Failed to handle interaction: {e}")
    
    async def _handle_application_command(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Handle slash command interactions."""
        try:
            command_name = interaction["data"]["name"]
            user_id = self._extract_user_id(interaction)
            
            logger.info(f"Processing command {command_name} from user {user_id}")
            
            # Authorization check
            if user_id != self.settings.discord.authorized_user_id:
                logger.warning(f"Unauthorized user {user_id} attempted to use command {command_name}")
                return {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": "❌ You are not authorized to use this bot.",
                        "flags": 64  # Ephemeral
                    }
                }
            
            if command_name == "ping":
                return self._handle_ping_command()
            
            if command_name == "post":
                return await self._handle_post_command(interaction)
            
            logger.warning(f"Unknown command: {command_name}")
            return {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": f"Unknown command: {command_name}",
                    "flags": 64  # Ephemeral
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling application command: {e}")
            raise DiscordCommandError(f"Failed to handle command: {e}")
    
    def _handle_ping_command(self) -> Dict[str, Any]:
        """Handle ping slash command."""
        return {
            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": "🏓 Pong! Discord bot is running via HTTP interactions.",
                "flags": 64  # Ephemeral
            }
        }
    
    async def _handle_post_command(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Handle post slash command - show modal for post creation."""
        try:
            # Get post type, response type, attachment, and alt_text from command options
            post_type = PostType.NOTE  # Default
            response_type = "reply"    # Default
            attachment = None          # Attachment data
            alt_text = None           # Alt text parameter
            
            if "options" in interaction["data"]:
                for option in interaction["data"]["options"]:
                    if option["name"] == "post_type":
                        try:
                            post_type = PostType(option["value"])
                        except ValueError:
                            logger.warning(f"Invalid post type: {option['value']}")
                    elif option["name"] == "response_type":
                        response_type = option["value"]
                    elif option["name"] == "alt_text":
                        alt_text = option.get("value", "").strip()
                        logger.info(f"Alt text parameter received: {alt_text}")
                    elif option["name"] == "attachment":
                        attachment_id = option.get("value")  # Discord sends attachment ID in value
                        logger.info(f"Attachment ID received: {attachment_id}")
                        
                        # Get attachment details from resolved data
                        resolved = interaction["data"].get("resolved", {})
                        attachments = resolved.get("attachments", {})
                        if attachment_id and attachment_id in attachments:
                            attachment = attachments[attachment_id]
                            logger.info(f"Attachment details: filename={attachment.get('filename')}, url={attachment.get('url')}, type={attachment.get('content_type')}")
                        else:
                            logger.warning(f"Attachment {attachment_id} not found in resolved data")
                            attachment = None
            
            # Debug logging for attachment processing
            if attachment:
                logger.info("Attachment processing completed successfully")
            else:
                logger.info("No attachment provided")
            
            # Validate attachment usage - only allow attachments for media posts
            if attachment and post_type != PostType.MEDIA:
                return {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": "❌ File attachments are only supported for media posts. Use `/post media` with your file.",
                        "flags": 64  # Ephemeral
                    }
                }
            
            # For media posts with attachment, validate file type
            if post_type == PostType.MEDIA and attachment:
                content_type = attachment.get("content_type")
                if not content_type or not content_type.startswith(('image/', 'video/', 'audio/')):
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {
                            "content": f"❌ Unsupported file type: {content_type or 'unknown'}. Please upload an image, video, or audio file.",
                            "flags": 64  # Ephemeral
                        }
                    }
                
                # Note: Azure Storage upload will happen during PR creation, not here
                # This keeps the modal response fast and within Discord's 3-second timeout
                logger.info(f"Media attachment detected: {attachment.get('filename')}, will upload to Azure during PR creation")
            
            modal = self._create_post_modal(post_type, response_type, attachment_data=attachment, alt_text=alt_text)
            
            return {
                "type": InteractionResponseType.MODAL,
                "data": modal
            }
            
        except Exception as e:
            logger.error(f"Error handling post command: {e}")
            raise DiscordCommandError(f"Failed to handle post command: {e}")
    
    def _create_post_modal(self, post_type: PostType, response_type: str = "reply", attachment_data=None, alt_text=None) -> Dict[str, Any]:
        """Create modal for post creation based on type."""
        # Include response_type in custom_id for response posts
        if post_type == PostType.RESPONSE:
            custom_id = f"post_modal_{post_type.value}_{response_type}"
        else:
            custom_id = f"post_modal_{post_type.value}"
            
        # Note: alt_text parameter handling is primarily supported in WebSocket bot
        # HTTP interactions have limitations for passing command parameters through modals
            
        modal = {
            "custom_id": custom_id,
            "title": f"Create {post_type.value.title()} Post",
            "components": []
        }
        
        # Common fields for all post types
        components = [
            {
                "type": ComponentType.ACTION_ROW,
                "components": [{
                    "type": ComponentType.TEXT_INPUT,
                    "custom_id": "title",
                    "label": "Title",
                    "style": 1,  # Short
                    "placeholder": "Enter post title...",
                    "required": True,
                    "max_length": 200
                }]
            },
            {
                "type": ComponentType.ACTION_ROW,
                "components": [{
                    "type": ComponentType.TEXT_INPUT,
                    "custom_id": "content",
                    "label": "Content",
                    "style": 2,  # Paragraph
                    "placeholder": "Enter post content...",
                    "required": True,
                    "max_length": 4000
                }]
            },
            {
                "type": ComponentType.ACTION_ROW,
                "components": [{
                    "type": ComponentType.TEXT_INPUT,
                    "custom_id": "tags",
                    "label": "Tags (comma-separated)",
                    "style": 1,  # Short
                    "placeholder": "tag1, tag2, tag3",
                    "required": False,
                    "max_length": 200
                }]
            },
            {
                "type": ComponentType.ACTION_ROW,
                "components": [{
                    "type": ComponentType.TEXT_INPUT,
                    "custom_id": "slug",
                    "label": "Custom Slug (optional)",
                    "style": 1,  # Short
                    "placeholder": "Leave blank to auto-generate from title",
                    "required": False,
                    "max_length": 80
                }]
            }
        ]
        
        # Type-specific fields
        if post_type == PostType.RESPONSE:
            components.append({
                "type": ComponentType.ACTION_ROW,
                "components": [{
                    "type": ComponentType.TEXT_INPUT,
                    "custom_id": "target_url",
                    "label": "Target URL",
                    "style": 1,  # Short
                    "placeholder": "https://example.com/original-post",
                    "required": True,
                    "max_length": 500
                }]
            })
        
        elif post_type == PostType.BOOKMARK:
            components.append({
                "type": ComponentType.ACTION_ROW,
                "components": [{
                    "type": ComponentType.TEXT_INPUT,
                    "custom_id": "target_url",
                    "label": "Bookmark URL",
                    "style": 1,  # Short
                    "placeholder": "https://example.com/article",
                    "required": True,
                    "max_length": 500
                }]
            })
        
        elif post_type == PostType.MEDIA:
            # Handle attachment data for media posts
            if attachment_data:
                attachment_url = attachment_data.get("url")
                attachment_filename = attachment_data.get("filename", "file")
                
                components.append({
                    "type": ComponentType.ACTION_ROW,
                    "components": [{
                        "type": ComponentType.TEXT_INPUT,
                        "custom_id": "media_url",
                        "label": "Media URL",
                        "style": 1,  # Short
                        "placeholder": f"Using uploaded file: {attachment_filename}",
                        "value": attachment_url,  # Pre-fill with attachment URL
                        "required": False,
                        "max_length": 500
                    }]
                })
            else:
                # Standard URL input when no attachment
                components.append({
                    "type": ComponentType.ACTION_ROW,
                    "components": [{
                        "type": ComponentType.TEXT_INPUT,
                        "custom_id": "media_url",
                        "label": "Media URL",
                        "style": 1,  # Short
                        "placeholder": "https://example.com/image.jpg",
                        "required": False,
                        "max_length": 500
                    }]
                })
            
            # Note: Alt text is now handled via command parameter only (Phase 2 simplification)
            # Modal consistently shows: Title, Content, Tags, Custom Slug, Media URL (5 fields)
        
        modal["components"] = components
        return modal
    
    def _handle_modal_submit(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Handle modal submission for post creation."""
        try:
            custom_id = interaction["data"]["custom_id"]
            user_id = self._extract_user_id(interaction)
            
            logger.info(f"Processing modal submission {custom_id} from user {user_id}")
            
            # Authorization check
            if user_id != self.settings.discord.authorized_user_id:
                logger.warning(f"Unauthorized user {user_id} attempted modal submission")
                return {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": "❌ You are not authorized to use this bot.",
                        "flags": 64  # Ephemeral
                    }
                }
            
            # Extract post type from custom_id
            if not custom_id.startswith("post_modal_"):
                raise DiscordModalError("Invalid modal custom_id", modal_id=custom_id)
            
            # Extract post type and response type from custom_id
            custom_id_parts = custom_id.replace("post_modal_", "").split("_")
            post_type_str = custom_id_parts[0]
            try:
                post_type = PostType(post_type_str)
            except ValueError:
                raise DiscordModalError(f"Invalid post type: {post_type_str}", modal_id=custom_id)
            
            # Extract form data
            form_data = self._extract_modal_data(interaction["data"]["components"])
            
            # Defer response while processing
            return {
                "type": InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "flags": 64  # Ephemeral
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling modal submit: {e}")
            raise DiscordModalError(f"Failed to handle modal submission: {e}")
    
    def extract_post_data_from_modal(self, interaction: Dict[str, Any]) -> PostData:
        """
        Extract PostData from modal submission interaction.
        
        Args:
            interaction: Modal submission interaction
            
        Returns:
            Structured post data
            
        Raises:
            DiscordModalError: If data extraction fails
        """
        try:
            custom_id = interaction["data"]["custom_id"]
            user_id = self._extract_user_id(interaction)
            
            # Import required utilities at the beginning
            from ..shared.utils import parse_tags
            from ..shared.types import ResponseType
            
            # Extract post type and response type from custom_id
            custom_id_parts = custom_id.replace("post_modal_", "").split("_")
            post_type_str = custom_id_parts[0]
            post_type = PostType(post_type_str)
            
            # Extract response type for response posts
            response_type = None
            if post_type == PostType.RESPONSE and len(custom_id_parts) > 1:
                response_type_str = custom_id_parts[1]
                try:
                    response_type = ResponseType(response_type_str)
                except ValueError:
                    response_type = ResponseType.REPLY  # Default fallback
            
            # Extract form data
            form_data = self._extract_modal_data(interaction["data"]["components"])
            
            return PostData(
                title=form_data.get("title", "").strip(),
                content=form_data.get("content", "").strip(),
                post_type=post_type,
                tags=parse_tags(form_data.get("tags", "")),
                slug=form_data.get("slug", "").strip() or None,  # Custom slug field from modal
                target_url=form_data.get("target_url", "").strip() or None,
                response_type=response_type,
                media_url=form_data.get("media_url", "").strip() or None,
                media_alt=None,  # Alt text via command parameter not supported in HTTP interactions yet
                created_by=user_id
            )
            
        except Exception as e:
            logger.error(f"Error extracting post data from modal: {e}")
            raise DiscordModalError(f"Failed to extract post data: {e}")
    
    def _extract_modal_data(self, components: list) -> Dict[str, str]:
        """Extract data from modal components."""
        return extract_component_data(components)
    
    def _extract_user_id(self, interaction: Dict[str, Any]) -> str:
        """Extract user ID from interaction."""
        # Try different possible locations for user ID
        if "member" in interaction and "user" in interaction["member"]:
            return interaction["member"]["user"]["id"]
        elif "user" in interaction:
            return interaction["user"]["id"]
        else:
            raise DiscordCommandError("Could not extract user ID from interaction")


def extract_component_data(components: list) -> Dict[str, str]:
    """Extract data from Discord modal components."""
    data = {}
    
    for action_row in components:
        for component in action_row["components"]:
            if component["type"] == ComponentType.TEXT_INPUT:
                custom_id = component["custom_id"]
                value = component.get("value", "")
                data[custom_id] = value
    
    return data


def extract_component_value(components: list, field_name: str) -> Optional[str]:
    """Extract a specific field value from Discord modal components."""
    data = extract_component_data(components)
    return data.get(field_name)
