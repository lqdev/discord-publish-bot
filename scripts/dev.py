#!/usr/bin/env python3
"""
Development scripts for Discord Publish Bot.

Quick commands for common development tasks.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_cmd(cmd, description=""):
    """Run a command with UV."""
    if description:
        print(f"📋 {description}")
    print(f"🔧 Running: uv run {cmd}")
    
    result = subprocess.run(f"uv run {cmd}", shell=True)
    return result.returncode == 0


def dev_server():
    """Start development servers."""
    print("🚀 Starting development servers...")
    print("📝 Make sure your .env file is configured first!")
    print("\n1. Publishing API will start on http://localhost:8000")
    print("2. Discord Bot will start in a separate process")
    print("3. Use Ctrl+C to stop both services")
    
    # You could implement concurrent server startup here
    print("\nTo start manually:")
    print("Terminal 1: uv run uvicorn src.publishing_api.main:app --reload --port 8000")
    print("Terminal 2: uv run python src/discord_bot/main.py")


def test_all():
    """Run all tests."""
    return run_cmd("pytest", "Running all tests")


def test_fast():
    """Run fast tests only."""
    return run_cmd('pytest -m "not slow"', "Running fast tests")


def test_coverage():
    """Run tests with coverage."""
    return run_cmd("pytest --cov=src --cov-report=html", "Running tests with coverage")


def format_code():
    """Format code with black and isort."""
    print("🎨 Formatting code...")
    black_ok = run_cmd("black src/ tests/", "Formatting with Black")
    isort_ok = run_cmd("isort src/ tests/", "Sorting imports with isort")
    
    if black_ok and isort_ok:
        print("✅ Code formatting completed")
        return True
    else:
        print("❌ Code formatting failed")
        return False


def check_types():
    """Run type checking."""
    return run_cmd("mypy src/", "Running type checks")


def lint_all():
    """Run all linting and formatting."""
    print("🔍 Running full code quality checks...")
    
    format_ok = format_code()
    test_ok = test_fast()
    
    if format_ok and test_ok:
        print("✅ All checks passed")
        return True
    else:
        print("❌ Some checks failed")
        return False


def install_deps():
    """Install/update dependencies."""
    return run_cmd("pip install -e \".[dev]\"", "Installing dependencies")


def build_package():
    """Build the package."""
    return run_cmd("python -m build", "Building package")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Discord Publish Bot development tools")
    parser.add_argument("command", choices=[
        "dev", "test", "test-fast", "test-cov", 
        "format", "lint", "types", "install", "build"
    ], help="Command to run")
    
    args = parser.parse_args()
    
    commands = {
        "dev": dev_server,
        "test": test_all,
        "test-fast": test_fast,
        "test-cov": test_coverage,
        "format": format_code,
        "lint": lint_all,
        "types": check_types,
        "install": install_deps,
        "build": build_package,
    }
    
    command_func = commands.get(args.command)
    if command_func:
        success = command_func()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
