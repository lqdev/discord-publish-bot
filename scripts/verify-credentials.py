#!/usr/bin/env python3
"""
Test GitHub connection and repository access.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from github import Github

def test_github_connection():
    """Test GitHub API connection and repository access."""
    print("🔍 Testing GitHub connection...")
    
    # Load environment variables with .env priority
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    github_token = os.getenv('GITHUB_TOKEN')
    github_repo = os.getenv('GITHUB_REPO')
    
    if not github_token:
        print("❌ GITHUB_TOKEN not found in environment")
        return False
        
    if not github_repo:
        print("❌ GITHUB_REPO not found in environment")
        return False
    
    try:
        # Test basic GitHub connection
        print(f"🔑 Testing token: {github_token[:10]}...")
        g = Github(github_token)
        
        # Test user access
        user = g.get_user()
        print(f"✅ Authenticated as: {user.login}")
        
        # Test repository access
        print(f"📁 Testing repository: {github_repo}")
        repo = g.get_repo(github_repo)
        print(f"✅ Repository access confirmed: {repo.full_name}")
        print(f"📊 Repository info:")
        print(f"   - Private: {repo.private}")
        print(f"   - Default branch: {repo.default_branch}")
        print(f"   - Permissions: {repo.permissions}")
        
        # Test write access by checking if we can create issues
        if repo.permissions.push:
            print("✅ Write access confirmed")
        else:
            print("⚠️  Limited access - may not be able to push content")
            
        return True
        
    except Exception as e:
        print(f"❌ GitHub connection failed: {e}")
        if "401" in str(e):
            print("💡 This usually means:")
            print("   1. Token is expired or invalid")
            print("   2. Token doesn't have required permissions")
            print("   3. Repository name is incorrect")
        return False

if __name__ == "__main__":
    success = test_github_connection()
    sys.exit(0 if success else 1)
