#!/usr/bin/env python3
"""
Security verification script for Discord Publish Bot.

Checks that security best practices are properly implemented.
"""

import os
import subprocess
import sys
from pathlib import Path


def check_gitignore():
    """Check that .gitignore exists and contains security patterns."""
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        return False, ".gitignore file not found"
    
    with open(gitignore_path) as f:
        content = f.read()
    
    required_patterns = [".env", "*.env", "*.key", "*.log", "__pycache__"]
    missing = [pattern for pattern in required_patterns if pattern not in content]
    
    if missing:
        return False, f"Missing patterns in .gitignore: {missing}"
    
    return True, ".gitignore properly configured"


def check_env_files():
    """Check that .env files are properly handled."""
    # Check .env.example exists
    if not Path(".env.example").exists():
        return False, ".env.example template not found"
    
    # Check .env exists locally
    if not Path(".env").exists():
        return False, ".env file not found - copy from .env.example"
    
    # Check .env is not tracked in git
    try:
        result = subprocess.run(
            ["git", "ls-files", ".env"], 
            capture_output=True, 
            text=True,
            check=False
        )
        if result.stdout.strip():
            return False, ".env file is tracked in git - security risk!"
    except subprocess.SubprocessError:
        return False, "Cannot check git status"
    
    return True, "Environment files properly configured"


def check_credentials():
    """Check that credentials are not placeholder values."""
    env_path = Path(".env")
    if not env_path.exists():
        return False, ".env file not found"
    
    with open(env_path) as f:
        content = f.read()
    
    # Check for placeholder values
    placeholders = [
        "your_discord_bot_token_here",
        "your_discord_user_id_here", 
        "generate_32_character_secure_key_here",
        "your_github_personal_access_token",
        "username/repository-name"
    ]
    
    found_placeholders = [p for p in placeholders if p in content]
    
    if found_placeholders:
        return False, f"Found placeholder values: {found_placeholders}"
    
    # Additional Discord-specific validation
    issues = []
    
    # Check Discord bot token format (should start with specific pattern)
    if "DISCORD_BOT_TOKEN=" in content:
        token_line = [line for line in content.split('\n') if line.startswith('DISCORD_BOT_TOKEN=')]
        if token_line:
            token_value = token_line[0].split('=', 1)[1].strip()
            if len(token_value) < 50:  # Discord bot tokens are typically 59+ characters
                issues.append("Discord bot token appears too short")
    
    # Check Discord user ID format (should be numeric snowflake)
    if "DISCORD_USER_ID=" in content:
        user_id_line = [line for line in content.split('\n') if line.startswith('DISCORD_USER_ID=')]
        if user_id_line:
            user_id_value = user_id_line[0].split('=', 1)[1].strip()
            if not user_id_value.isdigit() or len(user_id_value) < 17:
                issues.append("Discord user ID should be 17+ digit number")
    
    # Check API key length
    if "API_KEY=" in content:
        api_key_line = [line for line in content.split('\n') if line.startswith('API_KEY=')]
        if api_key_line:
            api_key_value = api_key_line[0].split('=', 1)[1].strip()
            if len(api_key_value) < 32:
                issues.append("API key should be at least 32 characters")
    
    # Check GitHub repo format
    if "GITHUB_REPO=" in content:
        repo_line = [line for line in content.split('\n') if line.startswith('GITHUB_REPO=')]
        if repo_line:
            repo_value = repo_line[0].split('=', 1)[1].strip()
            if '/' not in repo_value or repo_value.count('/') != 1:
                issues.append("GitHub repo should be in format 'username/repository'")
    
    if issues:
        return False, f"Credential format issues: {', '.join(issues)}"
    
    return True, "No placeholder values found in .env"


def main():
    """Run all security checks."""
    print("🔒 Discord Publish Bot Security Verification")
    print("=" * 50)
    
    checks = [
        ("GitIgnore Configuration", check_gitignore),
        ("Environment Files", check_env_files),
        ("Credential Setup", check_credentials),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {name}: {message}")
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"❌ ERROR {name}: {e}")
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 All security checks passed! Project is secure.")
        return 0
    else:
        print("⚠️  Security issues found. Please fix before proceeding.")
        print("\nSee docs/team/security-guidelines.md for setup help.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
