"""
Pytest configuration and shared fixtures for Discord Publish Bot tests.

Provides safe, isolated test environment with mock credentials and dependencies.
"""

import os
import asyncio
import pytest
from pathlib import Path
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock

"""
Pytest configuration and shared fixtures for Discord Publish Bot tests.

Provides safe, isolated test environment with mock credentials and dependencies.
"""

import os
import asyncio
import pytest
from pathlib import Path
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch

# Security: List of environment variables that contain sensitive data
SENSITIVE_ENV_VARS = [
    "DISCORD_BOT_TOKEN",
    "DISCORD_USER_ID", 
    "DISCORD_APPLICATION_ID",
    "DISCORD_PUBLIC_KEY",
    "DISCORD_GUILD_ID",
    "GITHUB_TOKEN",
    "GITHUB_REPO",
    "API_KEY",
    "FASTAPI_ENDPOINT",
    "SITE_BASE_URL"
]

def verify_no_production_credentials():
    """Verify that no production credentials are present in the environment."""
    dangerous_patterns = [
        ("DISCORD_BOT_TOKEN", ["FAKE_TOKENNEVER_REAL_TOKEN"]),  # Start of real token
        ("GITHUB_TOKEN", ["ghp_FAKE4W2rwp0WycBUp76grs48jLSeorh"]),  # Start of real token  
        ("DISCORD_USER_ID", ["727687304596160593"]),  # Real user ID
        ("GITHUB_REPO", ["example-dev/luisquintanilla.me"]),  # Real repo
    ]
    
    for env_var, dangerous_values in dangerous_patterns:
        current_value = os.environ.get(env_var, "")
        for dangerous_value in dangerous_values:
            if dangerous_value in current_value:
                raise ValueError(
                    f"SECURITY VIOLATION: Production credential detected!\n"
                    f"Environment variable '{env_var}' contains production data.\n"
                    f"This should never happen during testing."
                )

@pytest.fixture(autouse=True, scope="session")
def isolate_test_environment():
    """Automatically isolate test environment for all tests."""
    # Clear sensitive environment variables
    for var in SENSITIVE_ENV_VARS:
        if var in os.environ:
            del os.environ[var]
    
    # Set safe test environment
    test_env = {
        "DISCORD_BOT_TOKEN": "FAKE.TEST.TOKEN_NEVER_REAL",
        "DISCORD_APPLICATION_ID": "123456789012345678", 
        "DISCORD_PUBLIC_KEY": "f" * 64,
        "DISCORD_USER_ID": "987654321098765432",
        "GITHUB_TOKEN": "ghp_FAKE_TEST_TOKEN_NEVER_REAL",
        "GITHUB_REPO": "test-user/test-repo",
        "API_KEY": "test_FAKE_api_key_NEVER_REAL",
        "ENVIRONMENT": "development"  # Use valid environment
    }
    
    with patch.dict(os.environ, test_env, clear=False):
        yield

@pytest.fixture(autouse=True, scope="function")
def prevent_dotenv_loading():
    """Prevent .env file loading during tests."""
    with patch('dotenv.load_dotenv') as mock_load_dotenv:
        mock_load_dotenv.return_value = True
        yield

# Import our application modules AFTER security isolation setup
from discord_publish_bot.config import AppSettings, DiscordSettings, GitHubSettings, APISettings, PublishingSettings
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
def test_env_vars(monkeypatch):
    """Provide test environment variables."""
    test_vars = {
        "DISCORD_BOT_TOKEN": "FAKE_TEST_TOKEN_123456789.GhI6jK.abcdefghijklmnopqrstuvwxyz1234567890ABC",
        "DISCORD_APPLICATION_ID": "123456789012345678", 
        "DISCORD_PUBLIC_KEY": "a" * 64,
        "DISCORD_USER_ID": "987654321098765432",
        "GITHUB_TOKEN": "ghp_test_token_1234567890abcdef",
        "GITHUB_REPO": "test-user/test-repo",
        "GITHUB_BRANCH": "main",
        "API_KEY": "test_api_key_1234567890abcdef",
        "API_HOST": "localhost",
        "API_PORT": "8000",
        "SITE_BASE_URL": "https://test-site.example.com",
        "DEFAULT_AUTHOR": "Test Author",
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "DEBUG"
    }
    
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    
    return test_vars


@pytest.fixture
def test_settings() -> AppSettings:
    """
    Provide test application settings with completely safe, fake defaults.
    
    These credentials are designed to be obviously fake and safe for testing.
    They will never work with real services.
    """
    # Double-check security before creating settings
    verify_no_production_credentials()
    
    return AppSettings(
        app_name="Discord Publish Bot Test",
        version="2.0.0-test",
        environment="development",  # Use valid environment value
        log_level="DEBUG",
        discord=DiscordSettings(
            bot_token="FAKE_TEST_TOKEN_123456789.FAKE.TEST_TOKEN_NEVER_REAL_SAFE_FOR_TESTING",
            application_id="123456789012345678",
            public_key="f" * 64,  # Changed from "a" * 64 to make it more obviously fake
            authorized_user_id="987654321098765432"
        ),
        github=GitHubSettings(
            token="ghp_FAKE_TEST_TOKEN_SAFE_1234567890abcdef_NEVER_REAL",
            repository="test-user/test-repo-safe",
            branch="main"
        ),
        api=APISettings(
            key="test_api_key_SAFE_FAKE_1234567890abcdef_NEVER_REAL",
            host="localhost",
            port=8000,
            endpoint="http://localhost:8000"
        ),
        publishing=PublishingSettings(
            site_base_url="https://test-site-safe.example.com",
            default_author="Test Author"
        )
    )


@pytest.fixture
def mock_github_client():
    """Provide a mock GitHub client for testing."""
    client = Mock(spec=GitHubClient)
    client.check_connectivity = AsyncMock(return_value=True)
    # Fix: create_commit should return direct sha/url structure, not nested
    client.create_commit = AsyncMock(return_value={
        "sha": "abc123def456",
        "url": "https://github.com/test/repo/commit/abc123def456"
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
            "user": {
                "id": "987654321098765432",
                "username": "testuser"
            },
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
            "user": {
                "id": "987654321098765432",
                "username": "testuser"
            },
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
        github_settings=test_settings.github,
        publishing_settings=test_settings.publishing
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
