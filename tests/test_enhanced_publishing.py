"""
Test enhanced publishing functionality with branch/PR workflow and schema compliance.

Tests the new features implemented for luisquintanilla.me website compatibility.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.publishing_api.config import APIConfig
from src.publishing_api.github_client import GitHubClient
from src.publishing_api.publishing import PublishingService


class TestEnhancedPublishing:
    """Test enhanced publishing service functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock(spec=APIConfig)
        config.github_token = "test_token"
        config.github_repo = "test/repo"
        config.github_branch = "main"
        config.site_base_url = "https://example.com"
        return config

    @pytest.fixture
    def mock_github_client(self):
        """Create mock GitHub client."""
        client = MagicMock(spec=GitHubClient)
        
        # Mock branch creation
        client.create_branch = AsyncMock(return_value=(True, "Branch created successfully"))
        
        # Mock commit
        client.commit_file = AsyncMock(return_value="abc123")
        
        # Mock PR creation
        client.create_pull_request = AsyncMock(
            return_value=(True, "PR created successfully", "https://github.com/test/repo/pull/1")
        )
        
        # Mock branch name generation
        client.generate_branch_name = MagicMock(
            return_value="content/discord-bot/2025-08-08/note/user123-msg456"
        )
        
        # Mock PR template generation
        client.generate_pr_template = MagicMock(
            return_value=("Add note post: Test content", "Generated PR body")
        )
        
        # Mock enhanced commit workflow
        client.commit_file_to_branch = AsyncMock(return_value={
            "branch_created": True,
            "file_committed": True,
            "pr_created": True,
            "branch_name": "content/discord-bot/2025-08-08/note/user123-msg456",
            "commit_sha": "abc123",
            "pr_url": "https://github.com/test/repo/pull/1",
            "error": None,
        })
        
        return client

    @pytest.fixture
    def publishing_service(self, mock_github_client, mock_config):
        """Create publishing service with mocked dependencies."""
        return PublishingService(mock_github_client, mock_config)

    def test_content_type_directory_mapping(self, publishing_service):
        """Test that content types map to correct directories."""
        expected_mappings = {
            "note": "_src/notes",
            "response": "_src/responses",
            "bookmark": "_src/responses",
            "media": "_src/media",
        }
        
        for content_type, expected_dir in expected_mappings.items():
            assert publishing_service.CONTENT_TYPE_DIRECTORIES[content_type] == expected_dir

    def test_frontmatter_schema_compliance(self, publishing_service):
        """Test frontmatter conversion to target site schema."""
        # Test note post conversion
        source_frontmatter = {
            "type": "note",
            "date": "2025-08-08T10:30:00Z",
            "title": "Test Note",
            "tags": ["test", "note"]
        }
        
        target_frontmatter = publishing_service.convert_to_target_schema(
            "note", source_frontmatter, "Test content"
        )
        
        assert target_frontmatter["post_type"] == "note"
        assert "published_date" in target_frontmatter
        assert target_frontmatter["title"] == "Test Note"
        assert target_frontmatter["tags"] == ["test", "note"]

    def test_response_frontmatter_conversion(self, publishing_service):
        """Test response post frontmatter conversion."""
        source_frontmatter = {
            "type": "response",
            "response_type": "bookmark",
            "date": "2025-08-08T10:30:00Z",
            "title": "Interesting Article",
            "url": "https://example.com/article",
            "tags": ["bookmark", "article"]
        }
        
        target_frontmatter = publishing_service.convert_to_target_schema(
            "response", source_frontmatter, "Great read!"
        )
        
        assert target_frontmatter["response_type"] == "bookmark"
        assert "dt_published" in target_frontmatter
        assert "dt_updated" in target_frontmatter
        assert target_frontmatter["targeturl"] == "https://example.com/article"
        assert target_frontmatter["title"] == "Interesting Article"

    def test_bookmark_handling(self, publishing_service):
        """Test that bookmarks are handled as responses with correct type."""
        source_frontmatter = {
            "type": "bookmark",
            "date": "2025-08-08T10:30:00Z",
            "url": "https://example.com",
            "tags": ["bookmark"]
        }
        
        target_frontmatter = publishing_service.convert_to_target_schema(
            "bookmark", source_frontmatter, "Check this out"
        )
        
        assert target_frontmatter["response_type"] == "bookmark"
        assert target_frontmatter["targeturl"] == "https://example.com"
        assert "dt_published" in target_frontmatter
        assert "dt_updated" in target_frontmatter

    def test_content_validation(self, publishing_service):
        """Test content validation against target site requirements."""
        frontmatter = {
            "post_type": "note",
            "title": "Test Note",
            "published_date": "2025-08-08 10:30 -05:00",
            "tags": ["test"]
        }
        
        validation_results = publishing_service.validate_content(
            "note", frontmatter, "This is test content"
        )
        
        assert validation_results["required_fields"]["passed"] is True
        assert validation_results["content_length"]["passed"] is True
        assert validation_results["title_quality"]["passed"] is True

    def test_validation_missing_fields(self, publishing_service):
        """Test validation catches missing required fields."""
        incomplete_frontmatter = {
            "title": "Test Note"
            # Missing post_type and published_date
        }
        
        validation_results = publishing_service.validate_content(
            "note", incomplete_frontmatter, "Content"
        )
        
        assert validation_results["required_fields"]["passed"] is False
        assert "post_type" in validation_results["required_fields"]["message"]

    def test_filename_generation_target_format(self, publishing_service):
        """Test filename generation matches target site patterns."""
        frontmatter = {
            "published_date": "2025-08-08 10:30 -05:00",
            "slug": "test-note"
        }
        
        filename = publishing_service.generate_filename("note", frontmatter, "Content")
        
        assert filename == "2025-08-08-test-note.md"

    def test_date_format_handling(self, publishing_service):
        """Test handling of various date formats."""
        # Test ISO format
        iso_frontmatter = {"date": "2025-08-08T10:30:00Z"}
        target = publishing_service.convert_to_target_schema("note", iso_frontmatter, "")
        assert "published_date" in target
        
        # Test target site format
        site_frontmatter = {"dt_published": "2025-08-08 10:30"}
        target = publishing_service.convert_to_target_schema("response", site_frontmatter, "")
        assert "dt_published" in target

    @pytest.mark.asyncio
    async def test_enhanced_publish_workflow(self, publishing_service):
        """Test the complete enhanced publishing workflow."""
        message = """/post note
---
title: "Test Note"
tags: ["test", "automation"]
---

This is a test note content."""

        result = await publishing_service.publish_post(message, "user123")
        
        assert result["status"] == "success"
        assert result["workflow"] == "branch_and_pr"
        assert result["branch_name"] == "content/discord-bot/2025-08-08/note/user123-msg456"
        assert result["commit_sha"] == "abc123"
        assert result["pr_url"] == "https://github.com/test/repo/pull/1"
        assert result["directory"] == "_src/notes"
        assert "site_url_after_merge" in result

    @pytest.mark.asyncio
    async def test_response_post_workflow(self, publishing_service):
        """Test response post with target URL."""
        message = """/post response
---
response_type: "bookmark"
url: "https://example.com/article"
title: "Great Article"
---

This article has great insights."""

        # Update mock for response workflow
        publishing_service.github_client.generate_branch_name.return_value = (
            "content/discord-bot/2025-08-08/response/user123-msg456"
        )
        
        result = await publishing_service.publish_post(message, "user123")
        
        assert result["status"] == "success"
        assert result["directory"] == "_src/responses"

    def test_markdown_generation_target_format(self, publishing_service):
        """Test markdown file generation matches target site format."""
        frontmatter = {
            "post_type": "note",
            "title": "Test Note",
            "published_date": "2025-08-08 10:30 -05:00",
            "tags": ["test", "note"]
        }
        
        content = "This is test content."
        markdown = publishing_service.build_markdown_file(frontmatter, content)
        
        assert markdown.startswith("---\n")
        assert "post_type: note" in markdown
        assert "published_date: 2025-08-08 10:30 -05:00" in markdown
        assert markdown.endswith("This is test content.")

    def test_tag_handling(self, publishing_service):
        """Test tag processing and default tag assignment."""
        # Test string tags conversion
        frontmatter_string_tags = {"tags": "test, automation, discord"}
        target = publishing_service.convert_to_target_schema("note", frontmatter_string_tags, "")
        assert isinstance(target["tags"], list)
        assert "test" in target["tags"]
        
        # Test default tags for missing tags
        frontmatter_no_tags = {}
        target = publishing_service.convert_to_target_schema("note", frontmatter_no_tags, "")
        assert "discord" in target["tags"]
        assert "automated" in target["tags"]

    def test_slug_generation_compliance(self, publishing_service):
        """Test slug generation follows target site patterns."""
        # Test content-based slug
        content = "This is a test note with special characters!"
        slug = publishing_service.generate_slug(content)
        assert slug == "this-is-a-test-note-with-special-characters"
        
        # Test empty content handling
        empty_slug = publishing_service.generate_slug("")
        assert empty_slug == "untitled"


class TestGitHubClientEnhancements:
    """Test GitHub client enhancements for branch/PR workflow."""

    @pytest.fixture
    def github_client(self):
        """Create GitHub client with mocked dependencies."""
        with patch('src.publishing_api.github_client.Github') as mock_github:
            client = GitHubClient("test_token", "test/repo")
            
            # Mock repository
            mock_repo = MagicMock()
            client._repo = mock_repo
            
            return client, mock_repo

    def test_branch_name_generation(self, github_client):
        """Test branch name generation follows conventions."""
        client, _ = github_client
        
        branch_name = client.generate_branch_name("note", "msg123", "user456")
        
        assert branch_name.startswith("content/discord-bot/")
        assert "/note/" in branch_name
        assert branch_name.endswith("user456-msg123")

    def test_pr_template_generation(self, github_client):
        """Test PR template generation includes required information."""
        client, _ = github_client
        
        title, body = client.generate_pr_template(
            content_type="note",
            content_preview="This is a test note",
            user_id="user123",
            message_id="msg456"
        )
        
        assert "Add note post:" in title
        assert "This is a test note" in title
        assert "Discord Bot" in body
        assert "user123" in body
        assert "msg456" in body
        assert "Content Preview" in body
        assert "Validation Status" in body

    @pytest.mark.asyncio
    async def test_enhanced_commit_workflow_success(self, github_client):
        """Test successful enhanced commit workflow."""
        client, mock_repo = github_client
        
        # Mock successful operations
        with patch.object(client, 'create_branch', return_value=(True, "Success")), \
             patch.object(client, 'commit_file', return_value="abc123"), \
             patch.object(client, 'create_pull_request', return_value=(True, "Success", "https://github.com/test/pull/1")):
            
            result = await client.commit_file_to_branch(
                filepath="test.md",
                content="test content",
                commit_message="Test commit",
                branch_name="test-branch"
            )
            
            assert result["branch_created"] is True
            assert result["file_committed"] is True
            assert result["pr_created"] is True
            assert result["commit_sha"] == "abc123"
            assert result["pr_url"] == "https://github.com/test/pull/1"


class TestSchemaCompliance:
    """Test compliance with luisquintanilla.me schema patterns."""

    @pytest.fixture
    def publishing_service(self):
        """Create publishing service for schema testing."""
        mock_client = MagicMock()
        mock_config = MagicMock()
        return PublishingService(mock_client, mock_config)

    def test_note_schema_compliance(self, publishing_service):
        """Test note posts match target site schema."""
        source = {
            "type": "note",
            "date": "2025-08-08T10:30:00Z",
            "title": "Weekly Summary"
        }
        
        target = publishing_service.convert_to_target_schema("note", source, "Content")
        
        # Should match patterns from _src/feed/*.md
        assert target["post_type"] == "note"
        assert "published_date" in target
        assert target["title"] == "Weekly Summary"

    def test_response_schema_compliance(self, publishing_service):
        """Test response posts match target site schema."""
        source = {
            "type": "response",
            "response_type": "bookmark",
            "date": "2025-08-08T10:30:00Z",
            "url": "https://example.com",
            "title": "Interesting Link"
        }
        
        target = publishing_service.convert_to_target_schema("response", source, "Great resource!")
        
        # Should match patterns from _src/responses/*.md
        assert target["response_type"] == "bookmark"
        assert target["targeturl"] == "https://example.com"
        assert "dt_published" in target
        assert "dt_updated" in target
        assert target["title"] == "Interesting Link"

    def test_media_schema_compliance(self, publishing_service):
        """Test media posts match target site schema."""
        source = {
            "type": "media",
            "date": "2025-08-08T10:30:00Z",
            "media_url": "https://example.com/image.jpg"
        }
        
        target = publishing_service.convert_to_target_schema("media", source, "Photo from today")
        
        # Media posts are notes with media content
        assert target["post_type"] == "note"
        assert "published_date" in target
        assert target["media_url"] == "https://example.com/image.jpg"

    def test_directory_structure_compliance(self, publishing_service):
        """Test directory structure matches target site."""
        expected_structure = {
            "note": "_src/notes",
            "response": "_src/responses",
            "bookmark": "_src/responses",  # Bookmarks are responses
            "media": "_src/media",
        }
        
        for content_type, expected_dir in expected_structure.items():
            actual_dir = publishing_service.CONTENT_TYPE_DIRECTORIES[content_type]
            assert actual_dir == expected_dir, f"Content type {content_type} should map to {expected_dir}"

    def test_date_format_compliance(self, publishing_service):
        """Test date formats match target site patterns."""
        # Target site uses different formats for different content types
        
        # Notes use: published_date: "2025-08-08 10:30 -05:00"
        note_target = publishing_service.convert_to_target_schema(
            "note", {"date": "2025-08-08T10:30:00Z"}, ""
        )
        assert "published_date" in note_target
        assert " -05:00" in note_target["published_date"]
        
        # Responses use: dt_published and dt_updated
        response_target = publishing_service.convert_to_target_schema(
            "response", {"date": "2025-08-08T10:30:00Z"}, ""
        )
        assert "dt_published" in response_target
        assert "dt_updated" in response_target
