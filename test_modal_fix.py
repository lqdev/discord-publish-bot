#!/usr/bin/env python3
"""
Quick test script to validate the modal routing fix.
"""

from src.discord_publish_bot.discord.interactions import DiscordInteractionsHandler
from src.discord_publish_bot.config import DiscordSettings
from src.discord_publish_bot.shared import PostType


def test_modal_routing():
    """Test that modals are created correctly for each post type."""
    settings = DiscordSettings(
        bot_token="MTIzNDU2NzgxMjM0NTY3ODEyLkdXUUhVVy5fRGhYa2l5QWZVc2R3LXFNYnhhTW92RGdjWVZvZ3J0YnczUQ",  # Valid format
        application_id="1234567812345678912",  # Valid numeric format
        public_key="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",  # Valid hex format
        authorized_user_id="123456789012345678"  # Valid numeric format
    )
    
    handler = DiscordInteractionsHandler(settings)
    
    # Test each post type
    test_cases = [
        (PostType.NOTE, "Create Note Post", 3),  # 3 fields: title, content, tags
        (PostType.RESPONSE, "Create Response Post", 4),  # 4 fields: title, content, tags, target_url  
        (PostType.BOOKMARK, "Create Bookmark Post", 4),  # 4 fields: title, content, tags, target_url
        (PostType.MEDIA, "Create Media Post", 4),  # 4 fields: title, content, tags, media_url
    ]
    
    for post_type, expected_title, expected_fields in test_cases:
        modal = handler._create_post_modal(post_type)
        
        # Check title
        assert modal["title"] == expected_title, f"Wrong title for {post_type}: {modal['title']}"
        
        # Check custom_id
        expected_custom_id = f"post_modal_{post_type.value}"
        assert modal["custom_id"] == expected_custom_id, f"Wrong custom_id for {post_type}: {modal['custom_id']}"
        
        # Check field count
        assert len(modal["components"]) == expected_fields, f"Wrong field count for {post_type}: {len(modal['components'])} (expected {expected_fields})"
        
        print(f"✅ {post_type.value.title()} modal: {modal['title']} with {len(modal['components'])} fields")
    
    print("\n🎉 All modal routing tests passed!")


def test_post_command_parameter_parsing():
    """Test that post_type parameter is correctly parsed from Discord interactions."""
    settings = DiscordSettings(
        bot_token="MTIzNDU2NzgxMjM0NTY3ODEyLkdXUUhVVy5fRGhYa2l5QWZVc2R3LXFNYnhhTW92RGdjWVZvZ3J0YnczUQ",  # Valid format
        application_id="1234567812345678912",  # Valid numeric format
        public_key="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",  # Valid hex format
        authorized_user_id="123456789012345678"  # Valid numeric format
    )
    
    handler = DiscordInteractionsHandler(settings)
    
    # Test interactions for each post type
    test_interactions = [
        {
            "data": {
                "options": [{"name": "post_type", "value": "note"}]
            }
        },
        {
            "data": {
                "options": [{"name": "post_type", "value": "response"}]
            }
        },
        {
            "data": {
                "options": [{"name": "post_type", "value": "bookmark"}]
            }
        },
        {
            "data": {
                "options": [{"name": "post_type", "value": "media"}]
            }
        }
    ]
    
    expected_titles = [
        "Create Note Post",
        "Create Response Post", 
        "Create Bookmark Post",
        "Create Media Post"
    ]
    
    for interaction, expected_title in zip(test_interactions, expected_titles):
        try:
            response = handler._handle_post_command(interaction)
            modal = response["data"]
            actual_title = modal["title"]
            
            assert actual_title == expected_title, f"Expected '{expected_title}', got '{actual_title}'"
            print(f"✅ Parameter parsing: {interaction['data']['options'][0]['value']} → {actual_title}")
            
        except Exception as e:
            print(f"❌ Failed for {interaction}: {e}")
            raise
    
    print("\n🎉 All parameter parsing tests passed!")


if __name__ == "__main__":
    test_modal_routing()
    test_post_command_parameter_parsing()
    print("\n🎯 Modal fix validation complete!")
