#!/usr/bin/env python3
"""
Quick test to validate the actual frontmatter being generated.
"""

import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from publishing_api.config import APIConfig
from publishing_api.github_client import GitHubClient
from publishing_api.publishing import PublishingService


def test_frontmatter_conversion():
    """Test actual frontmatter conversion."""
    
    # Test cases
    test_messages = [
        {
            "name": "Simple Note",
            "message": """/post note
---
title: "Weekly Development Summary"
tags: ["development", "summary", "automation"]
---

This week I focused on improving the Discord publishing bot with branch/PR workflow support."""
        },
        {
            "name": "Response with URL",
            "message": """/post response
---
response_type: "reply"
in_reply_to: "https://github.com/example-dev/example-repo/blob/main/README.md"
title: "Great documentation architecture"
tags: ["documentation", "architecture", "fsharp"]
---

Excellent example of clean documentation architecture for a personal website."""
        },
        {
            "name": "Bookmark",
            "message": """/post bookmark
---
url: "https://indieweb.org/posts"
title: "IndieWeb Posts Documentation"
tags: ["indieweb", "documentation", "standards"]
---

Comprehensive documentation about post types and microformats for IndieWeb sites."""
        }
    ]
    
    # Create service
    try:
        config = APIConfig.from_env()
    except:
        config = APIConfig(
            api_key="test",
            discord_user_id="test_user",
            github_token="test",
            github_repo="test/test"
        )
    
    github_client = GitHubClient(config.github_token, config.github_repo)
    publishing_service = PublishingService(github_client, config)
    
    print("🔍 FRONTMATTER VALIDATION TEST")
    print("=" * 60)
    
    for i, test in enumerate(test_messages, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 40)
        
        # Parse message
        post_type, original_fm, content = publishing_service.parse_discord_message(test['message'])
        
        print(f"Post Type: {post_type}")
        
        print(f"\nORIGINAL frontmatter from Discord:")
        for key, value in original_fm.items():
            print(f"  {key}: {repr(value)}")
        
        # Convert to target schema
        target_fm = publishing_service.convert_to_target_schema(post_type, original_fm, content)
        
        print(f"\nTARGET frontmatter (luisquintanilla.me schema):")
        for key, value in target_fm.items():
            print(f"  {key}: {repr(value)}")
        
        # Generate full markdown
        markdown = publishing_service.build_markdown_file(target_fm, content)
        
        print(f"\nGenerated Markdown Preview:")
        lines = markdown.split('\n')
        frontmatter_end = 0
        for j, line in enumerate(lines[1:], 1):  # Skip first ---
            if line.strip() == '---':
                frontmatter_end = j
                break
        
        # Show just the frontmatter part
        if frontmatter_end > 0:
            frontmatter_section = '\n'.join(lines[:frontmatter_end + 1])
            print(frontmatter_section)
        else:
            print(markdown[:300] + "...")
        
        print(f"\nTotal markdown length: {len(markdown)} characters")
    
    print("\n" + "=" * 60)
    print("📋 SCHEMA COMPLIANCE CHECK")
    print("=" * 60)
    
    # Check what luisquintanilla.me actually uses
    print("\nExpected schemas for luisquintanilla.me:")
    
    print("\n📝 NOTE posts should have:")
    print("  ✓ post_type: 'note'")
    print("  ✓ title: string")
    print("  ✓ published_date: 'YYYY-MM-DD HH:MM -05:00'")
    print("  ✓ tags: [array]")
    
    print("\n💬 RESPONSE posts should have:")
    print("  ✓ title: string")
    print("  ✓ response_type: 'reply' | 'bookmark' | etc")
    print("  ✓ dt_published: 'YYYY-MM-DDTHH:MM:SSZ'")
    print("  ✓ dt_updated: 'YYYY-MM-DDTHH:MM:SSZ'")
    print("  ✓ tags: [array]")
    print("  ✓ targeturl: string (for bookmarks)")
    print("  ✓ in_reply_to: string (for replies)")
    
    print("\n🔖 BOOKMARK posts should have:")
    print("  ✓ Same as responses but with response_type: 'bookmark'")
    print("  ✓ targeturl: required")


if __name__ == "__main__":
    test_frontmatter_conversion()
