"""
Test modal integration and field allocation for Phase 2 validation.
"""
import pytest
import inspect
from src.discord_publish_bot.discord.bot import BasePostModal, MediaModal
from src.discord_publish_bot.shared.types import PostType


class TestModalIntegration:
    """Test modal integration without requiring Discord event loop."""
    
    def test_base_post_modal_constructor_signature(self):
        """Test BasePostModal constructor accepts PostType parameter."""
        # Check constructor signature
        sig = inspect.signature(BasePostModal.__init__)
        params = list(sig.parameters.keys())
        
        assert 'bot' in params, "BasePostModal should accept bot parameter"
        assert 'post_type' in params, "BasePostModal should accept post_type parameter"
    
    def test_media_modal_constructor_signature(self):
        """Test MediaModal constructor accepts attachment and alt_text parameters."""
        # Check constructor signature
        sig = inspect.signature(MediaModal.__init__)
        params = list(sig.parameters.keys())
        
        assert 'bot' in params, "MediaModal should accept bot parameter"
        assert 'attachment_url' in params, "MediaModal should accept attachment_url parameter"
        assert 'alt_text' in params, "MediaModal should accept alt_text parameter"
    
    def test_media_modal_inheritance_structure(self):
        """Test MediaModal inheritance and method structure."""
        # Check class hierarchy
        assert hasattr(MediaModal, '_add_type_specific_data'), "MediaModal should have _add_type_specific_data method"
        assert hasattr(MediaModal, 'on_submit'), "MediaModal should have custom on_submit method"
        
        # Check method signatures
        add_data_sig = inspect.signature(MediaModal._add_type_specific_data)
        assert 'post_data' in add_data_sig.parameters, "_add_type_specific_data should accept post_data parameter"
        
        submit_sig = inspect.signature(MediaModal.on_submit)
        assert 'interaction' in submit_sig.parameters, "on_submit should accept interaction parameter"
    
    def test_modal_field_initialization_logic(self):
        """Test modal field initialization logic by examining source code."""
        import ast
        import inspect
        
        # Get MediaModal.__init__ source code
        source = inspect.getsource(MediaModal.__init__)
        
        # Check for conditional field allocation logic
        assert 'command_alt_text' in source, "MediaModal should handle command_alt_text parameter"
        assert 'slug_input' in source, "MediaModal should have slug_input field logic"
        assert 'alt_text_input' in source, "MediaModal should have alt_text_input field logic"
        
        # Check for intelligent field allocation
        assert 'if self.command_alt_text' in source or 'if alt_text' in source, "MediaModal should have conditional field allocation"


class TestPostDataIntegration:
    """Test PostData integration with modal enhancements."""
    
    def test_postdata_slug_field_exists(self):
        """Test PostData model includes slug field."""
        from src.discord_publish_bot.shared.types import PostData
        
        # Check if slug is in the PostData model fields using Pydantic
        model_fields = PostData.model_fields
        assert 'slug' in model_fields, f"PostData should have slug field, found: {list(model_fields.keys())}"
        
        # Check that slug field is optional
        slug_field = model_fields['slug']
        assert slug_field.default is None, "PostData slug field should default to None"
        
        # Test optional slug creation
        post_data = PostData(
            title="Test Post",
            content="Test content",
            post_type=PostType.NOTE,
            created_by="test_user"
        )
        assert hasattr(post_data, 'slug'), "PostData instance should have slug attribute"
        assert post_data.slug is None, "PostData slug should be optional"
        
        # Test with slug
        post_data_with_slug = PostData(
            title="Test Post",
            content="Test content", 
            post_type=PostType.NOTE,
            created_by="test_user",
            slug="custom-slug"
        )
        assert post_data_with_slug.slug == "custom-slug", "PostData should accept custom slug"


class TestUtilsIntegration:
    """Test utils integration with slug functionality."""
    
    def test_generate_filename_slug_priority(self):
        """Test generate_filename prioritizes slug over title."""
        from src.discord_publish_bot.shared.utils import generate_filename
        from src.discord_publish_bot.shared.types import PostType
        
        # Test slug priority
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Long Title That Should Not Be Used",
            slug="custom-slug"
        )
        
        assert "custom-slug" in filename, "generate_filename should use slug when available"
        assert "Long Title" not in filename, "generate_filename should not use title when slug available"
    
    def test_generate_filename_fallback_to_title(self):
        """Test generate_filename falls back to title when no slug."""
        from src.discord_publish_bot.shared.utils import generate_filename
        from src.discord_publish_bot.shared.types import PostType
        
        # Test title fallback
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Test Post Title"
        )
        
        assert "test-post-title" in filename, "generate_filename should use title when no slug"


class TestBackwardsCompatibility:
    """Test backwards compatibility of modal changes."""
    
    def test_postdata_backwards_compatibility(self):
        """Test PostData backwards compatibility without slug."""
        from src.discord_publish_bot.shared.types import PostData
        
        # Old PostData creation should still work
        old_style_post = PostData(
            title="Test Post",
            content="Test content",
            post_type=PostType.NOTE,
            created_by="test_user"
            # No slug field
        )
        
        assert old_style_post.title == "Test Post"
        assert hasattr(old_style_post, 'slug'), "PostData should have slug attribute"
        assert old_style_post.slug is None, "PostData should default slug to None"
    
    def test_filename_generation_backwards_compatibility(self):
        """Test filename generation works with old-style calls."""
        from src.discord_publish_bot.shared.utils import generate_filename
        from src.discord_publish_bot.shared.types import PostType
        
        # Old-style filename generation
        filename = generate_filename(
            post_type=PostType.NOTE,
            title="Old Style Post"
        )
        
        assert filename is not None, "generate_filename should work with old signature"
        assert "old-style-post" in filename, "Should generate filename from title"
