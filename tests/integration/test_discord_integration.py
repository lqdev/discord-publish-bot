"""
Integration tests for Discord integration functionality.

Tests Discord interactions with mocked Discord API but real application logic.
"""

import pytest
import json
from unittest.mock import AsyncMock, Mock, patch

from discord_publish_bot.discord.interactions import DiscordInteractionsHandler
from discord_publish_bot.shared import PostData, PostType


@pytest.mark.integration
class TestDiscordIntegration:
    """Test Discord integration with application components."""
    
    @pytest.fixture
    def discord_bot(self, test_settings, mock_github_client):
        """Create Discord bot with mocked dependencies."""
        with patch('discord_publish_bot.api.dependencies.get_github_client', return_value=mock_github_client):
            return DiscordInteractionsHandler(test_settings.discord)
    
    @pytest.mark.asyncio
    async def test_full_interaction_flow_note(self, discord_bot, discord_interaction_payloads):
        """Test complete interaction flow for creating a note."""
        # Step 1: Slash command interaction
        command_payload = discord_interaction_payloads["slash_command"]
        command_payload["data"]["options"] = [{"name": "type", "value": "note"}]
        
        response = await discord_bot.handle_interaction(command_payload)
        
        assert response["type"] == 9  # MODAL response
        assert "note" in response["data"]["custom_id"]
        
        # Step 2: Modal submission
        modal_payload = discord_interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = "post_modal_note"
        modal_payload["data"]["components"] = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": "Integration Test Note"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": "This is a note created through integration testing."
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "tags",
                    "value": "integration, testing"
                }]
            }
        ]
        
        with patch.object(discord_bot, 'publishing_service') as mock_service:
            mock_service.publish_post.return_value = Mock(
                success=True,
                message="Post published successfully",
                site_url="https://test.example.com/posts/integration-test-note"
            )
            
            response = await discord_bot.handle_interaction(modal_payload)
            
            assert response["type"] == 4  # CHANNEL_MESSAGE_WITH_SOURCE
            assert "successfully" in response["data"]["content"]
            assert "https://test.example.com" in response["data"]["content"]
    
    @pytest.mark.asyncio
    async def test_full_interaction_flow_response(self, discord_bot, discord_interaction_payloads):
        """Test complete interaction flow for creating a response post."""
        # Slash command for response
        command_payload = discord_interaction_payloads["slash_command"]
        command_payload["data"]["options"] = [{"name": "type", "value": "response"}]
        
        response = await discord_bot.handle_interaction(command_payload)
        
        assert response["type"] == 9  # MODAL response
        assert "response" in response["data"]["custom_id"]
        
        # Modal submission with target URL
        modal_payload = discord_interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = "post_modal_response"
        modal_payload["data"]["components"] = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": "Re: Great Article"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": "Thanks for sharing this insight!"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "target_url",
                    "value": "https://example.com/great-article"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "tags",
                    "value": "response, discussion"
                }]
            }
        ]
        
        with patch.object(discord_bot, 'publishing_service') as mock_service:
            mock_service.publish_post.return_value = Mock(
                success=True,
                message="Response post published successfully",
                site_url="https://test.example.com/posts/re-great-article"
            )
            
            response = await discord_bot.handle_interaction(modal_payload)
            
            assert response["type"] == 4
            assert "successfully" in response["data"]["content"]
    
    @pytest.mark.asyncio
    async def test_error_handling_publishing_failure(self, discord_bot, discord_interaction_payloads):
        """Test error handling when publishing fails."""
        modal_payload = discord_interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = "post_modal_note"
        modal_payload["data"]["components"] = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": "Failed Post"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": "This post will fail to publish"
                }]
            }
        ]
        
        with patch.object(discord_bot, 'publishing_service') as mock_service:
            mock_service.publish_post.return_value = Mock(
                success=False,
                message="GitHub API error: Repository not found"
            )
            
            response = await discord_bot.handle_interaction(modal_payload)
            
            assert response["type"] == 4
            assert "error" in response["data"]["content"].lower()
            assert "repository not found" in response["data"]["content"]
    
    @pytest.mark.asyncio
    async def test_invalid_interaction_handling(self, discord_bot):
        """Test handling of invalid or malformed interactions."""
        invalid_payloads = [
            {},  # Empty payload
            {"type": 999},  # Invalid type
            {"type": 2, "data": {}},  # Missing required data
            {"type": 5, "data": {"custom_id": "unknown_modal"}},  # Unknown modal
        ]
        
        for payload in invalid_payloads:
            response = await discord_bot.handle_interaction(payload)
            
            assert response["type"] == 4  # Error message response
            assert "error" in response["data"]["content"].lower()
    
    def test_signature_verification_integration(self, discord_bot):
        """Test Discord signature verification with realistic data."""
        # Mock the crypto verification function
        with patch('discord_publish_bot.discord.interactions.verify_signature') as mock_verify:
            mock_verify.return_value = True
            
            # Test with realistic signature data
            signature = "ed25519=signature_here"
            timestamp = "1640995200"
            body = b'{"type": 1, "id": "interaction_id"}'
            
            result = discord_bot.verify_signature(signature, timestamp, body)
            
            assert result is True
            mock_verify.assert_called_once_with(
                signature, timestamp, body, discord_bot.settings.discord.public_key
            )
    
    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self, discord_bot, discord_interaction_payloads):
        """Test behavior under rapid interaction submissions."""
        command_payload = discord_interaction_payloads["slash_command"]
        
        # Simulate multiple rapid requests
        responses = []
        for i in range(5):
            response = await discord_bot.handle_interaction(command_payload)
            responses.append(response)
        
        # All should be handled properly (no rate limiting in our implementation)
        for response in responses:
            assert response["type"] == 9  # MODAL response
    
    def test_modal_component_extraction(self, discord_bot):
        """Test extraction of data from Discord modal components."""
        modal_data = {
            "custom_id": "post_modal_note",
            "components": [
                {
                    "type": 1,
                    "components": [{
                        "type": 4,
                        "custom_id": "title",
                        "value": "Test Title"
                    }]
                },
                {
                    "type": 1,
                    "components": [{
                        "type": 4,
                        "custom_id": "content",
                        "value": "Test content here"
                    }]
                },
                {
                    "type": 1,
                    "components": [{
                        "type": 4,
                        "custom_id": "tags",
                        "value": "test, integration"
                    }]
                }
            ]
        }
        
        post_data = discord_bot._extract_post_data_from_modal(modal_data)
        
        assert isinstance(post_data, PostData)
        assert post_data.title == "Test Title"
        assert post_data.content == "Test content here"
        assert post_data.tags == ["test", "integration"]
        assert post_data.post_type == PostType.NOTE
    
    def test_different_post_type_modals(self, discord_bot):
        """Test modal creation for different post types."""
        post_types = ["note", "response", "bookmark", "media"]
        
        for post_type in post_types:
            modal = discord_bot._create_post_modal(post_type)
            
            assert modal["type"] == 9  # MODAL type
            assert post_type in modal["data"]["custom_id"]
            
            components = modal["data"]["components"]
            
            # All modals should have title and content
            component_ids = []
            for action_row in components:
                for component in action_row["components"]:
                    component_ids.append(component["custom_id"])
            
            assert "title" in component_ids
            assert "content" in component_ids
            
            # Response and bookmark should have target_url
            if post_type in ["response", "bookmark"]:
                assert "target_url" in component_ids
            
            # Media should have media_url
            if post_type == "media":
                assert "media_url" in component_ids


@pytest.mark.integration
class TestDiscordPublishingIntegration:
    """Test integration between Discord and publishing service."""
    
    @pytest.fixture
    def discord_bot_with_real_publishing(self, test_settings, mock_github_client):
        """Create Discord bot with real publishing service but mocked GitHub."""
        from discord_publish_bot.publishing.service import PublishingService
        
        publishing_service = PublishingService(
            github_client=mock_github_client,
            github_settings=test_settings.github,
            publishing_settings=test_settings.publishing
        )
        
        bot = DiscordInteractionsHandler(test_settings.discord)
        bot.publishing_service = publishing_service
        
        return bot
    
    @pytest.mark.asyncio
    async def test_end_to_end_note_publishing(self, discord_bot_with_real_publishing, discord_interaction_payloads):
        """Test end-to-end note publishing through Discord."""
        modal_payload = discord_interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = "post_modal_note"
        modal_payload["data"]["components"] = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": "E2E Integration Test"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": "This tests the complete flow from Discord to GitHub."
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "tags",
                    "value": "integration, e2e, testing"
                }]
            }
        ]
        
        response = await discord_bot_with_real_publishing.handle_interaction(modal_payload)
        
        assert response["type"] == 4
        assert "successfully" in response["data"]["content"]
        
        # Verify GitHub client was called
        github_client = discord_bot_with_real_publishing.publishing_service.github_client
        github_client.create_file.assert_called_once()
        
        # Verify the content passed to GitHub
        call_args = github_client.create_file.call_args
        filename, content, commit_message = call_args[0]
        
        assert filename.endswith(".md")
        assert "E2E Integration Test" in content
        assert "This tests the complete flow" in content
        assert "integration" in content
        assert "commit" in commit_message.lower()
    
    @pytest.mark.asyncio
    async def test_frontmatter_generation_through_discord(self, discord_bot_with_real_publishing, discord_interaction_payloads):
        """Test that frontmatter is correctly generated through Discord workflow."""
        # Test response post with target URL
        modal_payload = discord_interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = "post_modal_response"
        modal_payload["data"]["components"] = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": "Response to Article"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": "Great points made in this article!"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "target_url",
                    "value": "https://example.com/original-article"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "tags",
                    "value": "response, discussion"
                }]
            }
        ]
        
        response = await discord_bot_with_real_publishing.handle_interaction(modal_payload)
        
        assert response["type"] == 4
        assert "successfully" in response["data"]["content"]
        
        # Verify the frontmatter in the generated content
        github_client = discord_bot_with_real_publishing.publishing_service.github_client
        call_args = github_client.create_file.call_args
        content = call_args[0][1]  # Content is second argument
        
        # Should contain response post frontmatter
        assert "response_type: response" in content
        assert "in_reply_to: https://example.com/original-article" in content
        assert "dt_published:" in content
        assert "- response" in content
        assert "- discussion" in content
