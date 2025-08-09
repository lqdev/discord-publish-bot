"""
Discord HTTP Interactions Bot

Handles Discord interactions via HTTP webhooks instead of WebSocket gateway.
This enables serverless deployment with scale-to-zero capabilities on Azure Container Apps.
"""

import logging
import json
from typing import Dict, Any, Optional
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from fastapi import HTTPException

from .config import DiscordConfig


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


class DiscordInteractionsBot:
    """
    Discord bot that handles interactions via HTTP webhooks.
    
    This replaces the WebSocket-based bot for serverless deployment.
    """
    
    def __init__(self, config: DiscordConfig):
        self.config = config
        self.verify_key = VerifyKey(bytes.fromhex(config.public_key))
        self.logger = logging.getLogger(__name__)
    
    def verify_signature(self, signature: str, timestamp: str, body: bytes) -> bool:
        """
        Verify Discord request signature for security.
        
        Args:
            signature: X-Signature-Ed25519 header
            timestamp: X-Signature-Timestamp header
            body: Raw request body
            
        Returns:
            True if signature is valid
        """
        try:
            self.verify_key.verify(
                f"{timestamp}{body.decode('utf-8')}".encode(),
                bytes.fromhex(signature)
            )
            return True
        except BadSignatureError:
            return False
    
    def handle_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming Discord interaction.
        
        Args:
            interaction: Discord interaction payload
            
        Returns:
            Discord interaction response
        """
        interaction_type = interaction.get("type")
        
        if interaction_type == InteractionType.PING:
            return {"type": InteractionResponseType.PONG}
        
        if interaction_type == InteractionType.APPLICATION_COMMAND:
            return self._handle_application_command(interaction)
        
        if interaction_type == InteractionType.MODAL_SUBMIT:
            return self._handle_modal_submit(interaction)
        
        # Unknown interaction type
        return {
            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": "Unknown interaction type",
                "flags": 64  # Ephemeral
            }
        }
    
    def _handle_application_command(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Handle slash command interactions."""
        command_name = interaction["data"]["name"]
        user_id = interaction["member"]["user"]["id"]
        
        # Authorization check
        if user_id != self.config.authorized_user_id:
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
            return self._handle_post_command(interaction)
        
        return {
            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": f"Unknown command: {command_name}",
                "flags": 64  # Ephemeral
            }
        }
    
    def _handle_ping_command(self) -> Dict[str, Any]:
        """Handle ping slash command."""
        return {
            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "content": "🏓 Pong! Discord bot is running via HTTP interactions.",
                "flags": 64  # Ephemeral
            }
        }
    
    def _handle_post_command(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Handle post slash command - show modal for post creation."""
        # Get post type from command option
        post_type = "note"  # Default
        if "options" in interaction["data"]:
            for option in interaction["data"]["options"]:
                if option["name"] == "type":
                    post_type = option["value"]
                    break
        
        modal = self._create_post_modal(post_type)
        
        return {
            "type": InteractionResponseType.MODAL,
            "data": modal
        }
    
    def _create_post_modal(self, post_type: str) -> Dict[str, Any]:
        """Create modal for post creation based on type."""
        
        # Base modal structure
        modal = {
            "custom_id": f"post_modal_{post_type}",
            "title": f"Create {post_type.title()} Post",
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
            }
        ]
        
        # Type-specific fields
        if post_type == "response":
            components.append({
                "type": ComponentType.ACTION_ROW,
                "components": [{
                    "type": ComponentType.TEXT_INPUT,
                    "custom_id": "reply_to_url",
                    "label": "Reply to URL",
                    "style": 1,  # Short
                    "placeholder": "https://example.com/original-post",
                    "required": True,
                    "max_length": 500
                }]
            })
        
        elif post_type == "bookmark":
            components.append({
                "type": ComponentType.ACTION_ROW,
                "components": [{
                    "type": ComponentType.TEXT_INPUT,
                    "custom_id": "bookmark_url",
                    "label": "Bookmark URL",
                    "style": 1,  # Short
                    "placeholder": "https://example.com/article",
                    "required": True,
                    "max_length": 500
                }]
            })
        
        elif post_type == "media":
            components.append({
                "type": ComponentType.ACTION_ROW,
                "components": [{
                    "type": ComponentType.TEXT_INPUT,
                    "custom_id": "media_url",
                    "label": "Media URL",
                    "style": 1,  # Short
                    "placeholder": "https://example.com/image.jpg",
                    "required": True,
                    "max_length": 500
                }]
            })
        
        modal["components"] = components
        return modal
    
    def _handle_modal_submit(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Handle modal submission for post creation."""
        custom_id = interaction["data"]["custom_id"]
        user_id = interaction["member"]["user"]["id"]
        
        # Authorization check
        if user_id != self.config.authorized_user_id:
            return {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": "❌ You are not authorized to use this bot.",
                    "flags": 64  # Ephemeral
                }
            }
        
        # Extract post type from custom_id
        if not custom_id.startswith("post_modal_"):
            return {
                "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                "data": {
                    "content": "❌ Invalid modal submission.",
                    "flags": 64  # Ephemeral
                }
            }
        
        post_type = custom_id.replace("post_modal_", "")
        
        # Extract form data
        form_data = self._extract_modal_data(interaction["data"]["components"])
        
        # Defer response while processing
        return {
            "type": InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
            "data": {
                "flags": 64  # Ephemeral
            }
        }
    
    def _extract_modal_data(self, components: list) -> Dict[str, str]:
        """Extract data from modal components."""
        data = {}
        
        for action_row in components:
            for component in action_row["components"]:
                if component["type"] == ComponentType.TEXT_INPUT:
                    custom_id = component["custom_id"]
                    value = component.get("value", "")
                    data[custom_id] = value
        
        return data
