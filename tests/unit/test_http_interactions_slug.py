"""
Test HTTP interactions handler slug field integration for Phase 3.
"""
import pytest
from unittest.mock import Mock, patch
from src.discord_publish_bot.discord.interactions import DiscordInteractionsHandler
from src.discord_publish_bot.shared.types import PostType


class TestHTTPInteractionsSlugSupport:
    """Test HTTP interactions handler with slug field support."""

    @pytest.fixture
    def handler(self):
        """Create interactions handler with mocked settings."""
        mock_settings = Mock()
        mock_settings.discord.authorized_user_id = "987654321098765432"
        mock_settings.discord.public_key = "f" * 64
        
        with patch('src.discord_publish_bot.discord.interactions.VerifyKey'):
            handler = DiscordInteractionsHandler.__new__(DiscordInteractionsHandler)
            handler.settings = mock_settings
            handler.verify_key = Mock()
            return handler

    def test_modal_creation_includes_slug_field(self, handler):
        """Test that created modals include slug field."""
        # Test note modal
        modal = handler._create_post_modal(PostType.NOTE)
        
        # Check modal structure
        assert modal["title"] == "Create Note Post"
        assert "components" in modal
        assert len(modal["components"]) == 4  # Title, Content, Tags, Slug
        
        # Find slug field
        slug_field = None
        for component in modal["components"]:
            text_input = component["components"][0]
            if text_input["custom_id"] == "slug":
                slug_field = text_input
                break
        
        assert slug_field is not None, "Slug field should be present in modal"
        assert slug_field["label"] == "Custom Slug (optional)"
        assert slug_field["required"] is False
        assert slug_field["max_length"] == 80

    def test_modal_creation_all_post_types_have_slug(self, handler):
        """Test that all post types include slug field."""
        for post_type in PostType:
            modal = handler._create_post_modal(post_type)
            
            # Find slug field
            slug_field = None
            for component in modal["components"]:
                text_input = component["components"][0]
                if text_input["custom_id"] == "slug":
                    slug_field = text_input
                    break
            
            assert slug_field is not None, f"Slug field should be present in {post_type.value} modal"

    def test_media_modal_has_correct_field_count(self, handler):
        """Test that media modal has correct number of fields after simplification."""
        # Test media modal without attachment
        modal = handler._create_post_modal(PostType.MEDIA)
        
        # Should have: Title, Content, Tags, Slug, Media URL (5 fields total)
        assert len(modal["components"]) == 5
        
        # Verify field IDs
        field_ids = []
        for component in modal["components"]:
            text_input = component["components"][0]
            field_ids.append(text_input["custom_id"])
        
        expected_fields = ["title", "content", "tags", "slug", "media_url"]
        assert field_ids == expected_fields

    def test_media_modal_with_attachment(self, handler):
        """Test media modal with attachment data."""
        attachment_data = {
            "url": "https://cdn.discordapp.com/attachments/123/456/test.jpg",
            "filename": "test.jpg",
            "content_type": "image/jpeg"
        }
        
        modal = handler._create_post_modal(PostType.MEDIA, attachment_data=attachment_data)
        
        # Find media URL field
        media_url_field = None
        for component in modal["components"]:
            text_input = component["components"][0]
            if text_input["custom_id"] == "media_url":
                media_url_field = text_input
                break
        
        assert media_url_field is not None
        assert media_url_field["value"] == attachment_data["url"]
        assert "test.jpg" in media_url_field["placeholder"]

    def test_post_data_extraction_includes_slug(self, handler):
        """Test that PostData extraction includes slug field."""
        # Mock modal submission interaction
        interaction = {
            "data": {
                "custom_id": "post_modal_note",
                "components": [
                    {
                        "components": [{
                            "type": 4,  # TEXT_INPUT
                            "custom_id": "title",
                            "value": "Test Post"
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "content", 
                            "value": "Test content"
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "tags",
                            "value": "test, example"
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "slug",
                            "value": "custom-test-slug"
                        }]
                    }
                ]
            },
            "user": {"id": "987654321098765432"}
        }
        
        post_data = handler.extract_post_data_from_modal(interaction)
        
        assert post_data.title == "Test Post"
        assert post_data.content == "Test content"
        assert post_data.post_type == PostType.NOTE
        assert post_data.slug == "custom-test-slug"
        assert len(post_data.tags) == 2
        assert "test" in post_data.tags
        assert "example" in post_data.tags

    def test_post_data_extraction_empty_slug(self, handler):
        """Test PostData extraction with empty slug field."""
        interaction = {
            "data": {
                "custom_id": "post_modal_note",
                "components": [
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "title",
                            "value": "Test Post"
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "content",
                            "value": "Test content"
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "tags",
                            "value": ""
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "slug",
                            "value": ""  # Empty slug
                        }]
                    }
                ]
            },
            "user": {"id": "987654321098765432"}
        }
        
        post_data = handler.extract_post_data_from_modal(interaction)
        
        assert post_data.slug is None  # Empty string should become None

    def test_media_post_data_extraction(self, handler):
        """Test PostData extraction for media posts."""
        interaction = {
            "data": {
                "custom_id": "post_modal_media",
                "components": [
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "title",
                            "value": "Test Media"
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "content",
                            "value": "Test media content"
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "tags", 
                            "value": "media, test"
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "slug",
                            "value": "test-media-slug"
                        }]
                    },
                    {
                        "components": [{
                            "type": 4,
                            "custom_id": "media_url",
                            "value": "https://example.com/image.jpg"
                        }]
                    }
                ]
            },
            "user": {"id": "987654321098765432"}
        }
        
        post_data = handler.extract_post_data_from_modal(interaction)
        
        assert post_data.title == "Test Media"
        assert post_data.post_type == PostType.MEDIA
        assert post_data.slug == "test-media-slug"
        assert post_data.media_url == "https://example.com/image.jpg"
        assert post_data.media_alt is None  # No alt text from modal in Phase 3
