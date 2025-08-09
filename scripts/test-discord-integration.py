#!/usr/bin/env python3
"""
Discord Bot Integration Test

Tests the Discord bot with mock interactions to verify modal functionality.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from discord_bot.main import create_bot
from discord_bot.modals import NoteModal
from discord_bot.api_client import PublishingAPIClient

load_dotenv()

class MockInteraction:
    """Mock Discord interaction for testing."""
    
    def __init__(self, user_id: str):
        self.user = MagicMock()
        self.user.id = int(user_id)
        self.response = AsyncMock()
        self.followup = AsyncMock()

class MockTextInput:
    """Mock Discord TextInput for testing."""
    
    def __init__(self, value: str):
        self.value = value
    
    def strip(self):
        return self.value.strip()
    
    def lower(self):
        return self.value.lower()
    
    def split(self, sep=None):
        return self.value.split(sep)

async def test_bot_initialization():
    """Test that the bot initializes correctly."""
    print("🤖 Testing Bot Initialization")
    print("=" * 40)
    
    try:
        bot = create_bot()
        
        print(f"✅ Bot created successfully")
        print(f"📝 Bot user ID configured: {bot.config.discord_user_id}")
        print(f"🔗 API endpoint: {bot.config.fastapi_endpoint}")
        
        # Test authorization check
        authorized_user = int(bot.config.discord_user_id)
        unauthorized_user = 123456789
        
        assert bot.is_authorized(authorized_user) == True
        assert bot.is_authorized(unauthorized_user) == False
        
        print("✅ Authorization checks working")
        
        # Clean up
        await bot.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_note_modal():
    """Test the note modal functionality."""
    print("\n📝 Testing Note Modal")
    print("=" * 30)
    
    try:
        # Create mock API client that returns success
        api_client = MagicMock()
        api_client.publish_post = AsyncMock(return_value=(True, {
            "filepath": "posts/notes/2025-08-09-test-modal-note.md",
            "commit_sha": "abc123def456",
            "site_url": "https://example.com/posts/notes/test-modal-note"
        }))
        
        # Create note modal
        modal = NoteModal(api_client)
        
        # Mock text inputs
        modal.content = MockTextInput("This is a **test note** from the modal.\n\n- Item 1\n- Item 2")
        modal.title = MockTextInput("Test Modal Note")
        modal.tags = MockTextInput("test, modal, automation")
        
        # Create mock interaction
        user_id = os.getenv("DISCORD_USER_ID", "727687304596160593")
        interaction = MockInteraction(user_id)
        
        # Test submission
        await modal.on_submit(interaction)
        
        # Verify API was called
        api_client.publish_post.assert_called_once()
        
        # Check the message format
        call_args = api_client.publish_post.call_args
        message = call_args[1]['message']
        user_id_param = call_args[1]['user_id']
        
        print("📤 Generated message:")
        print("-" * 20)
        print(message)
        print("-" * 20)
        
        # Verify message structure
        assert message.startswith("/post note")
        assert "title: Test Modal Note" in message
        assert "tags: [" in message
        assert "This is a **test note** from the modal." in message
        
        print("✅ Note modal test passed")
        return True
        
    except Exception as e:
        print(f"❌ Note modal test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_client():
    """Test the API client functionality."""
    print("\n🔗 Testing API Client")
    print("=" * 25)
    
    try:
        from discord_bot.config import BotConfig
        
        config = BotConfig.from_env()
        api_client = PublishingAPIClient(config.fastapi_endpoint, config.api_key)
        
        # Test health check (this should work even if publishing API isn't running)
        print("🏥 Testing health check...")
        
        # Note: This will fail if publishing API isn't running, which is expected
        try:
            health = await api_client.check_health()
            print(f"✅ Health check returned: {health}")
        except Exception as e:
            print(f"⚠️ Health check failed (expected if API not running): {str(e)}")
        
        # Test client creation
        print("✅ API client created successfully")
        print(f"🔗 Endpoint: {api_client.base_url}")
        
        # Clean up
        await api_client.close()
        
        return True
        
    except Exception as e:
        print(f"❌ API client test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_all_modals():
    """Test all modal types."""
    print("\n📋 Testing All Modal Types")
    print("=" * 35)
    
    try:
        from discord_bot.modals import ResponseModal, BookmarkModal, MediaModal
        
        # Mock API client
        api_client = MagicMock()
        api_client.publish_post = AsyncMock(return_value=(True, {
            "filepath": "posts/test/test.md",
            "commit_sha": "abc123",
            "site_url": "https://example.com/test"
        }))
        
        user_id = os.getenv("DISCORD_USER_ID", "727687304596160593")
        interaction = MockInteraction(user_id)
        
        # Test Response Modal
        print("1. Testing Response Modal...")
        response_modal = ResponseModal(api_client)
        response_modal.response_type = MockTextInput("reply")
        response_modal.content = MockTextInput("This is my response to the original post.")
        response_modal.original_url = MockTextInput("https://example.com/original")
        
        await response_modal.on_submit(interaction)
        print("   ✅ Response modal worked")
        
        # Test Bookmark Modal
        print("2. Testing Bookmark Modal...")
        bookmark_modal = BookmarkModal(api_client)
        bookmark_modal.url = MockTextInput("https://example.com/interesting-article")
        bookmark_modal.title = MockTextInput("Interesting Article")
        bookmark_modal.notes = MockTextInput("Found this article really insightful.")
        bookmark_modal.tags = MockTextInput("article, learning, web")
        
        await bookmark_modal.on_submit(interaction)
        print("   ✅ Bookmark modal worked")
        
        # Test Media Modal
        print("3. Testing Media Modal...")
        media_modal = MediaModal(api_client)
        media_modal.media_url = MockTextInput("https://example.com/image.jpg")
        media_modal.caption = MockTextInput("A beautiful sunset photo I took today.")
        media_modal.alt_text = MockTextInput("Sunset over the ocean")
        media_modal.tags = MockTextInput("photo, sunset, nature")
        
        await media_modal.on_submit(interaction)
        print("   ✅ Media modal worked")
        
        print("✅ All modal types tested successfully")
        return True
        
    except Exception as e:
        print(f"❌ Modal testing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner."""
    print("🧪 Discord Bot Integration Testing")
    print("=" * 50)
    
    tests = [
        ("Bot Initialization", test_bot_initialization),
        ("API Client", test_api_client),
        ("Note Modal", test_note_modal),
        ("All Modals", test_all_modals),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Discord bot is ready.")
        return 0
    else:
        print("💥 Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
