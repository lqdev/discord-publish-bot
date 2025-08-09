#!/usr/bin/env python3
"""
Cleanup script to remove test branches from the repository.
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from publishing_api.github_client import GitHubClient
from publishing_api.config import APIConfig

async def cleanup_test_branches():
    """Remove test branches from previous test runs."""
    print("🧹 Cleaning up test branches")
    print("=" * 50)
    
    # Load configuration
    config = APIConfig.from_env()
    print(f"✓ Config loaded: {config.github_repo}")
    
    # Initialize GitHub client
    github_client = GitHubClient(config.github_token, config.github_repo)
    
    # Test branch patterns to clean up
    test_patterns = [
        "content/discord-bot/2025-08-09/note/727687304596160593-integration-test-1",
        "content/discord-bot/2025-08-09/response/727687304596160593-integration-test-2", 
        "content/discord-bot/2025-08-09/bookmark/727687304596160593-integration-test-3",
        "content/discord-bot/2025-08-09/media/727687304596160593-integration-test-4",
        "debug/test-20250808-211753",
        "debug/commit-test-20250808-211846"
    ]
    
    cleaned_count = 0
    failed_count = 0
    
    for branch_name in test_patterns:
        try:
            print(f"🗑️ Attempting to delete branch: {branch_name}")
            success = await github_client.delete_branch(branch_name)
            if success:
                print(f"✓ Deleted: {branch_name}")
                cleaned_count += 1
            else:
                print(f"⚠️ Could not delete: {branch_name} (may not exist)")
                failed_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {branch_name}: {e}")
            failed_count += 1
    
    print(f"\n📊 Cleanup Summary:")
    print(f"✓ Successfully deleted: {cleaned_count}")
    print(f"⚠️ Failed or not found: {failed_count}")
    print(f"🎉 Cleanup completed!")

if __name__ == "__main__":
    # Check environment
    if not os.getenv("RUN_GITHUB_TESTS"):
        print("Set RUN_GITHUB_TESTS=true to run this cleanup script")
        exit(1)
    
    asyncio.run(cleanup_test_branches())
