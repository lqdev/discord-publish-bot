"""
Test script for Discord HTTP interactions bot.

Tests the new serverless Discord bot implementation.
"""

import json
import asyncio
import os
from dotenv import load_dotenv
import sys
import hmac
import hashlib
from datetime import datetime
import requests

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from discord_interactions.config import DiscordConfig
from discord_interactions.bot import DiscordInteractionsBot

load_dotenv()


def test_config_validation():
    """Test Discord configuration validation."""
    print("🔧 Testing Discord configuration...")
    
    config = DiscordConfig.from_env()
    is_valid, errors = config.validate()
    
    if is_valid:
        print("✅ Discord configuration is valid")
        return config
    else:
        print("❌ Discord configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return None


def test_bot_initialization():
    """Test Discord bot initialization."""
    print("\n🤖 Testing bot initialization...")
    
    config = test_config_validation()
    if not config:
        return None
    
    try:
        bot = DiscordInteractionsBot(config)
        print("✅ Discord bot initialized successfully")
        return bot
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return None


def create_test_interaction(interaction_type: int = 1, command_name: str = None, 
                          user_id: str = None, options: list = None) -> dict:
    """Create test interaction payload."""
    
    # Use configured user ID or test ID
    if not user_id:
        config = DiscordConfig.from_env()
        user_id = config.authorized_user_id or "123456789"
    
    interaction = {
        "type": interaction_type,
        "id": "test_interaction_id",
        "application_id": "test_app_id",
        "token": "test_token",
        "version": 1
    }
    
    if interaction_type == 1:  # PING
        return interaction
    
    if interaction_type == 2:  # APPLICATION_COMMAND
        interaction["data"] = {
            "id": "test_command_id",
            "name": command_name or "ping",
            "type": 1
        }
        
        if options:
            interaction["data"]["options"] = options
        
        interaction["member"] = {
            "user": {
                "id": user_id,
                "username": "testuser"
            }
        }
    
    if interaction_type == 5:  # MODAL_SUBMIT
        interaction["data"] = {
            "custom_id": "post_modal_note",
            "components": [
                {
                    "type": 1,  # ACTION_ROW
                    "components": [{
                        "type": 4,  # TEXT_INPUT
                        "custom_id": "title",
                        "value": "Test Note Title"
                    }]
                },
                {
                    "type": 1,  # ACTION_ROW
                    "components": [{
                        "type": 4,  # TEXT_INPUT
                        "custom_id": "content",
                        "value": "This is test content for a note post."
                    }]
                },
                {
                    "type": 1,  # ACTION_ROW
                    "components": [{
                        "type": 4,  # TEXT_INPUT
                        "custom_id": "tags",
                        "value": "test, automation"
                    }]
                }
            ]
        }
        
        interaction["member"] = {
            "user": {
                "id": user_id,
                "username": "testuser"
            }
        }
    
    return interaction


def test_ping_interaction():
    """Test ping interaction handling."""
    print("\n🏓 Testing ping interaction...")
    
    bot = test_bot_initialization()
    if not bot:
        return False
    
    # Test PING interaction
    ping_interaction = create_test_interaction(1)  # PING type
    response = bot.handle_interaction(ping_interaction)
    
    if response.get("type") == 1:  # PONG
        print("✅ Ping interaction handled correctly")
        return True
    else:
        print(f"❌ Unexpected ping response: {response}")
        return False


def test_slash_commands():
    """Test slash command handling."""
    print("\n⚡ Testing slash commands...")
    
    bot = test_bot_initialization()
    if not bot:
        return False
    
    # Test ping command
    ping_cmd = create_test_interaction(2, "ping")  # APPLICATION_COMMAND
    response = bot.handle_interaction(ping_cmd)
    
    if response.get("type") == 4:  # CHANNEL_MESSAGE_WITH_SOURCE
        print("✅ Ping command handled correctly")
    else:
        print(f"❌ Unexpected ping command response: {response}")
        return False
    
    # Test post command
    post_cmd = create_test_interaction(2, "post", options=[
        {"name": "type", "value": "note"}
    ])
    response = bot.handle_interaction(post_cmd)
    
    if response.get("type") == 9:  # MODAL
        print("✅ Post command shows modal correctly")
        return True
    else:
        print(f"❌ Unexpected post command response: {response}")
        return False


def test_modal_submission():
    """Test modal submission handling."""
    print("\n📝 Testing modal submission...")
    
    bot = test_bot_initialization()
    if not bot:
        return False
    
    # Test modal submit
    modal_submit = create_test_interaction(5)  # MODAL_SUBMIT
    response = bot.handle_interaction(modal_submit)
    
    if response.get("type") == 5:  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
        print("✅ Modal submission deferred correctly")
        return True
    else:
        print(f"❌ Unexpected modal response: {response}")
        return False


def test_authorization():
    """Test user authorization."""
    print("\n🔒 Testing authorization...")
    
    bot = test_bot_initialization()
    if not bot:
        return False
    
    # Test unauthorized user
    unauth_cmd = create_test_interaction(2, "ping", user_id="unauthorized_user")
    response = bot.handle_interaction(unauth_cmd)
    
    if "not authorized" in response.get("data", {}).get("content", "").lower():
        print("✅ Unauthorized user blocked correctly")
        return True
    else:
        print(f"❌ Authorization test failed: {response}")
        return False


def test_combined_app_health():
    """Test combined app health endpoint."""
    print("\n🏥 Testing combined app health...")
    
    try:
        # Try to import and test the combined app
        from combined_app import app
        print("✅ Combined app imports successfully")
        
        # Could add more detailed testing here if needed
        return True
    except ImportError as e:
        print(f"❌ Combined app import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Combined app test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Discord HTTP Interactions Bot - Test Suite")
    print("=" * 50)
    
    tests = [
        test_config_validation,
        test_bot_initialization,
        test_ping_interaction,
        test_slash_commands,
        test_modal_submission,
        test_authorization,
        test_combined_app_health
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Discord HTTP interactions are ready for deployment.")
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
