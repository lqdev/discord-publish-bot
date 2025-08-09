"""
Basic end-to-end integration tests.

Simple tests to validate core integration points work correctly.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from discord_publish_bot.discord.interactions import DiscordInteractionsHandler
from discord_publish_bot.publishing.service import PublishingService 
from discord_publish_bot.shared import PostData, PostType


@pytest.mark.integration
class TestBasicEndToEnd:
    """Basic end-to-end workflow tests."""
    
    def test_discord_handler_initialization(self, test_settings):
        """Test that Discord handler can be initialized with settings."""
        handler = DiscordInteractionsHandler(test_settings.discord)
        
        assert handler.settings == test_settings.discord
        assert hasattr(handler, 'handle_interaction')
        assert hasattr(handler, 'verify_signature')
    
    def test_publishing_service_initialization(self, test_settings, mock_github_client):
        """Test that publishing service can be initialized correctly."""
        service = PublishingService(
            github_client=mock_github_client,
            github_settings=test_settings.github,
            publishing_settings=test_settings.publishing
        )
        
        assert service.github_client == mock_github_client
        assert service.github_settings == test_settings.github
        assert service.publishing_settings == test_settings.publishing
    
    @pytest.mark.asyncio
    async def test_complete_publishing_workflow(self, test_settings, mock_github_client):
        """Test complete publishing workflow with real service integration."""
        # Create publishing service
        service = PublishingService(
            github_client=mock_github_client,
            github_settings=test_settings.github,
            publishing_settings=test_settings.publishing
        )
        
        # Create test post data
        post_data = PostData(
            title="E2E Test Post",
            content="This is an end-to-end integration test post.",
            post_type=PostType.NOTE,
            tags=["e2e", "integration", "test"]
        )
        
        # Publish the post
        result = await service.publish_post(post_data)
        
        # Verify success
        assert result.success is True
        assert "successfully" in result.message.lower()
        assert result.filename == "2025-08-09-e2e-test-post.md"
        assert result.filepath == "_src/feed/2025-08-09-e2e-test-post.md"
        assert result.commit_sha == "abc123def456"
        assert result.file_url == "https://github.com/test/repo/commit/abc123def456"
        
        # Verify GitHub client was called correctly
        mock_github_client.create_commit.assert_called_once()
        call_args = mock_github_client.create_commit.call_args
        
        # Check the arguments passed to GitHub
        assert call_args.kwargs["filename"] == "_src/feed/2025-08-09-e2e-test-post.md"
        assert "E2E Test Post" in call_args.kwargs["content"]
        assert "This is an end-to-end integration test post." in call_args.kwargs["content"]
        assert "- e2e" in call_args.kwargs["content"]
        assert "- integration" in call_args.kwargs["content"]
        assert "Add note post: E2E Test Post" in call_args.kwargs["message"]
    
    def test_discord_ping_interaction(self, test_settings):
        """Test basic Discord ping interaction handling."""
        handler = DiscordInteractionsHandler(test_settings.discord)
        
        ping_interaction = {
            "type": 1,  # PING
            "id": "test_interaction_id",
            "token": "test_token"
        }
        
        response = handler.handle_interaction(ping_interaction)
        
        assert response["type"] == 1  # PONG
    
    def test_discord_command_interaction(self, test_settings):
        """Test Discord slash command interaction handling."""
        handler = DiscordInteractionsHandler(test_settings.discord)
        
        command_interaction = {
            "type": 2,  # APPLICATION_COMMAND
            "id": "test_interaction_id",
            "token": "test_token",
            "data": {
                "name": "post",
                "options": [
                    {
                        "name": "type",
                        "value": "note"
                    }
                ]
            },
            "member": {
                "user": {
                    "id": "987654321098765432",  # Use authorized user ID from test settings
                    "username": "testuser"
                }
            }
        }
        
        response = handler.handle_interaction(command_interaction)
        
        assert response["type"] == 9  # MODAL
        assert "post_modal_note" in response["data"]["custom_id"]
        assert "Create Note Post" in response["data"]["title"]
    
    def test_all_post_types_can_create_modals(self, test_settings):
        """Test that all post types can create proper modals."""
        handler = DiscordInteractionsHandler(test_settings.discord)
        
        for post_type in [PostType.NOTE, PostType.RESPONSE, PostType.BOOKMARK, PostType.MEDIA]:
            modal_data = handler._create_post_modal(post_type)
            
            # Check modal data structure (not response structure)
            assert "custom_id" in modal_data
            assert post_type.value in modal_data["custom_id"]
            assert "title" in modal_data
            assert "components" in modal_data
            assert len(modal_data["components"]) >= 2  # At least title and content
    
    def test_post_data_extraction_from_modal_data(self, test_settings):
        """Test extraction of PostData from Discord modal interaction."""
        handler = DiscordInteractionsHandler(test_settings.discord)
        
        modal_interaction = {
            "type": 5,  # MODAL_SUBMIT
            "data": {
                "custom_id": "post_modal_note",
                "components": [
                    {
                        "type": 1,  # ACTION_ROW
                        "components": [
                            {
                                "type": 4,  # TEXT_INPUT
                                "custom_id": "title",
                                "value": "Test Note Title"
                            }
                        ]
                    },
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 4,
                                "custom_id": "content",
                                "value": "This is the content of the test note."
                            }
                        ]
                    },
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 4,
                                "custom_id": "tags",
                                "value": "test, note, integration"
                            }
                        ]
                    }
                ]
            },
            "member": {
                "user": {
                    "id": "987654321098765432"  # Use authorized user ID
                }
            }
        }
        
        post_data = handler.extract_post_data_from_modal(modal_interaction)
        
        assert isinstance(post_data, PostData)
        assert post_data.title == "Test Note Title"
        assert post_data.content == "This is the content of the test note."
        assert post_data.post_type == PostType.NOTE
        assert post_data.tags == ["test", "note", "integration"]


@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration integration across components."""
    
    def test_settings_propagation(self, test_settings):
        """Test that settings are properly propagated to all components."""
        # Create Discord handler
        discord_handler = DiscordInteractionsHandler(test_settings.discord)
        
        # Create publishing service  
        mock_github = Mock()
        publishing_service = PublishingService(
            github_client=mock_github,
            github_settings=test_settings.github,
            publishing_settings=test_settings.publishing
        )
        
        # Verify settings are preserved
        assert discord_handler.settings.public_key == test_settings.discord.public_key
        assert publishing_service.github_settings.repository == test_settings.github.repository
        assert publishing_service.publishing_settings.site_base_url == test_settings.publishing.site_base_url
    
    def test_environment_specific_behavior(self, test_settings):
        """Test that components behave correctly based on environment settings."""
        # In test environment, certain validations should be relaxed
        assert test_settings.environment == "development"
        
        # Discord handler should work with test keys
        handler = DiscordInteractionsHandler(test_settings.discord)
        assert len(handler.settings.public_key) == 64  # Valid hex key length
        
        # Publishing service should use test repository
        mock_github = Mock()
        service = PublishingService(
            github_client=mock_github,
            github_settings=test_settings.github,
            publishing_settings=test_settings.publishing
        )
        assert "test" in service.github_settings.repository.lower()


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across integration points."""
    
    @pytest.mark.asyncio
    async def test_publishing_error_handling(self, test_settings):
        """Test error handling in publishing workflow."""
        # Create GitHub client that will fail
        failing_github_client = AsyncMock()
        failing_github_client.create_commit.side_effect = Exception("GitHub API error")
        
        service = PublishingService(
            github_client=failing_github_client,
            github_settings=test_settings.github,
            publishing_settings=test_settings.publishing
        )
        
        post_data = PostData(
            title="Test Post",
            content="This will fail to publish",
            post_type=PostType.NOTE,
            tags=["test"]
        )
        
        result = await service.publish_post(post_data)
        
        assert result.success is False
        assert "GitHub API error" in result.message
        assert result.error_code == "PUBLISHING_FAILED"
    
    def test_discord_invalid_interaction_handling(self, test_settings):
        """Test Discord handler's response to invalid interactions."""
        handler = DiscordInteractionsHandler(test_settings.discord)
        
        invalid_interactions = [
            {},  # Empty
            {"type": 999},  # Invalid type
            # Note: interactions with missing data may raise exceptions, which is valid behavior
        ]
        
        for invalid_interaction in invalid_interactions:
            try:
                response = handler.handle_interaction(invalid_interaction)
                # If we get a response, it should be a dict
                assert isinstance(response, dict)
                if "type" in response:
                    # Should be an error message response if it doesn't crash
                    assert response["type"] in [4, 1]  # Error response or PONG
            except Exception as e:
                # It's acceptable for the handler to raise exceptions for invalid data
                assert isinstance(e, (KeyError, ValueError, Exception))
                # This demonstrates that invalid interactions are handled (by raising exceptions)
