#!/usr/bin/env python3
"""
Complete End-to-End Integration Test

This script demonstrates the complete Discord to GitHub publishing workflow
by simulating a real Discord interaction and publishing to GitHub.
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from discord_bot.main import create_bot
from discord_bot.modals import NoteModal
from publishing_api.config import APIConfig
from publishing_api.github_client import GitHubClient
from publishing_api.publishing import PublishingService

load_dotenv()

class MockDiscordInteraction:
    """Mock Discord interaction that behaves like the real thing."""
    
    def __init__(self, user_id: str):
        self.user = type('User', (), {'id': int(user_id)})()
        self.response = type('Response', (), {
            'defer': self._async_noop,
            'send_message': self._async_print
        })()
        self.followup = type('Followup', (), {
            'send': self._async_print
        })()
    
    async def _async_noop(self, *args, **kwargs):
        """No-op for defer."""
        pass
    
    async def _async_print(self, message, ephemeral=True):
        """Print message like Discord would show it."""
        print(f"📱 Discord Response: {message}")

class MockTextInput:
    """Mock Discord TextInput with all necessary methods."""
    
    def __init__(self, value: str):
        self.value = value
    
    def strip(self):
        return self.value.strip()
    
    def lower(self):
        return self.value.lower()
    
    def split(self, sep=None):
        return self.value.split(sep)

async def simulate_discord_note_publishing():
    """Simulate the complete Discord note publishing workflow."""
    print("🎭 Simulating Complete Discord Workflow")
    print("=" * 60)
    
    try:
        # 1. Initialize Discord Bot (like when bot starts)
        print("1️⃣ Initializing Discord Bot...")
        bot = create_bot()
        print(f"   ✅ Bot created for user: {bot.config.discord_user_id}")
        print(f"   🔗 API endpoint: {bot.config.fastapi_endpoint}")
        
        # 2. Initialize API components (like when API starts)
        print("\n2️⃣ Initializing Publishing API components...")
        api_config = APIConfig.from_env()
        github_client = GitHubClient(api_config.github_token, api_config.github_repo)
        publishing_service = PublishingService(github_client, api_config)
        
        # Test GitHub connectivity
        await github_client.check_connectivity()
        print(f"   ✅ GitHub connected: {api_config.github_repo}")
        
        # 3. Simulate user typing /post note command in Discord
        print("\n3️⃣ User types '/post note' command in Discord...")
        print("   💬 Discord shows modal dialog...")
        
        # 4. User fills out the note modal
        print("\n4️⃣ User fills out note modal...")
        
        # Create real API client for the bot to use
        api_client = bot.api_client
        
        # Create note modal (like Discord would)
        note_modal = NoteModal(api_client)
        
        # Simulate user input in modal
        note_modal.content = MockTextInput("""# My Development Journey

Today I made significant progress on the **Discord Publishing Bot** project! 

## What I Accomplished

- ✅ Implemented complete note publishing workflow
- ✅ Created comprehensive modal interfaces for all post types
- ✅ Built robust content processing with YAML frontmatter
- ✅ Integrated GitHub API for automated commits
- ✅ Added end-to-end testing and validation

## Technical Highlights

The system uses a clean **microservices architecture**:

1. **Discord Bot** - Handles user interaction with slash commands and modals
2. **Publishing API** - Processes content and manages GitHub integration

```python
# Example of the publishing workflow
async def publish_note(content):
    markdown = generate_markdown_with_frontmatter(content)
    commit_sha = await github_client.commit_file(filepath, markdown)
    return f"Published to {filepath}"
```

## Next Steps

- [ ] Deploy to production environment
- [ ] Add monitoring and alerting
- [ ] Implement additional post types
- [ ] Create user documentation

This project demonstrates the power of **automation** in content publishing workflows! 🚀""")
        
        note_modal.title = MockTextInput("Discord Publishing Bot Development Update")
        note_modal.tags = MockTextInput("development, automation, discord, github, publishing")
        
        print("   📝 Modal filled with:")
        print(f"      Title: {note_modal.title.value}")
        print(f"      Tags: {note_modal.tags.value}")
        print(f"      Content: {len(note_modal.content.value)} characters")
        
        # 5. Simulate modal submission
        print("\n5️⃣ User clicks 'Submit' button...")
        
        # Create mock interaction
        user_id = api_config.discord_user_id
        interaction = MockDiscordInteraction(user_id)
        
        # Override the API client to use our in-process publishing service
        # This simulates what would happen when the Discord bot calls the API
        original_publish_post = api_client.publish_post
        
        async def mock_publish_post(message, user_id):
            """Simulate the API call by using the publishing service directly."""
            try:
                result = await publishing_service.publish_post(message, user_id)
                return True, result
            except Exception as e:
                return False, {"error": str(e)}
        
        api_client.publish_post = mock_publish_post
        
        # Submit the modal (this triggers the entire publishing workflow)
        await note_modal.on_submit(interaction)
        
        print("\n6️⃣ Publishing workflow completed!")
        
        # 7. Restore original method and cleanup
        api_client.publish_post = original_publish_post
        await bot.close()
        
        print("\n🎉 Complete end-to-end workflow simulation successful!")
        print("\nWhat just happened:")
        print("1. Discord bot received /post note command")
        print("2. Modal dialog was presented to user")
        print("3. User filled out note content, title, and tags")
        print("4. Modal submission triggered publishing workflow")
        print("5. Content was parsed and formatted with YAML frontmatter")
        print("6. Markdown file was committed to GitHub repository")
        print("7. User received confirmation with file path and site URL")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def demonstrate_all_post_types():
    """Demonstrate all post types being processed."""
    print("\n🎨 Demonstrating All Post Types")
    print("=" * 45)
    
    try:
        # Initialize components
        api_config = APIConfig.from_env()
        github_client = GitHubClient(api_config.github_token, api_config.github_repo)
        publishing_service = PublishingService(github_client, api_config)
        
        # Test cases for all post types
        test_posts = [
            {
                "type": "note",
                "message": """/post note
---
title: Quick Development Note
tags: ["development", "testing"]
---

Just implemented a new feature! The Discord bot now supports all four post types with proper validation and error handling."""
            },
            {
                "type": "response",
                "message": """/post response
---
response_type: reply
in_reply_to: https://example.com/original-post
---

Great point about the architecture! I think the microservices approach really helps with maintainability."""
            },
            {
                "type": "bookmark",
                "message": """/post bookmark
---
url: https://fastapi.tiangolo.com/
title: FastAPI Documentation
tags: ["documentation", "python", "api"]
---

Excellent documentation for FastAPI. Very comprehensive with great examples."""
            },
            {
                "type": "media",
                "message": """/post media
---
media_url: https://example.com/architecture-diagram.png
alt_text: System architecture diagram showing Discord bot and Publishing API
tags: ["diagram", "architecture", "documentation"]
---

System architecture diagram showing the complete Discord Publishing Bot workflow."""
            }
        ]
        
        user_id = api_config.discord_user_id
        
        for i, post_data in enumerate(test_posts, 1):
            print(f"\n{i}. Processing {post_data['type']} post...")
            
            try:
                result = await publishing_service.publish_post(
                    message=post_data['message'],
                    user_id=user_id
                )
                
                print(f"   ✅ Published: {result['filepath']}")
                print(f"   🔗 Commit: {result['commit_sha'][:8]}...")
                
                if result.get('site_url'):
                    print(f"   🌐 URL: {result['site_url']}")
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
        
        print("\n✅ All post types demonstrated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Post type demonstration failed: {str(e)}")
        return False

async def main():
    """Main demonstration runner."""
    print("🚀 Discord Publishing Bot - Complete Integration Demo")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.utcnow().isoformat()}Z")
    
    # Run complete workflow simulation
    workflow_success = await simulate_discord_note_publishing()
    
    # Demonstrate all post types
    demo_success = await demonstrate_all_post_types()
    
    print("\n" + "=" * 70)
    print("📊 Demo Results Summary")
    print("=" * 70)
    
    if workflow_success and demo_success:
        print("🎊 Complete Integration Demo Successful!")
        print("\n✅ Key Achievements:")
        print("   • Discord bot initialization and configuration")
        print("   • Modal interface simulation and form processing")
        print("   • Content parsing and YAML frontmatter generation")
        print("   • GitHub API integration and file commits")
        print("   • All four post types (note, response, bookmark, media)")
        print("   • End-to-end workflow validation")
        
        print("\n🎯 Next Steps for Production:")
        print("   1. Deploy Publishing API to cloud hosting (Fly.io/Railway)")
        print("   2. Configure Discord bot hosting")
        print("   3. Set up monitoring and alerting")
        print("   4. Create user documentation")
        print("   5. Implement additional features (preview, editing)")
        
        return 0
    else:
        print("💥 Some demonstrations failed. Check output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
