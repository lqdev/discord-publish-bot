"""
Unit tests for Discord interactions functionality.

Tests the Discord interactions module in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from discord_publish_bot.discord.interactions import DiscordInteractionsHandler
from discord_publish_bot.shared import PostType, PostData


@pytest.mark.unit
class TestDiscordInteractions:
    """Test Discord interactions functionality."""
    
    def test_import_structure(self):
        """Test that all Discord modules can be imported."""
        # Test imports - if this runs, imports work
        from discord_publish_bot.discord import DiscordInteractionsHandler
        from discord_publish_bot.config import AppSettings
        from discord_publish_bot.shared import PostType, PostData
        
        assert DiscordInteractionsHandler is not None
        assert PostType is not None
        assert PostData is not None
    
    def test_discord_bot_initialization(self, test_settings):
        """Test Discord bot can be initialized with settings."""
        bot = DiscordInteractionsHandler(test_settings)
        
        assert bot.settings == test_settings
        assert hasattr(bot, 'verify_signature')
        assert hasattr(bot, 'handle_interaction')
    
    @pytest.mark.asyncio
    async def test_ping_interaction(self, mock_discord_bot, discord_interaction_payloads):
        """Test handling of Discord ping interactions."""
        ping_payload = discord_interaction_payloads["ping"]
        
        response = mock_discord_bot.handle_interaction(ping_payload)
        
        assert response["type"] == 1  # PONG response type
    
    @pytest.mark.asyncio
    async def test_slash_command_interaction(self, mock_discord_bot, discord_interaction_payloads):
        """Test handling of slash command interactions."""
        command_payload = discord_interaction_payloads["slash_command"]
        
        with patch.object(mock_discord_bot, '_create_post_modal') as mock_modal:
            mock_modal.return_value = {
                "type": 9,  # MODAL response type
                "data": {"custom_id": "post_modal_note", "title": "Create Note"}
            }
            
            response = mock_discord_bot.handle_interaction(command_payload)
            
            assert response["type"] == 9  # MODAL response
            mock_modal.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_modal_submit_interaction(self, mock_discord_bot, discord_interaction_payloads, mock_github_client):
        """Test handling of modal submit interactions."""
        modal_payload = discord_interaction_payloads["modal_submit"]
        
        with patch.object(mock_discord_bot, 'publishing_service') as mock_service:
            mock_service.publish_post.return_value = Mock(
                success=True,
                message="Post published successfully",
                site_url="https://test.example.com/posts/test-post"
            )
            
            response = mock_discord_bot.handle_interaction(modal_payload)
            
            assert response["type"] == 4  # CHANNEL_MESSAGE_WITH_SOURCE
            assert "successfully" in response["data"]["content"]
    
    def test_signature_verification(self, mock_discord_bot):
        """Test Discord signature verification logic."""
        # Mock signature verification since we don't have real Discord keys
        test_signature = "test_signature"
        test_timestamp = "1234567890"
        test_body = b'{"type": 1}'
        
        with patch('discord_publish_bot.discord.interactions.verify_signature') as mock_verify:
            mock_verify.return_value = True
            
            result = mock_discord_bot.verify_signature(test_signature, test_timestamp, test_body)
            
            assert result is True
            mock_verify.assert_called_once()
    
    def test_post_type_validation(self, mock_discord_bot):
        """Test that post type validation works correctly."""
        valid_types = ["note", "response", "bookmark", "media"]
        
        for post_type in valid_types:
            # This should not raise an exception
            try:
                PostType(post_type)
                is_valid = True
            except ValueError:
                is_valid = False
            
            assert is_valid, f"Post type '{post_type}' should be valid"
    
    def test_modal_creation(self, mock_discord_bot):
        """Test modal creation for different post types."""
        post_types = ["note", "response", "bookmark", "media"]
        
        for post_type in post_types:
            modal = mock_discord_bot._create_post_modal(post_type)
            
            assert modal["type"] == 9  # MODAL type
            assert "custom_id" in modal["data"]
            assert "title" in modal["data"]
            assert "components" in modal["data"]
            
            # Check that modal has required components
            components = modal["data"]["components"]
            assert len(components) >= 2  # At least title and content fields
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_discord_bot, discord_interaction_payloads):
        """Test error handling in interaction processing."""
        invalid_payload = {"type": 999}  # Invalid interaction type
        
        response = mock_discord_bot.handle_interaction(invalid_payload)
        
        assert response["type"] == 4  # CHANNEL_MESSAGE_WITH_SOURCE
        assert "error" in response["data"]["content"].lower()
    
    def test_post_data_creation(self, mock_discord_bot):
        """Test creation of PostData from Discord modal submission."""
        modal_data = {
            "custom_id": "post_modal_note",
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 4,
                            "custom_id": "title",
                            "value": "Test Post Title"
                        }
                    ]
                },
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 4,
                            "custom_id": "content", 
                            "value": "Test post content here"
                        }
                    ]
                },
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 4,
                            "custom_id": "tags",
                            "value": "test, unit-test"
                        }
                    ]
                }
            ]
        }
        
        post_data = mock_discord_bot._extract_post_data_from_modal(modal_data)
        
        assert post_data.title == "Test Post Title"
        assert post_data.content == "Test post content here"
        assert post_data.post_type == PostType.NOTE
        assert "test" in post_data.tags
        assert "unit-test" in post_data.tags


@pytest.mark.unit
class TestDiscordUtilities:
    """Test Discord utility functions."""
    
    def test_component_value_extraction(self):
        """Test extraction of values from Discord components."""
        from discord_publish_bot.discord.interactions import extract_component_value
        
        components = [
            {
                "type": 1,
                "components": [
                    {
                        "type": 4,
                        "custom_id": "test_field",
                        "value": "test_value"
                    }
                ]
            }
        ]
        
        value = extract_component_value(components, "test_field")
        assert value == "test_value"
        
        # Test missing field
        missing_value = extract_component_value(components, "missing_field")
        assert missing_value is None
    
    def test_tag_parsing(self):
        """Test parsing of tags from string input."""
        from discord_publish_bot.shared.utils import parse_tags
        
        test_cases = [
            ("tag1, tag2, tag3", ["tag1", "tag2", "tag3"]),
            ("tag1,tag2,tag3", ["tag1", "tag2", "tag3"]),  # No spaces
            ("tag1; tag2; tag3", ["tag1", "tag2", "tag3"]),  # Semicolon separator
            ("single-tag", ["single-tag"]),  # Single tag
            ("", []),  # Empty string
            ("tag with spaces, another tag", ["tag with spaces", "another tag"]),
        ]
        
        for input_tags, expected in test_cases:
            result = parse_tags(input_tags)
            assert result == expected, f"Failed for input: '{input_tags}'"
    
    def test_content_sanitization(self):
        """Test content sanitization for Discord messages."""
        from discord_publish_bot.shared.utils import sanitize_content
        
        test_cases = [
            ("Normal content", "Normal content"),
            ("Content with <script>alert('xss')</script>", "Content with alert('xss')"),
            ("Content with @everyone", "Content with @everyone"),  # Should be preserved in posts
            ("Content with\nmultiple\nlines", "Content with\nmultiple\nlines"),
        ]
        
        for input_content, expected in test_cases:
            result = sanitize_content(input_content)
            assert expected in result, f"Failed for input: '{input_content}'"
