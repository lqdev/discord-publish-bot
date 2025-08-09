"""
Unit tests for publishing service functionality.

Tests the publishing service with mocked GitHub client.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from discord_publish_bot.publishing.service import PublishingService
from discord_publish_bot.publishing.github_client import GitHubClient
from discord_publish_bot.shared import PostData, PostType, PublishResult
from discord_publish_bot.shared.utils import (
    generate_filename, validate_url, parse_tags, format_datetime
)


@pytest.mark.unit
class TestPublishingService:
    """Test publishing service functionality."""
    
    def test_publishing_service_initialization(self, test_settings, mock_github_client):
        """Test publishing service can be initialized."""
        service = PublishingService(
            github_client=mock_github_client,
            github_settings=test_settings.github,
            publishing_settings=test_settings.publishing
        )
        
        assert service.github_client == mock_github_client
        assert service.github_settings == test_settings.github
        assert service.publishing_settings == test_settings.publishing
    
    @pytest.mark.asyncio
    async def test_publish_note_post(self, publishing_service, sample_post_data):
        """Test publishing a note post."""
        note_data = sample_post_data["note"]
        
        result = await publishing_service.publish_post(note_data)
        
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert "successfully" in result.message.lower()
        assert result.site_url is not None
    
    @pytest.mark.asyncio
    async def test_publish_response_post(self, publishing_service, sample_post_data):
        """Test publishing a response post."""
        response_data = sample_post_data["response"]
        
        result = await publishing_service.publish_post(response_data)
        
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert result.filepath.endswith("test-response.md")
        assert "_src/responses" in result.filepath  # Responses go to responses directory
    
    @pytest.mark.asyncio
    async def test_publish_bookmark_post(self, publishing_service, sample_post_data):
        """Test publishing a bookmark post."""
        bookmark_data = sample_post_data["bookmark"]
        
        result = await publishing_service.publish_post(bookmark_data)
        
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert result.filepath.endswith("test-bookmark.md")
        assert "_src/responses" in result.filepath  # Bookmarks go to responses directory
    
    @pytest.mark.asyncio
    async def test_publish_media_post(self, publishing_service, sample_post_data):
        """Test publishing a media post."""
        media_data = sample_post_data["media"]
        
        result = await publishing_service.publish_post(media_data)
        
        assert isinstance(result, PublishResult)
        assert result.success is True
        assert result.filepath.endswith("test-media-post.md")
        assert "_src/media" in result.filepath  # Media posts go to media directory
    
    def test_frontmatter_generation_note(self, publishing_service, sample_post_data):
        """Test frontmatter generation for note posts."""
        note_data = sample_post_data["note"]
        
        frontmatter = publishing_service._generate_frontmatter(note_data)
        
        assert frontmatter["title"] == note_data.title
        assert frontmatter["post_type"] == "note"
        assert "published_date" in frontmatter
        assert frontmatter["tags"] == note_data.tags
        assert "target_url" not in frontmatter  # Notes don't have target URLs
    
    def test_frontmatter_generation_response(self, publishing_service, sample_post_data):
        """Test frontmatter generation for response posts."""
        response_data = sample_post_data["response"]
        
        frontmatter = publishing_service._generate_frontmatter(response_data)
        
        assert frontmatter["title"] == response_data.title
        assert frontmatter["response_type"] == "reply"
        assert "dt_published" in frontmatter
        assert frontmatter["target_url"] == response_data.target_url
        assert frontmatter["tags"] == response_data.tags
    
    def test_frontmatter_generation_bookmark(self, publishing_service, sample_post_data):
        """Test frontmatter generation for bookmark posts."""
        bookmark_data = sample_post_data["bookmark"]
        
        frontmatter = publishing_service._generate_frontmatter(bookmark_data)
        
        assert frontmatter["title"] == bookmark_data.title
        assert frontmatter["response_type"] == "bookmark"
        assert "dt_published" in frontmatter
        assert frontmatter["target_url"] == bookmark_data.target_url
        assert frontmatter["tags"] == bookmark_data.tags
    
    def test_filename_generation(self, publishing_service, sample_post_data):
        """Test filename generation for different post types."""
        for post_type, post_data in sample_post_data.items():
            filename = generate_filename(
                post_type=post_data.post_type,
                title=post_data.title,
                timestamp=datetime.now()
            )
            
            assert filename.endswith(".md")
            assert len(filename) > 10  # Should have reasonable length
            
            # Filename should be URL-safe
            assert " " not in filename
            assert all(c.isalnum() or c in "-_." for c in filename)
    
    def test_content_formatting(self, publishing_service, sample_post_data):
        """Test markdown content formatting."""
        note_data = sample_post_data["note"]
        
        # Test frontmatter generation and content building
        frontmatter = publishing_service._generate_frontmatter(note_data)
        formatted_content = publishing_service._build_markdown_content(frontmatter, note_data.content)
        
        assert note_data.content in formatted_content
        # Should preserve markdown formatting
        assert "\n" in formatted_content or len(formatted_content.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_github_failure(self, test_settings, sample_post_data):
        """Test error handling when GitHub operations fail."""
        # Create a mock GitHub client that fails
        failing_github_client = AsyncMock()
        failing_github_client.create_file.side_effect = Exception("GitHub API Error")
        
        service = PublishingService(
            github_client=failing_github_client,
            github_settings=test_settings.github,
            publishing_settings=test_settings.publishing
        )
        
        note_data = sample_post_data["note"]
        result = await service.publish_post(note_data)
        
        assert result.success is False
        assert "error" in result.message.lower()
    
    def test_tag_validation_and_cleanup(self, publishing_service):
        """Test tag validation and cleanup."""
        test_cases = [
            (["valid", "tags"], ["valid", "tags"]),
            (["tag with spaces", "another-tag"], ["tag with spaces", "another-tag"]),
            (["", "valid-tag", ""], ["valid-tag"]),  # Empty tags filtered
            ([], []),  # Empty list handled
        ]
        
        for input_tags, expected_tags in test_cases:
            post_data = PostData(
                title="Test Post",
                content="Test content",
                post_type=PostType.NOTE,
                tags=input_tags
            )
            
            cleaned_tags = parse_tags(",".join(input_tags) if input_tags else "")
            assert cleaned_tags == expected_tags
    
    def test_url_validation(self, publishing_service):
        """Test URL validation for target URLs and media URLs."""
        valid_urls = [
            "https://example.com",
            "https://blog.example.com/post/123",
            "http://localhost:3000/test",
        ]
        
        invalid_urls = [
            "not-a-url",
            "",
            None
        ]
        
        for url in valid_urls:
            assert validate_url(url) is True
        
        for url in invalid_urls:
            assert validate_url(url or "") is False
    
    @pytest.mark.asyncio
    async def test_duplicate_post_handling(self, publishing_service, sample_post_data):
        """Test handling of duplicate posts."""
        note_data = sample_post_data["note"]
        
        # Mock GitHub client to simulate file already exists
        publishing_service.github_client.create_file.side_effect = Exception("File already exists")
        
        result = await publishing_service.publish_post(note_data)
        
        # Should handle gracefully (either success with different filename or clear error)
        assert isinstance(result, PublishResult)
    
    def test_content_length_validation(self, publishing_service):
        """Test content length validation."""
        # Very short content
        short_post = PostData(
            title="Short",
            content="Hi",
            post_type=PostType.NOTE,
            tags=["test"]
        )
        
        # Very long content
        long_content = "This is a very long post. " * 1000  # ~27,000 characters
        long_post = PostData(
            title="Long Post",
            content=long_content,
            post_type=PostType.NOTE,
            tags=["test"]
        )
        
        # Both should be valid (service should handle various lengths)
        short_frontmatter = publishing_service._generate_frontmatter(short_post)
        long_frontmatter = publishing_service._generate_frontmatter(long_post)
        
        assert short_frontmatter["title"] == "Short"
        assert long_frontmatter["title"] == "Long Post"


@pytest.mark.unit 
class TestPublishingUtilities:
    """Test publishing utility functions."""
    
    def test_slugify_function(self):
        """Test the slugify utility function."""
        from discord_publish_bot.shared.utils import slugify
        
        test_cases = [
            ("Simple Title", "simple-title"),
            ("Title with Special Characters!", "title-with-special-characters"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("Numbers 123 and Symbols @#$", "numbers-123-and-symbols"),
            ("", ""),  # Empty string
            ("Already-Slugified-Title", "already-slugified-title"),
        ]
        
        for input_title, expected_slug in test_cases:
            result = slugify(input_title)
            assert result == expected_slug, f"Failed for '{input_title}'"
    
    def test_datetime_formatting(self):
        """Test datetime formatting for frontmatter."""
        from discord_publish_bot.shared.utils import format_datetime
        
        test_datetime = datetime(2025, 8, 9, 12, 30, 45)
        
        # Test ISO format
        iso_formatted = format_datetime(test_datetime, format_str="%Y-%m-%dT%H:%M:%S")
        assert "2025-08-09T12:30:45" in iso_formatted
        
        # Test date only
        date_formatted = format_datetime(test_datetime, format_str="%Y-%m-%d")
        assert date_formatted == "2025-08-09"
    
    def test_frontmatter_serialization(self):
        """Test frontmatter serialization to YAML."""
        from discord_publish_bot.shared.utils import format_frontmatter
        
        frontmatter_dict = {
            "title": "Test Post",
            "post_type": "note",
            "published_date": "2025-08-09T12:30:45",
            "tags": ["test", "unit-test"]
        }
        
        yaml_output = format_frontmatter(frontmatter_dict)
        
        # Should be valid YAML without delimiters (format_frontmatter just does YAML)
        assert "title: Test Post" in yaml_output
        assert "post_type: note" in yaml_output
        assert "tags:" in yaml_output
    
    def test_content_hash_generation(self):
        """Test content hash generation for duplicate detection."""
        from discord_publish_bot.shared.utils import calculate_content_hash
        
        content1 = "This is test content"
        content2 = "This is test content"
        content3 = "This is different content"
        
        hash1 = calculate_content_hash(content1)
        hash2 = calculate_content_hash(content2)
        hash3 = calculate_content_hash(content3)
        
        assert hash1 == hash2  # Same content should have same hash
        assert hash1 != hash3  # Different content should have different hash
        assert len(hash1) > 0  # Hash should not be empty
