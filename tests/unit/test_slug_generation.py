"""
Unit tests for slug generation functionality.

Tests the enhanced generate_filename function with slug priority logic.
"""

import pytest
from datetime import datetime

from src.discord_publish_bot.shared.types import PostType
from src.discord_publish_bot.shared.utils import generate_filename, slugify


class TestSlugGeneration:
    """Test slug generation and filename creation with custom slug support."""

    def test_slug_priority_over_title(self):
        """Test that custom slug takes priority over title-based generation."""
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="This is a Very Long Title That Would Generate a Long Slug",
            slug="custom-short-slug"
        )
        assert filename == "custom-short-slug.md"

    def test_slug_fallback_to_title(self):
        """Test fallback to title when slug is empty or None."""
        # Test with None slug
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title",
            slug=None
        )
        assert filename == "test-title.md"
        
        # Test with empty slug
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title",
            slug=""
        )
        assert filename == "test-title.md"
        
        # Test with whitespace-only slug
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title",
            slug="   "
        )
        assert filename == "test-title.md"

    def test_slug_sanitization(self):
        """Test that slug is properly sanitized using slugify function."""
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title",
            slug="Custom Slug with Spaces & Special Characters!"
        )
        assert filename == "custom-slug-with-spaces-special-characters.md"

    def test_slug_length_limit(self):
        """Test that slug respects max length limit."""
        very_long_slug = "a" * 100  # 100 characters
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title",
            slug=very_long_slug
        )
        # Should be truncated to 80 characters + .md
        assert len(filename) == 83  # 80 + ".md"
        assert filename.endswith(".md")
        assert filename.startswith("a")

    def test_slug_with_different_post_types(self):
        """Test slug generation works with all post types."""
        test_cases = [
            (PostType.NOTE, "note-slug"),
            (PostType.RESPONSE, "response-slug"),
            (PostType.BOOKMARK, "bookmark-slug"),
            (PostType.MEDIA, "media-slug"),
        ]
        
        for post_type, expected_slug in test_cases:
            filename = generate_filename(
                post_type=post_type,
                title="Test Title",
                slug=expected_slug
            )
            assert filename == f"{expected_slug}.md"

    def test_backwards_compatibility(self):
        """Test that existing code calling without slug parameter still works."""
        # Test old signature compatibility
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title"
        )
        assert filename == "test-title.md"
        
        # Test with timestamp parameter (should be ignored)
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title",
            timestamp=datetime.now()
        )
        assert filename == "test-title.md"

    def test_unicode_slug_handling(self):
        """Test handling of unicode characters in slugs."""
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title",
            slug="Café & Résumé with Unicode"
        )
        # Unicode should be normalized and special chars removed
        assert filename == "cafe-resume-with-unicode.md"

    def test_edge_cases(self):
        """Test various edge cases for slug generation."""
        # Slug with only special characters
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Fallback Title",
            slug="!@#$%^&*()"
        )
        # Should fall back to title since slug becomes empty after sanitization
        assert filename == "fallback-title.md"
        
        # Slug with numbers and hyphens
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title",
            slug="test-123-slug-456"
        )
        assert filename == "test-123-slug-456.md"
        
        # Slug that starts/ends with hyphens
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Title",
            slug="-hyphen-test-"
        )
        # Slugify should remove leading/trailing hyphens
        assert filename == "hyphen-test.md"


class TestSlugifyFunction:
    """Test the slugify utility function that supports slug generation."""

    def test_basic_slugification(self):
        """Test basic text to slug conversion."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test Title Here") == "test-title-here"

    def test_special_character_removal(self):
        """Test removal of special characters."""
        assert slugify("Hello, World!") == "hello-world"
        assert slugify("Test & Title @ Here") == "test-title-here"
        assert slugify("Price: $19.99") == "price-1999"

    def test_unicode_normalization(self):
        """Test unicode character normalization."""
        assert slugify("Café") == "cafe"
        assert slugify("Résumé") == "resume"
        assert slugify("Naïve") == "naive"

    def test_multiple_spaces_and_hyphens(self):
        """Test consolidation of multiple spaces and hyphens."""
        assert slugify("Hello   World") == "hello-world"
        assert slugify("Test--Title") == "test-title"
        assert slugify("Hello   --   World") == "hello-world"

    def test_length_limiting(self):
        """Test max length parameter."""
        long_text = "This is a very long title that exceeds the maximum length"
        result = slugify(long_text, max_length=20)
        assert len(result) <= 20
        assert not result.endswith("-")  # Should not end with hyphen

    def test_empty_and_whitespace(self):
        """Test handling of empty strings and whitespace."""
        assert slugify("") == ""
        assert slugify("   ") == ""
        assert slugify("!!!") == ""  # Only special chars

    def test_numbers_and_mixed_content(self):
        """Test handling of numbers and mixed content."""
        assert slugify("Version 2.0 Release") == "version-20-release"
        assert slugify("COVID-19 Update") == "covid-19-update"
        assert slugify("123 Test 456") == "123-test-456"


class TestSlugIntegration:
    """Integration tests for slug functionality across the system."""

    def test_postdata_slug_field(self):
        """Test that PostData model accepts slug field."""
        from src.discord_publish_bot.shared.types import PostData
        
        post_data = PostData(
            title="Test Title",
            content="Test content",
            post_type=PostType.NOTE,
            slug="custom-slug"
        )
        
        assert post_data.slug == "custom-slug"
        assert post_data.title == "Test Title"

    def test_postdata_optional_slug(self):
        """Test that slug field is optional in PostData."""
        from src.discord_publish_bot.shared.types import PostData
        
        post_data = PostData(
            title="Test Title",
            content="Test content",
            post_type=PostType.NOTE
            # No slug provided
        )
        
        assert post_data.slug is None

    def test_filename_generation_with_postdata(self):
        """Test filename generation using data from PostData model."""
        from src.discord_publish_bot.shared.types import PostData
        
        # Test with custom slug
        post_data = PostData(
            title="Original Title",
            content="Test content",
            post_type=PostType.NOTE,
            slug="custom-filename"
        )
        
        filename = generate_filename(
            post_type=post_data.post_type,
            title=post_data.title,
            slug=post_data.slug
        )
        assert filename == "custom-filename.md"
        
        # Test without custom slug
        post_data_no_slug = PostData(
            title="Original Title",
            content="Test content",
            post_type=PostType.NOTE
        )
        
        filename = generate_filename(
            post_type=post_data_no_slug.post_type,
            title=post_data_no_slug.title,
            slug=post_data_no_slug.slug
        )
        assert filename == "original-title.md"
