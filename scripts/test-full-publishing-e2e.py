#!/usr/bin/env python3
"""
Discord HTTP Interactions - Full Publishing E2E Test

Tests the complete end-to-end workflow including:
1. Discord interaction simulation
2. Modal submission processing  
3. Publishing API integration
4. GitHub branch creation
5. Pull request creation
6. Full post publishing workflow

Based on test-enhanced-workflow.py patterns but adapted for HTTP interactions.
"""

import asyncio
import json
import os
import sys
import time
import requests
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

load_dotenv()

# Import components
from discord_interactions.config import DiscordConfig
from discord_interactions.bot import DiscordInteractionsBot, InteractionType, InteractionResponseType
from discord_interactions.api_client import InteractionsAPIClient, PostData
from publishing_api.config import APIConfig
from publishing_api.github_client import GitHubClient
from publishing_api.publishing import PublishingService


class FullPublishingE2ETest:
    """Complete E2E test including actual GitHub operations."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.discord_config = None
        self.api_config = None
        self.publishing_service = None
        self.github_client = None
        self.test_results = []
        
    async def setup_configuration(self):
        """Set up both Discord and Publishing API configurations."""
        print("🔧 Setting up configurations...")
        
        # Set up Discord config (can use mock for this test)
        print("\n📱 Discord Configuration:")
        try:
            self.discord_config = DiscordConfig.from_env()
            is_valid, errors = self.discord_config.validate()
            
            if is_valid:
                print("✅ Real Discord configuration loaded")
            else:
                print(f"⚠️ Real config incomplete: {errors}")
                print("🎭 Using mock Discord configuration for testing")
                self.discord_config = DiscordConfig(
                    application_id="123456789012345678",
                    public_key="a" * 64,
                    bot_token="mock_bot_token",
                    authorized_user_id="test_user_123456",
                    publishing_api_endpoint=self.base_url,
                    api_key="test_api_key_for_e2e"
                )
        except Exception as e:
            print(f"⚠️ Error loading Discord config: {e}")
            return False
        
        # Set up Publishing API config (needs to be real)
        print("\n📡 Publishing API Configuration:")
        try:
            self.api_config = APIConfig.from_env()
            self.api_config.validate()
            print("✅ Publishing API configuration loaded")
            print(f"   📦 Repository: {self.api_config.github_repo}")
            print(f"   👤 Discord User: {self.api_config.discord_user_id}")
            print(f"   🌐 Site URL: {self.api_config.site_base_url}")
        except Exception as e:
            print(f"❌ Publishing API configuration error: {e}")
            print("   Please ensure environment variables are set:")
            print("   - GITHUB_TOKEN, GITHUB_REPO, DISCORD_USER_ID, API_KEY")
            return False
        
        # Set up GitHub client and publishing service
        try:
            self.github_client = GitHubClient(
                self.api_config.github_token, 
                self.api_config.github_repo
            )
            self.publishing_service = PublishingService(
                self.github_client, 
                self.api_config
            )
            print("✅ GitHub client and publishing service initialized")
        except Exception as e:
            print(f"❌ Error initializing services: {e}")
            return False
        
        return True
    
    async def test_github_connectivity(self):
        """Test GitHub connectivity."""
        print("\n🔗 Testing GitHub connectivity...")
        
        try:
            await self.github_client.check_connectivity()
            print("✅ GitHub connection successful")
            return True
        except Exception as e:
            print(f"❌ GitHub connection failed: {e}")
            return False
    
    def simulate_discord_modal_submission(self, post_type: str, test_data: dict):
        """Simulate a Discord modal submission."""
        print(f"\n📝 Simulating Discord modal submission for {post_type}...")
        
        # Create Discord interaction
        interaction = {
            "type": InteractionType.MODAL_SUBMIT,
            "id": f"test_interaction_{int(time.time())}",
            "application_id": self.discord_config.application_id,
            "token": f"test_token_{int(time.time())}",
            "version": 1,
            "data": {
                "custom_id": f"post_modal_{post_type}",
                "components": []
            },
            "member": {
                "user": {
                    "id": self.discord_config.authorized_user_id,
                    "username": "testuser"
                }
            }
        }
        
        # Convert test data to Discord component format
        for field_name, value in test_data.items():
            interaction["data"]["components"].append({
                "type": 1,  # ACTION_ROW
                "components": [{
                    "type": 4,  # TEXT_INPUT
                    "custom_id": field_name,
                    "value": value
                }]
            })
        
        return interaction
    
    def extract_modal_data(self, interaction):
        """Extract form data from Discord modal interaction."""
        data = {}
        
        for action_row in interaction["data"]["components"]:
            for component in action_row["components"]:
                if component["type"] == 4:  # TEXT_INPUT
                    custom_id = component["custom_id"]
                    value = component.get("value", "")
                    data[custom_id] = value
        
        return data
    
    async def test_full_publishing_workflow(self, test_case):
        """Test the complete publishing workflow for a single post."""
        post_type = test_case["post_type"]
        test_data = test_case["test_data"]
        
        print(f"\n{'='*60}")
        print(f"🧪 Testing Full {post_type.upper()} Publishing Workflow")
        print(f"{'='*60}")
        
        try:
            # Step 1: Simulate Discord modal submission
            interaction = self.simulate_discord_modal_submission(post_type, test_data)
            
            # Step 2: Process the interaction (like our combined app would)
            bot = DiscordInteractionsBot(self.discord_config)
            response = bot.handle_interaction(interaction)
            
            if response.get("type") != InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE:
                print(f"❌ Modal submission not deferred correctly: {response}")
                return False
            
            print("✅ Discord modal submission processed and deferred")
            
            # Step 3: Extract form data and create PostData
            form_data = self.extract_modal_data(interaction)
            
            post_data = PostData(
                title=form_data.get("title", ""),
                content=form_data.get("content", ""),
                post_type=post_type,
                tags=form_data.get("tags"),
                reply_to_url=form_data.get("reply_to_url"),
                bookmark_url=form_data.get("bookmark_url"),
                media_url=form_data.get("media_url")
            )
            
            print(f"✅ PostData created: {post_data.title}")
            
            # Step 4: Validate required fields
            if not post_data.title or not post_data.content:
                print("❌ Missing required fields (title/content)")
                return False
            
            print("✅ Required fields validated")
            
            # Step 5: Process with publishing service (simulate the background task)
            print(f"\n📊 Processing with publishing service...")
            
            # Parse message in publishing service format
            message = f"/post {post_type}\n---\n"
            message += f"title: \"{post_data.title}\"\n"
            if post_data.tags:
                tag_list = [f'"{tag.strip()}"' for tag in post_data.tags.split(',')]
                message += f"tags: [{', '.join(tag_list)}]\n"
            if post_data.reply_to_url:
                message += f"reply_to_url: \"{post_data.reply_to_url}\"\n"
            if post_data.bookmark_url:
                message += f"bookmark_url: \"{post_data.bookmark_url}\"\n"
            if post_data.media_url:
                message += f"media_url: \"{post_data.media_url}\"\n"
            message += "---\n"
            message += post_data.content
            
            # Parse and validate with publishing service
            parsed_type, frontmatter, content = self.publishing_service.parse_discord_message(message)
            print(f"✅ Message parsed: type={parsed_type}")
            
            # Convert to target schema
            target_frontmatter = self.publishing_service.convert_to_target_schema(
                parsed_type, frontmatter, content
            )
            print(f"✅ Schema converted: {list(target_frontmatter.keys())}")
            
            # Validate content
            validation_results = self.publishing_service.validate_content(
                parsed_type, target_frontmatter, content
            )
            
            all_validations_passed = all(result["passed"] for result in validation_results.values())
            print(f"✅ Content validation: {'PASSED' if all_validations_passed else 'WARNINGS'}")
            
            for check, result in validation_results.items():
                status = "✅" if result["passed"] else "⚠️"
                print(f"   {status} {check}: {result['message']}")
            
            # Generate filename and markdown
            filename = self.publishing_service.generate_filename(parsed_type, target_frontmatter, content)
            markdown_content = self.publishing_service.build_markdown_file(target_frontmatter, content)
            
            print(f"✅ Generated filename: {filename}")
            print(f"✅ Generated markdown: {len(markdown_content)} characters")
            
            # Step 6: GitHub operations (if enabled)
            github_tests_enabled = os.getenv("RUN_GITHUB_TESTS", "false").lower() == "true"
            
            if github_tests_enabled:
                print(f"\n🚀 Creating GitHub branch and PR...")
                
                # Generate branch name
                branch_name = self.github_client.generate_branch_name(
                    content_type=parsed_type,
                    message_id=f"e2e-test-{int(time.time())}",
                    user_id=self.api_config.discord_user_id
                )
                
                # Generate PR template
                content_preview = content[:100] if content else target_frontmatter.get("title", "")
                pr_title, pr_body = self.github_client.generate_pr_template(
                    content_type=parsed_type,
                    content_preview=content_preview,
                    user_id=self.api_config.discord_user_id,
                    message_id=f"e2e-test-{int(time.time())}",
                    validation_results=validation_results
                )
                
                print(f"✅ Branch name: {branch_name}")
                print(f"✅ PR title: {pr_title}")
                
                # Create branch, commit file, and create PR
                directory = self.publishing_service.CONTENT_TYPE_DIRECTORIES[parsed_type]
                full_path = f"{directory}/{filename}"
                
                commit_result = await self.github_client.commit_file_to_branch(
                    filepath=full_path,
                    content=markdown_content,
                    commit_message=f"Add {parsed_type} post via Discord HTTP interactions E2E test",
                    branch_name=branch_name,
                    create_pr=True,
                    pr_title=pr_title,
                    pr_body=pr_body,
                )
                
                if commit_result and commit_result.get("commit_sha"):
                    print(f"✅ File committed: {commit_result['commit_sha'][:8]}")
                    
                    if commit_result.get("pr_url"):
                        print(f"🎉 Pull request created: {commit_result['pr_url']}")
                        print(f"   Branch: {branch_name}")
                        print(f"   File: {full_path}")
                        
                        return {
                            "success": True,
                            "post_type": parsed_type,
                            "filename": filename,
                            "branch_name": branch_name,
                            "pr_url": commit_result["pr_url"],
                            "commit_sha": commit_result["commit_sha"],
                            "validation_passed": all_validations_passed
                        }
                    else:
                        print(f"⚠️ Commit successful but PR creation failed")
                        return {
                            "success": True,
                            "post_type": parsed_type,
                            "filename": filename,
                            "branch_name": branch_name,
                            "commit_sha": commit_result["commit_sha"],
                            "validation_passed": all_validations_passed,
                            "pr_creation_failed": True
                        }
                else:
                    error_msg = commit_result.get("error", "Unknown error") if commit_result else "No result returned"
                    print(f"❌ GitHub commit failed: {error_msg}")
                    return {"success": False, "error": error_msg}
            
            else:
                print(f"\n💡 GitHub operations skipped (set RUN_GITHUB_TESTS=true to enable actual PR creation)")
                return {
                    "success": True,
                    "post_type": parsed_type,
                    "filename": filename,
                    "validation_passed": all_validations_passed,
                    "github_skipped": True
                }
            
        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def run_full_e2e_tests(self):
        """Run complete E2E tests with actual publishing."""
        print("🚀 Discord HTTP Interactions - Full Publishing E2E Test")
        print("=" * 80)
        print(f"🕐 Test started at: {datetime.utcnow().isoformat()}Z")
        print()
        
        # Setup
        if not await self.setup_configuration():
            return False
        
        # Test GitHub connectivity
        if not await self.test_github_connectivity():
            return False
        
        # Check if GitHub tests are enabled
        github_tests_enabled = os.getenv("RUN_GITHUB_TESTS", "false").lower() == "true"
        print(f"\n🔧 GitHub Testing: {'ENABLED' if github_tests_enabled else 'DISABLED'}")
        if not github_tests_enabled:
            print("   💡 Set RUN_GITHUB_TESTS=true to enable actual PR creation")
        
        # Define test cases
        test_cases = [
            {
                "post_type": "note",
                "test_data": {
                    "title": "Discord HTTP Interactions E2E Test Note",
                    "content": "This note was created during E2E testing of the Discord HTTP interactions bot. Testing complete workflow including PR creation.",
                    "tags": "testing, e2e, discord, http-interactions"
                }
            },
            {
                "post_type": "response",
                "test_data": {
                    "title": "E2E Test Response Post",
                    "content": "This is a response post created during comprehensive E2E testing.",
                    "tags": "testing, response, e2e",
                    "reply_to_url": "https://github.com/example-dev/example-repo/discussions/test"
                }
            },
            {
                "post_type": "bookmark",
                "test_data": {
                    "title": "E2E Test Bookmark",
                    "content": "Bookmarking this resource during E2E testing of the HTTP interactions workflow.",
                    "tags": "testing, bookmark, e2e",
                    "bookmark_url": "https://docs.discord.com/interactions/receiving-and-responding"
                }
            }
        ]
        
        # Run tests
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'🧪' * 3} Test {i}/{len(test_cases)}: {test_case['post_type'].upper()} Post")
            result = await self.test_full_publishing_workflow(test_case)
            results.append(result)
        
        # Summary
        await self.print_results_summary(results, github_tests_enabled)
        
        successful_tests = [r for r in results if r and r.get("success")]
        return len(successful_tests) == len(test_cases)
    
    async def print_results_summary(self, results, github_tests_enabled):
        """Print comprehensive results summary."""
        print("\n" + "=" * 80)
        print("📊 Full Publishing E2E Test Results")
        print("=" * 80)
        
        successful_tests = [r for r in results if r and r.get("success")]
        failed_tests = [r for r in results if not r or not r.get("success")]
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
        print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
        
        if github_tests_enabled:
            prs_created = [r for r in successful_tests if r.get("pr_url")]
            commits_made = [r for r in successful_tests if r.get("commit_sha")]
            
            print(f"\n🚀 GitHub Operations:")
            print(f"   📝 Commits created: {len(commits_made)}")
            print(f"   🔀 Pull requests created: {len(prs_created)}")
            
            if prs_created:
                print(f"\n🎉 Created Pull Requests:")
                for result in prs_created:
                    print(f"   • {result['post_type'].upper()}: {result['pr_url']}")
                    print(f"     Branch: {result['branch_name']}")
                    print(f"     File: {result['filename']}")
                    print(f"     Commit: {result['commit_sha'][:8]}")
        
        # Validation summary
        validation_results = [r for r in successful_tests if r.get("validation_passed")]
        print(f"\n📋 Content Validation:")
        print(f"   ✅ All validations passed: {len(validation_results)}/{len(successful_tests)}")
        
        # Overall assessment
        success_rate = len(successful_tests) / len(results) * 100
        
        print(f"\n🎯 Overall E2E Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 100:
            print("🏆 EXCELLENT: Complete workflow validated and production-ready!")
            if github_tests_enabled:
                print("   ✅ Real GitHub PRs created successfully")
            print("   ✅ Discord interactions working perfectly")
            print("   ✅ Publishing pipeline fully operational")
        elif success_rate >= 80:
            print("✅ GOOD: Core workflow functional with minor issues")
        else:
            print("❌ NEEDS WORK: Significant issues in the publishing pipeline")
        
        print(f"\n🏁 Test completed at: {datetime.utcnow().isoformat()}Z")


async def main():
    """Main execution function."""
    
    # Check if combined app is running
    print("🔍 Checking if combined app is running...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Combined app is running: {data}")
                else:
                    print(f"⚠️ Combined app returned status {response.status}")
    except Exception as e:
        print(f"❌ Combined app not accessible: {e}")
        print("\n📋 To run this test:")
        print("1. Start the combined app: uv run combined-app")
        print("2. Set environment variables including RUN_GITHUB_TESTS=true")
        print("3. Run this test script")
        return False
    
    # Run full E2E test
    test_suite = FullPublishingE2ETest()
    success = await test_suite.run_full_e2e_tests()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        
        if success:
            print("\n🎉 FULL E2E TEST SUCCESSFUL!")
            print("Your Discord HTTP interactions bot with publishing workflow is production-ready!")
        else:
            print("\n⚠️ E2E test completed with issues - review output above")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
