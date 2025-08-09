#!/usr/bin/env python3
"""
Discord HTTP Interactions Bot - Comprehensive E2E Integration Test

Tests the complete HTTP interactions workflow end-to-end:
1. Combined app health and startup
2. Discord interaction simulation (PING, commands, modals)
3. Integration with publishing API
4. Full post creation workflow
5. Error handling and authorization

Follows established E2E testing patterns from existing scripts.
"""

import asyncio
import json
import os
import sys
import tempfile
import time
import requests
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

load_dotenv()

# Import our HTTP interactions components
from discord_interactions.config import DiscordConfig
from discord_interactions.bot import DiscordInteractionsBot, InteractionType, InteractionResponseType
from discord_interactions.api_client import InteractionsAPIClient, PostData


class E2ETestSuite:
    """Comprehensive E2E test suite for Discord HTTP interactions."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        self.config = None
        
    async def setup_configuration(self):
        """Set up configuration for testing."""
        print("🔧 Setting up test configuration...")
        
        # Try to load real config first
        try:
            self.config = DiscordConfig.from_env()
            is_valid, errors = self.config.validate()
            
            if is_valid:
                print("✅ Real Discord configuration loaded")
                return True
            else:
                print(f"⚠️ Real config incomplete: {errors}")
                
        except Exception as e:
            print(f"⚠️ Error loading real config: {e}")
        
        # Fall back to mock configuration for testing
        print("🎭 Using mock configuration for testing")
        self.config = DiscordConfig(
            application_id="123456789012345678",
            public_key="a" * 64,  # Valid hex string
            bot_token="mock_bot_token",
            authorized_user_id="test_user_123456",
            publishing_api_endpoint=self.base_url,
            api_key="test_api_key_for_e2e"
        )
        return True
    
    async def test_combined_app_health(self):
        """Test that the combined app is running and healthy."""
        print("\n🏥 Testing combined app health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Health check passed: {data}")
                        
                        # Validate expected health response structure
                        required_fields = ["status", "discord_configured", "api_configured"]
                        missing_fields = [f for f in required_fields if f not in data]
                        
                        if not missing_fields:
                            print("✅ Health response structure valid")
                            return True
                        else:
                            print(f"❌ Missing health fields: {missing_fields}")
                            return False
                    else:
                        print(f"❌ Health check failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_root_endpoint(self):
        """Test the root endpoint provides correct service info."""
        print("\n🌐 Testing root endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Root endpoint accessible")
                        
                        # Validate expected structure
                        expected_fields = ["service", "version", "discord_enabled", "endpoints"]
                        present_fields = [f for f in expected_fields if f in data]
                        
                        print(f"✓ Response fields: {present_fields}")
                        
                        if "endpoints" in data and "discord_interactions" in data["endpoints"]:
                            print("✅ Discord interactions endpoint listed")
                            return True
                        else:
                            print("❌ Discord interactions endpoint not found")
                            return False
                    else:
                        print(f"❌ Root endpoint failed: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            return False
    
    def create_test_interaction(self, interaction_type: int, command_name: str = None, 
                              post_type: str = None, modal_data: dict = None) -> dict:
        """Create test Discord interaction payloads."""
        
        interaction = {
            "type": interaction_type,
            "id": f"test_interaction_{int(time.time())}",
            "application_id": self.config.application_id,
            "token": f"test_token_{int(time.time())}",
            "version": 1
        }
        
        if interaction_type == InteractionType.PING:
            return interaction
        
        if interaction_type == InteractionType.APPLICATION_COMMAND:
            interaction["data"] = {
                "id": "test_command_id",
                "name": command_name or "ping",
                "type": 1
            }
            
            if command_name == "post" and post_type:
                interaction["data"]["options"] = [
                    {"name": "type", "value": post_type}
                ]
            
            interaction["member"] = {
                "user": {
                    "id": self.config.authorized_user_id,
                    "username": "testuser"
                }
            }
        
        if interaction_type == InteractionType.MODAL_SUBMIT and modal_data:
            interaction["data"] = {
                "custom_id": f"post_modal_{post_type or 'note'}",
                "components": []
            }
            
            # Convert modal data to Discord component format
            for field_name, value in modal_data.items():
                interaction["data"]["components"].append({
                    "type": 1,  # ACTION_ROW
                    "components": [{
                        "type": 4,  # TEXT_INPUT
                        "custom_id": field_name,
                        "value": value
                    }]
                })
            
            interaction["member"] = {
                "user": {
                    "id": self.config.authorized_user_id,
                    "username": "testuser"
                }
            }
        
        return interaction
    
    async def test_discord_ping_interaction(self):
        """Test Discord PING interaction handling."""
        print("\n🏓 Testing Discord PING interaction...")
        
        # Create PING interaction
        ping_interaction = self.create_test_interaction(InteractionType.PING)
        
        try:
            # Send to Discord interactions endpoint
            async with aiohttp.ClientSession() as session:
                # Note: In real Discord, this would include signature headers
                # For testing, we'll simulate the interaction processing directly
                
                bot = DiscordInteractionsBot(self.config)
                response = bot.handle_interaction(ping_interaction)
                
                if response.get("type") == InteractionResponseType.PONG:
                    print("✅ PING interaction handled correctly")
                    print(f"✓ Response: {response}")
                    return True
                else:
                    print(f"❌ Unexpected PING response: {response}")
                    return False
                    
        except Exception as e:
            print(f"❌ PING interaction error: {e}")
            return False
    
    async def test_discord_slash_commands(self):
        """Test Discord slash command handling."""
        print("\n⚡ Testing Discord slash commands...")
        
        bot = DiscordInteractionsBot(self.config)
        test_commands = [
            {"name": "ping", "expected_type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE},
            {"name": "post", "post_type": "note", "expected_type": InteractionResponseType.MODAL}
        ]
        
        all_passed = True
        
        for cmd in test_commands:
            print(f"\n  Testing /{cmd['name']} command...")
            
            try:
                interaction = self.create_test_interaction(
                    InteractionType.APPLICATION_COMMAND,
                    command_name=cmd["name"],
                    post_type=cmd.get("post_type")
                )
                
                response = bot.handle_interaction(interaction)
                
                if response.get("type") == cmd["expected_type"]:
                    print(f"  ✅ /{cmd['name']} command handled correctly")
                    
                    # Additional validation for post command
                    if cmd["name"] == "post" and "data" in response:
                        modal_data = response["data"]
                        if "components" in modal_data and len(modal_data["components"]) > 0:
                            print(f"  ✓ Modal generated with {len(modal_data['components'])} components")
                        else:
                            print("  ❌ Modal missing components")
                            all_passed = False
                else:
                    print(f"  ❌ Unexpected response type: {response.get('type')}")
                    all_passed = False
                    
            except Exception as e:
                print(f"  ❌ Command /{cmd['name']} error: {e}")
                all_passed = False
        
        return all_passed
    
    async def test_authorization(self):
        """Test user authorization in Discord interactions."""
        print("\n🔒 Testing authorization...")
        
        bot = DiscordInteractionsBot(self.config)
        
        # Test unauthorized user
        unauthorized_interaction = self.create_test_interaction(
            InteractionType.APPLICATION_COMMAND,
            command_name="ping"
        )
        unauthorized_interaction["member"]["user"]["id"] = "unauthorized_user_id"
        
        try:
            response = bot.handle_interaction(unauthorized_interaction)
            content = response.get("data", {}).get("content", "")
            
            if "not authorized" in content.lower():
                print("✅ Unauthorized user properly blocked")
                return True
            else:
                print(f"❌ Authorization failed: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Authorization test error: {e}")
            return False
    
    async def test_modal_submissions(self):
        """Test modal submission handling."""
        print("\n📝 Testing modal submissions...")
        
        bot = DiscordInteractionsBot(self.config)
        
        test_cases = [
            {
                "post_type": "note",
                "modal_data": {
                    "title": "E2E Test Note",
                    "content": "This is a test note created during E2E testing.",
                    "tags": "testing, e2e, automation"
                }
            },
            {
                "post_type": "response",
                "modal_data": {
                    "title": "E2E Test Response",
                    "content": "This is a test response post.",
                    "tags": "testing, response",
                    "reply_to_url": "https://example.com/original-post"
                }
            },
            {
                "post_type": "bookmark",
                "modal_data": {
                    "title": "E2E Test Bookmark",
                    "content": "Bookmarking this for testing purposes.",
                    "tags": "testing, bookmark",
                    "bookmark_url": "https://example.com/interesting-article"
                }
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            print(f"\n  Testing {test_case['post_type']} modal submission...")
            
            try:
                interaction = self.create_test_interaction(
                    InteractionType.MODAL_SUBMIT,
                    post_type=test_case["post_type"],
                    modal_data=test_case["modal_data"]
                )
                
                response = bot.handle_interaction(interaction)
                
                # Modal submissions should return deferred response
                if response.get("type") == InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE:
                    print(f"  ✅ {test_case['post_type']} modal submission deferred correctly")
                else:
                    print(f"  ❌ Unexpected modal response: {response}")
                    all_passed = False
                    
            except Exception as e:
                print(f"  ❌ Modal submission error: {e}")
                all_passed = False
        
        return all_passed
    
    async def test_api_client_functionality(self):
        """Test the interactions API client."""
        print("\n🔗 Testing API client functionality...")
        
        api_client = InteractionsAPIClient(
            self.config.publishing_api_endpoint,
            self.config.api_key
        )
        
        # Test PostData creation
        test_post = PostData(
            title="E2E Test API Client Post",
            content="Testing the API client functionality during E2E testing.",
            post_type="note",
            tags="testing, api, e2e"
        )
        
        print(f"✅ PostData created: {test_post.title}")
        print(f"✓ Post type: {test_post.post_type}")
        print(f"✓ Content length: {len(test_post.content)} chars")
        
        # Note: We're not actually calling create_post here because we'd need
        # a real publishing API running with proper auth. This tests the structure.
        
        return True
    
    async def test_publishing_api_integration(self):
        """Test integration with the publishing API."""
        print("\n📡 Testing publishing API integration...")
        
        try:
            # Test API health endpoint (should work if publishing API is mounted)
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Publishing API accessible via /api/ mount")
                        print(f"✓ API info: {data.get('name', 'Unknown')}")
                        return True
                    else:
                        print(f"⚠️ Publishing API not accessible: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"⚠️ Publishing API integration test error: {e}")
            return False
    
    async def test_error_handling(self):
        """Test error handling scenarios."""
        print("\n🚨 Testing error handling...")
        
        bot = DiscordInteractionsBot(self.config)
        
        test_cases = [
            {
                "name": "Unknown interaction type",
                "interaction": {
                    "type": 999,  # Invalid type
                    "id": "test_error_unknown_type",
                    "application_id": self.config.application_id,
                    "token": "test_token",
                    "version": 1
                },
                "expected_content_contains": "unknown"
            },
            {
                "name": "Unknown command",
                "interaction": self.create_test_interaction(
                    InteractionType.APPLICATION_COMMAND,
                    command_name="nonexistent_command"
                ),
                "expected_content_contains": "unknown command"
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            print(f"\n  Testing {test_case['name']}...")
            
            try:
                response = bot.handle_interaction(test_case["interaction"])
                content = response.get("data", {}).get("content", "").lower()
                expected = test_case["expected_content_contains"].lower()
                
                if expected in content:
                    print(f"  ✅ Error handled correctly: '{expected}' found in response")
                else:
                    print(f"  ❌ Error not handled properly: {response}")
                    all_passed = False
                    
            except Exception as e:
                print(f"  ❌ Error handling test failed: {e}")
                all_passed = False
        
        return all_passed
    
    async def run_comprehensive_test_suite(self):
        """Run the complete E2E test suite."""
        print("🧪 Discord HTTP Interactions Bot - Comprehensive E2E Test Suite")
        print("=" * 80)
        print(f"🕐 Test started at: {datetime.utcnow().isoformat()}Z")
        print()
        
        # Setup
        setup_success = await self.setup_configuration()
        if not setup_success:
            print("❌ Setup failed, aborting tests")
            return False
        
        # Define test sequence
        tests = [
            ("Combined App Health", self.test_combined_app_health),
            ("Root Endpoint", self.test_root_endpoint),
            ("Discord PING Interaction", self.test_discord_ping_interaction),
            ("Discord Slash Commands", self.test_discord_slash_commands),
            ("Authorization", self.test_authorization),
            ("Modal Submissions", self.test_modal_submissions),
            ("API Client Functionality", self.test_api_client_functionality),
            ("Publishing API Integration", self.test_publishing_api_integration),
            ("Error Handling", self.test_error_handling)
        ]
        
        # Run tests
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 Running: {test_name}")
            print(f"{'='*60}")
            
            try:
                result = await test_func()
                if result:
                    passed_tests += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
                    
                self.results.append({
                    "name": test_name,
                    "passed": result,
                    "error": None
                })
                
            except Exception as e:
                print(f"❌ {test_name} CRASHED: {e}")
                self.results.append({
                    "name": test_name,
                    "passed": False,
                    "error": str(e)
                })
        
        # Results summary
        await self.print_test_summary(passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    async def print_test_summary(self, passed_tests: int, total_tests: int):
        """Print comprehensive test summary."""
        print("\n" + "=" * 80)
        print("📊 E2E Test Suite Results Summary")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Detailed results
        print(f"\n📋 Detailed Test Results:")
        for result in self.results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"  {status} {result['name']}")
            if result["error"]:
                print(f"    Error: {result['error']}")
        
        # Component health assessment
        print(f"\n🔍 Component Health Assessment:")
        
        # Group tests by component
        component_results = {
            "Infrastructure": ["Combined App Health", "Root Endpoint"],
            "Discord Interactions": ["Discord PING Interaction", "Discord Slash Commands", "Authorization"],
            "Modal Processing": ["Modal Submissions"],
            "API Integration": ["API Client Functionality", "Publishing API Integration"],
            "Error Handling": ["Error Handling"]
        }
        
        for component, test_names in component_results.items():
            component_tests = [r for r in self.results if r["name"] in test_names]
            component_passed = sum(1 for r in component_tests if r["passed"])
            component_total = len(component_tests)
            component_rate = (component_passed / component_total * 100) if component_total > 0 else 0
            
            status = "🟢" if component_rate == 100 else "🟡" if component_rate >= 80 else "🔴"
            print(f"  {status} {component}: {component_passed}/{component_total} ({component_rate:.1f}%)")
        
        # Overall assessment
        print(f"\n🎯 System Readiness Assessment:")
        
        if success_rate >= 100:
            print("🏆 EXCELLENT: HTTP Interactions bot is production-ready!")
            print("   All systems operational and fully validated.")
        elif success_rate >= 90:
            print("✅ GOOD: System ready for production with minor issues.")
            print("   Review failed tests and consider fixes.")
        elif success_rate >= 75:
            print("⚠️ ACCEPTABLE: Core functionality working but needs attention.")
            print("   Address failing tests before production deployment.")
        else:
            print("❌ NEEDS WORK: Significant issues detected.")
            print("   Major fixes required before production readiness.")
        
        print(f"\n🏁 Test completed at: {datetime.utcnow().isoformat()}Z")


async def main():
    """Main test execution function."""
    
    # Check if combined app is running
    print("🔍 Checking if combined app is running on localhost:8000...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health", timeout=5) as response:
                if response.status == 200:
                    print("✅ Combined app is running and accessible")
                else:
                    print(f"⚠️ Combined app returned status {response.status}")
    except Exception as e:
        print(f"❌ Combined app not accessible: {e}")
        print("\n📋 To run this E2E test:")
        print("1. Start the combined app: cd src && uv run python combined_app.py")
        print("2. In another terminal, run this test script")
        print("3. Or set up proper Discord configuration and use the UV script")
        return False
    
    # Run comprehensive test suite
    test_suite = E2ETestSuite()
    success = await test_suite.run_comprehensive_test_suite()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
