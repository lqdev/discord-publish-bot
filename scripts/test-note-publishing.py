#!/usr/bin/env python3
"""
Test script for note publishing workflow.

Tests the end-to-end note publishing functionality without requiring Discord interaction.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from publishing_api.config import APIConfig
from publishing_api.github_client import GitHubClient
from publishing_api.publishing import PublishingService

load_dotenv()

async def test_note_publishing():
    """Test the note publishing workflow."""
    print("🔬 Testing Note Publishing Workflow")
    print("=" * 50)
    
    try:
        # Initialize configuration
        print("📋 Loading configuration...")
        config = APIConfig.from_env()
        config.validate()
        print(f"✅ Config loaded - Repository: {config.github_repo}")
        
        # Initialize GitHub client
        print("🐙 Initializing GitHub client...")
        github_client = GitHubClient(config.github_token, config.github_repo)
        
        # Test connectivity
        print("🔗 Testing GitHub connectivity...")
        await github_client.check_connectivity()
        print("✅ GitHub connection successful")
        
        # Initialize publishing service
        print("📝 Initializing publishing service...")
        publishing_service = PublishingService(github_client, config)
        print("✅ Publishing service ready")
        
        # Test note publishing
        print("📄 Testing note publishing...")
        
        # Create a test note message
        test_message = """/post note
---
title: Test Note from Development
tags: ["test", "development", "automation"]
---

# Test Note

This is a **test note** published from the development testing script.

## Features Tested

- Discord message parsing
- YAML frontmatter generation
- Markdown file creation
- GitHub commit functionality

*Generated at: {timestamp}*

## Code Example

```python
def hello_world():
    print("Hello from Discord Publishing Bot!")
```

This note validates that the entire publishing pipeline is working correctly."""
        
        from datetime import datetime
        test_message = test_message.format(timestamp=datetime.utcnow().isoformat())
        
        # Test user ID (should match your Discord user ID in env)
        test_user_id = config.discord_user_id
        
        print(f"📤 Publishing test note for user {test_user_id}...")
        
        # Publish the note
        result = await publishing_service.publish_post(
            message=test_message,
            user_id=test_user_id
        )
        
        print("✅ Note published successfully!")
        print(f"📁 File path: {result['filepath']}")
        print(f"🔗 Commit SHA: {result['commit_sha']}")
        
        if result.get('site_url'):
            print(f"🌐 Site URL: {result['site_url']}")
        
        print("\n🎉 End-to-end test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_message_parsing():
    """Test message parsing functionality."""
    print("\n🔍 Testing Message Parsing")
    print("=" * 30)
    
    try:
        config = APIConfig.from_env()
        github_client = GitHubClient(config.github_token, config.github_repo)
        publishing_service = PublishingService(github_client, config)
        
        # Test cases
        test_cases = [
            {
                "name": "Simple note",
                "message": "/post note\nThis is a simple note without frontmatter.",
            },
            {
                "name": "Note with title",
                "message": "/post note\n---\ntitle: My Custom Title\n---\nThis note has a custom title.",
            },
            {
                "name": "Note with tags",
                "message": '/post note\n---\ntags: ["development", "testing"]\n---\nThis note has tags.',
            },
            {
                "name": "Full frontmatter note",
                "message": '/post note\n---\ntitle: Complex Note\ntags: ["test", "complex"]\n---\n# Heading\n\nThis is **complex** content with *formatting*.',
            },
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing {test_case['name']}...")
            
            try:
                post_type, frontmatter, content = publishing_service.parse_discord_message(test_case['message'])
                
                print(f"   Post type: {post_type}")
                print(f"   Frontmatter: {frontmatter}")
                print(f"   Content: {content[:50]}...")
                
                # Test markdown generation
                markdown = publishing_service.build_markdown_file(frontmatter, content)
                print(f"   ✅ Markdown generated ({len(markdown)} chars)")
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
        
        print("\n✅ Message parsing tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Parsing test failed: {str(e)}")
        return False

async def main():
    """Main test runner."""
    print("🚀 Discord Publish Bot - Development Testing")
    print("=" * 60)
    
    # Test parsing functionality
    parsing_success = await test_message_parsing()
    
    # Test full publishing workflow
    publishing_success = await test_note_publishing()
    
    if parsing_success and publishing_success:
        print("\n🎊 All tests passed! The note publishing workflow is ready.")
        return 0
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
