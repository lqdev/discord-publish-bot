"""
Test script for Discord HTTP interactions bot - Configuration Independent Version

Tests the new serverless Discord bot implementation without requiring full Discord configuration.
"""

import json
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_import_structure():
    """Test that all modules can be imported."""
    print("📦 Testing module imports...")
    
    try:
        from discord_interactions.config import DiscordConfig
        print("✅ discord_interactions.config imported")
    except ImportError as e:
        print(f"❌ Failed to import discord_interactions.config: {e}")
        return False
    
    try:
        from discord_interactions.bot import DiscordInteractionsBot, InteractionType, InteractionResponseType
        print("✅ discord_interactions.bot imported")
    except ImportError as e:
        print(f"❌ Failed to import discord_interactions.bot: {e}")
        return False
    
    try:
        from discord_interactions.api_client import InteractionsAPIClient, PostData
        print("✅ discord_interactions.api_client imported")
    except ImportError as e:
        print(f"❌ Failed to import discord_interactions.api_client: {e}")
        return False
    
    try:
        from combined_app import app
        print("✅ combined_app imported")
    except ImportError as e:
        print(f"❌ Failed to import combined_app: {e}")
        return False
    
    return True


def test_bot_with_mock_config():
    """Test bot functionality with mock configuration."""
    print("\n🤖 Testing bot with mock configuration...")
    
    try:
        from discord_interactions.config import DiscordConfig
        from discord_interactions.bot import DiscordInteractionsBot
        
        # Create mock configuration
        mock_config = DiscordConfig(
            application_id="123456789",
            public_key="a" * 64,  # 64-character hex string
            bot_token="mock_token",
            authorized_user_id="test_user_123",
            publishing_api_endpoint="http://localhost:8000",
            api_key="test_api_key"
        )
        
        # Try to initialize bot
        bot = DiscordInteractionsBot(mock_config)
        print("✅ Bot initialized with mock config")
        return bot
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return None


def test_interaction_handling():
    """Test interaction handling logic."""
    print("\n⚡ Testing interaction handling...")
    
    bot = test_bot_with_mock_config()
    if not bot:
        return False
    
    # Test PING interaction
    ping_interaction = {
        "type": 1  # PING
    }
    
    response = bot.handle_interaction(ping_interaction)
    if response.get("type") == 1:  # PONG
        print("✅ PING interaction handled correctly")
    else:
        print(f"❌ PING response incorrect: {response}")
        return False
    
    # Test authorized command
    authorized_command = {
        "type": 2,  # APPLICATION_COMMAND
        "data": {
            "name": "ping"
        },
        "member": {
            "user": {
                "id": "test_user_123"  # Matches authorized user
            }
        }
    }
    
    response = bot.handle_interaction(authorized_command)
    if response.get("type") == 4:  # CHANNEL_MESSAGE_WITH_SOURCE
        print("✅ Authorized command handled correctly")
    else:
        print(f"❌ Authorized command response incorrect: {response}")
        return False
    
    # Test unauthorized command
    unauthorized_command = {
        "type": 2,  # APPLICATION_COMMAND
        "data": {
            "name": "ping"
        },
        "member": {
            "user": {
                "id": "unauthorized_user"
            }
        }
    }
    
    response = bot.handle_interaction(unauthorized_command)
    content = response.get("data", {}).get("content", "")
    if "not authorized" in content.lower():
        print("✅ Unauthorized user blocked correctly")
    else:
        print(f"❌ Unauthorized user not blocked: {response}")
        return False
    
    return True


def test_modal_creation():
    """Test modal creation for different post types."""
    print("\n📝 Testing modal creation...")
    
    bot = test_bot_with_mock_config()
    if not bot:
        return False
    
    post_types = ["note", "response", "bookmark", "media"]
    
    for post_type in post_types:
        try:
            modal = bot._create_post_modal(post_type)
            
            # Validate modal structure
            if not isinstance(modal, dict):
                print(f"❌ Modal for {post_type} is not a dict")
                return False
            
            if "custom_id" not in modal or "title" not in modal or "components" not in modal:
                print(f"❌ Modal for {post_type} missing required fields")
                return False
            
            if not modal["custom_id"].endswith(post_type):
                print(f"❌ Modal for {post_type} has incorrect custom_id")
                return False
            
            print(f"✅ Modal for {post_type} created correctly")
            
        except Exception as e:
            print(f"❌ Modal creation for {post_type} failed: {e}")
            return False
    
    return True


def test_post_data_structure():
    """Test PostData structure."""
    print("\n📊 Testing PostData structure...")
    
    try:
        from discord_interactions.api_client import PostData
        
        # Test basic post data
        post_data = PostData(
            title="Test Title",
            content="Test Content",
            post_type="note",
            tags="test, automation"
        )
        
        if post_data.title == "Test Title" and post_data.post_type == "note":
            print("✅ PostData structure works correctly")
            return True
        else:
            print("❌ PostData fields not accessible")
            return False
            
    except Exception as e:
        print(f"❌ PostData test failed: {e}")
        return False


def test_fastapi_app_structure():
    """Test FastAPI app can be accessed."""
    print("\n🌐 Testing FastAPI app structure...")
    
    try:
        from combined_app import app
        
        # Check that it's a FastAPI instance
        if hasattr(app, 'routes'):
            print("✅ FastAPI app has routes")
        else:
            print("❌ FastAPI app missing routes")
            return False
        
        # Check for expected routes
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        
        expected_paths = ["/", "/health", "/discord/interactions"]
        for path in expected_paths:
            if path in route_paths:
                print(f"✅ Route {path} found")
            else:
                print(f"❌ Route {path} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        return False


def test_dependencies():
    """Test that required dependencies are available."""
    print("\n📋 Testing dependencies...")
    
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"), 
        ("pynacl", "nacl"),
        ("aiohttp", "aiohttp"),
        ("python-dotenv", "dotenv")
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} available")
        except ImportError:
            print(f"❌ {package_name} missing")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: uv sync")
        return False
    
    return True


def main():
    """Run all tests."""
    print("🧪 Discord HTTP Interactions Bot - Configuration Independent Tests")
    print("=" * 70)
    
    tests = [
        test_dependencies,
        test_import_structure,
        test_bot_with_mock_config,
        test_interaction_handling,
        test_modal_creation,
        test_post_data_structure,
        test_fastapi_app_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                break  # Stop on first failure for easier debugging
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            break
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Discord HTTP interactions implementation is ready.")
        print("\n📋 Next Steps:")
        print("1. Set up Discord application and get DISCORD_APPLICATION_ID, DISCORD_PUBLIC_KEY")
        print("2. Configure environment variables")
        print("3. Deploy to Azure Container Apps")
        print("4. Register Discord webhook endpoint")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
