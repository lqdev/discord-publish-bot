#!/usr/bin/env python3
"""
Development setup script for Discord Publish Bot using UV.

This script automates the setup process for new developers.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(cmd, check=True, shell=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=shell, 
            check=check, 
            capture_output=True, 
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return None


def check_uv_installed():
    """Check if UV is installed."""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ UV is installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ UV is not installed")
    return False


def install_uv():
    """Install UV package manager."""
    print("Installing UV...")
    
    system = platform.system().lower()
    
    if system == "windows":
        cmd = 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
    else:
        cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
    
    result = run_command(cmd)
    if result and result.returncode == 0:
        print("✅ UV installed successfully")
        return True
    else:
        print("❌ Failed to install UV")
        return False


def setup_virtual_environment():
    """Set up Python virtual environment with UV."""
    print("Setting up virtual environment...")
    
    # Create virtual environment
    result = run_command("uv venv")
    if not result or result.returncode != 0:
        print("❌ Failed to create virtual environment")
        return False
    
    print("✅ Virtual environment created")
    return True


def install_dependencies():
    """Install project dependencies."""
    print("Installing dependencies...")
    
    # Install dependencies
    result = run_command("uv pip install -e \".[dev]\"")
    if not result or result.returncode != 0:
        print("❌ Failed to install dependencies")
        return False
    
    print("✅ Dependencies installed successfully")
    return True


def setup_environment_file():
    """Set up environment configuration file."""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_example.exists() and not env_file.exists():
        print("Setting up environment configuration...")
        
        # Copy example file
        env_file.write_text(env_example.read_text())
        print("✅ Created .env file from template")
        print("📝 Please edit .env with your configuration before running the bot")
        return True
    elif env_file.exists():
        print("✅ Environment file already exists")
        return True
    else:
        print("❌ .env.example file not found")
        return False


def run_tests():
    """Run basic tests to verify setup."""
    print("Running basic tests...")
    
    result = run_command("uv run pytest tests/test_basic.py -v")
    if result and result.returncode == 0:
        print("✅ Basic tests passed")
        return True
    else:
        print("❌ Tests failed")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit .env file with your Discord and GitHub configuration")
    print("2. Set up Discord bot application at https://discord.com/developers/applications")
    print("3. Create GitHub personal access token with repo permissions")
    print("\nTo start development:")
    
    system = platform.system().lower()
    if system == "windows":
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    
    print("   uv run python src/discord_bot/main.py")
    print("\nFor more information, see README.md")


def main():
    """Main setup function."""
    print("Discord Publish Bot - Development Setup")
    print("="*40)
    
    # Check if UV is installed
    if not check_uv_installed():
        if not install_uv():
            print("Please install UV manually: https://github.com/astral-sh/uv")
            sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment file
    if not setup_environment_file():
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("⚠️  Tests failed, but setup is complete. Check your configuration.")
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
