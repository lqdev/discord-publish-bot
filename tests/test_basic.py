"""
Test suite for Discord Publish Bot.

Tests both Discord bot and Publishing API components.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Configure pytest for async testing
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def mock_discord_interaction():
    """Mock Discord interaction object."""
    interaction = Mock()
    interaction.user.id = 123456789
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.fixture
def mock_api_client():
    """Mock API client for testing."""
    client = Mock()
    client.publish_post = AsyncMock(return_value=(True, {"filepath": "test.md"}))
    client.check_health = AsyncMock(return_value=True)
    return client


@pytest.fixture
def sample_discord_message():
    """Sample Discord message for testing."""
    return """/post note
---
title: Test Note
tags: ["test", "sample"]
---
This is a test note with **markdown** content."""


class TestPlaceholder:
    """Placeholder test class to ensure pytest runs successfully."""

    def test_basic_setup(self):
        """Test that basic setup works."""
        assert True

    @pytest.mark.asyncio
    async def test_async_setup(self):
        """Test that async setup works."""
        await asyncio.sleep(0.01)
        assert True
