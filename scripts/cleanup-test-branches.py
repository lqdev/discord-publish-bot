#!/usr/bin/env python3
"""
Cleanup script to remove test branches from the repository.
Dynamically finds and removes test branches from recent PRs.
"""
import asyncio
import os
import sys
import requests
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from publishing_api.github_client import GitHubClient
from publishing_api.config import APIConfig

async def cleanup_test_branches():
    """Clean up test branches with dynamic detection."""
    print("🧹 Cleaning up test branches")
    print("=" * 50)
    
    # Load configuration
    config = APIConfig.from_env()
    print(f"✓ Config loaded: {config.github_repo}")
    
    # GitHub API headers
    headers = {
        "Authorization": f"token {config.github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    base_url = f"https://api.github.com/repos/{config.github_repo}"
    
    # Get recent PRs to find test branches dynamically
    print("🔍 Fetching recent PRs to identify test branches...")
    
    try:
        # Get recent PRs (last 50)
        prs_url = f"{base_url}/pulls?state=all&sort=created&direction=desc&per_page=50"
        response = requests.get(prs_url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch PRs: {response.status_code}")
            return
            
        prs = response.json()
        test_branches = []
        
        for pr in prs:
            branch_name = pr["head"]["ref"]
            pr_title = pr["title"]
            pr_number = pr["number"]
            created_at = pr["created_at"]
            
            # Check if it's a test branch based on patterns
            test_patterns = [
                "content/discord-bot/",
                "debug/",
                "test-",
                "e2e-",
                "-test-",
                "-e2e-"
            ]
            
            title_test_keywords = [
                "test",
                "e2e",
                "testing",
                "debug"
            ]
            
            is_test_branch = (
                any(pattern in branch_name.lower() for pattern in test_patterns) or
                any(keyword in pr_title.lower() for keyword in title_test_keywords)
            )
            
            if is_test_branch:
                test_branches.append({
                    "name": branch_name,
                    "pr_number": pr_number,
                    "title": pr_title,
                    "created_at": created_at
                })
                print(f"📝 Found test branch: {branch_name} (PR #{pr_number})")
        
        print(f"\n🎯 Found {len(test_branches)} test branches to clean up")
        
        if not test_branches:
            print("✅ No test branches found - repository is clean!")
            return
        
        # Delete branches using direct API calls for reliability
        success_count = 0
        failed_count = 0
        
        for branch_info in test_branches:
            branch_name = branch_info["name"]
            pr_number = branch_info["pr_number"]
            
            print(f"🗑️ Attempting to delete branch: {branch_name} (PR #{pr_number})")
            
            try:
                # Delete the branch
                delete_url = f"{base_url}/git/refs/heads/{branch_name}"
                response = requests.delete(delete_url, headers=headers)
                
                if response.status_code == 204:
                    print(f"✓ Deleted: {branch_name}")
                    success_count += 1
                elif response.status_code == 422:
                    error_detail = response.json().get("message", "Unknown error")
                    if "reference does not exist" in error_detail.lower() or "not found" in error_detail.lower():
                        print(f"ℹ️ Branch {branch_name} already deleted")
                        success_count += 1  # Count as success since it's gone
                    else:
                        print(f"ℹ️ Branch {branch_name} protected or cannot be deleted: {error_detail}")
                        failed_count += 1
                elif response.status_code == 404:
                    print(f"ℹ️ Branch {branch_name} already deleted or not found")
                    success_count += 1  # Count as success since it's gone
                else:
                    print(f"⚠️ Failed to delete {branch_name}: {response.status_code}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"⚠️ Error deleting {branch_name}: {e}")
                failed_count += 1
        
        print(f"\n📊 Cleanup Summary:")
        print(f"✓ Successfully deleted: {success_count}")
        print(f"⚠️ Failed or not found: {failed_count}")
        print(f"🎉 Cleanup completed!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    # Safety check - require explicit confirmation
    if not os.getenv("RUN_GITHUB_TESTS"):
        print("⚠️ Branch cleanup requires RUN_GITHUB_TESTS=true environment variable")
        print("This is a safety measure to prevent accidental deletions.")
        print("Set the environment variable and run again to proceed.")
        print()
        print("Example:")
        print("  export RUN_GITHUB_TESTS=true  # Linux/Mac")
        print("  $env:RUN_GITHUB_TESTS='true'  # PowerShell")
        print("  set RUN_GITHUB_TESTS=true     # Command Prompt")
        exit(1)
    
    asyncio.run(cleanup_test_branches())
