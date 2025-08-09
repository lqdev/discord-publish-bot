"""
Pytest configuration and shared fixtures for Discord Publish Bot tests.

Provides common fixtures, test configuration, and utilities for all test types.
"""

import os
import asyncio
import pytest
from pathlib import Path
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock

# Import our application modules
from discord_publish_bot.config import AppSettings
from discord_publish_bot.publishing import GitHubClient, PublishingService
from discord_publish_bot.discord import DiscordInteractionsHandler
from discord_publish_bot.shared import PostData, PostType


# Test configuration
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> AppSettings:
    """Provide test application settings with safe defaults."""
    return AppSettings(
        app_name="Discord Publish Bot Test",
        version="2.0.0-test",
        environment="development",
        log_level="DEBUG",
        discord=AppSettings.DiscordSettings(
            bot_token="test_bot_token",
            application_id="123456789012345678",
            public_key="a" * 64,
        ),
        github=AppSettings.GitHubSettings(
            token="ghp_test_token_1234567890abcdef",
            repository="test-user/test-repo",
            branch="main"
        ),
        api=AppSettings.APISettings(
            key="test_api_key_1234567890abcdef",
            host="localhost",
            port=8000,
            endpoint="http://localhost:8000"
        ),
        publishing=AppSettings.PublishingSettings(
            site_base_url="https://test-site.example.com",
            default_author="Test Author"
        )
    )


@pytest.fixture
def mock_github_client():
    """Provide a mock GitHub client for testing."""
    client = Mock(spec=GitHubClient)
    client.check_connectivity = AsyncMock(return_value=True)
    client.create_file = AsyncMock(return_value={
        "commit": {"sha": "abc123"},
        "content": {"download_url": "https://github.com/test/file.md"}
    })
    client.get_repository_info = Mock(return_value={
        "name": "test-repo",
        "owner": {"login": "test-user"},
        "default_branch": "main"
    })
    return client


@pytest.fixture
def sample_post_data() -> Dict[str, PostData]:
    """Provide sample post data for testing."""
    return {
        "note": PostData(
            title="Test Note",
            content="This is a test note for unit testing purposes.",
            post_type=PostType.NOTE,
            tags=["testing", "unit-test"]
        ),
        "response": PostData(
            title="Test Response",
            content="This is a test response to another post.",
            post_type=PostType.RESPONSE,
            tags=["testing", "response"],
            target_url="https://example.com/original-post"
        ),
        "bookmark": PostData(
            title="Test Bookmark",
            content="Bookmarking this for later reference.",
            post_type=PostType.BOOKMARK,
            tags=["testing", "bookmark"],
            target_url="https://example.com/interesting-article"
        ),
        "media": PostData(
            title="Test Media Post",
            content="Sharing an interesting image or video.",
            post_type=PostType.MEDIA,
            tags=["testing", "media"],
            media_url="https://example.com/image.jpg"
        )
    }


@pytest.fixture
def discord_interaction_payloads() -> Dict[str, Dict[str, Any]]:
    """Provide sample Discord interaction payloads."""
    return {
        "ping": {
            "type": 1,
            "id": "test_ping_interaction",
            "application_id": "123456789012345678",
            "token": "test_token",
            "version": 1
        },
        "slash_command": {
            "type": 2,
            "id": "test_command_interaction",
            "application_id": "123456789012345678",
            "token": "test_token",
            "version": 1,
            "data": {
                "id": "test_command_id",
                "name": "post",
                "type": 1,
                "options": [
                    {
                        "name": "type",
                        "type": 3,
                        "value": "note"
                    }
                ]
            }
        },
        "modal_submit": {
            "type": 5,
            "id": "test_modal_interaction",
            "application_id": "123456789012345678",
            "token": "test_token",
            "version": 1,
            "data": {
                "custom_id": "post_modal_note",
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 4,
                                "custom_id": "title",
                                "value": "Test Modal Post"
                            }
                        ]
                    },
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 4,
                                "custom_id": "content",
                                "value": "Content from modal submission"
                            }
                        ]
                    }
                ]
            }
        }
    }


@pytest.fixture
def publishing_service(test_settings, mock_github_client):
    """Provide a publishing service with mocked dependencies."""
    return PublishingService(
        github_client=mock_github_client,
        settings=test_settings
    )


@pytest.fixture
def mock_discord_bot(test_settings):
    """Provide a mock Discord bot for testing."""
    return DiscordInteractionsHandler(test_settings)


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (moderate speed, external deps)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (slow, full system)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


# Test utilities
class TestHelper:
    """Utility methods for tests."""
    
    @staticmethod
    def create_test_file_content(frontmatter: Dict[str, Any], content: str) -> str:
        """Create a test markdown file with frontmatter."""
        import yaml
        
        fm_str = yaml.dump(frontmatter, default_flow_style=False)
        return f"---\n{fm_str}---\n\n{content}"
    
    @staticmethod
    def assert_valid_frontmatter(frontmatter: Dict[str, Any], post_type: str):
        """Assert that frontmatter contains required fields for post type."""
        required_fields = {
            "note": ["title", "post_type", "published_date", "tags"],
            "response": ["title", "response_type", "dt_published", "in_reply_to"],
            "bookmark": ["title", "response_type", "dt_published", "targeturl"],
            "media": ["title", "post_type", "published_date", "media_url"]
        }
        
        for field in required_fields.get(post_type, []):
            assert field in frontmatter, f"Missing required field '{field}' for {post_type}"


@pytest.fixture
def test_helper():
    """Provide test utility methods."""
    return TestHelper
