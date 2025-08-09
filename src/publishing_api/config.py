"""
Configuration management for Publishing API.

Handles environment variable loading and validation.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class APIConfig:
    """Configuration class for Publishing API settings."""

    api_key: str
    discord_user_id: str
    github_token: str
    github_repo: str
    github_branch: str = "main"
    site_base_url: Optional[str] = None
    log_level: str = "INFO"
    environment: str = "development"

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create configuration from environment variables."""
        # Load .env file first to ensure .env values override system env
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # Required configuration
        api_key = os.getenv("API_KEY")
        discord_user_id = os.getenv("DISCORD_USER_ID")
        github_token = os.getenv("GITHUB_TOKEN")
        github_repo = os.getenv("GITHUB_REPO")

        # Validate required configuration
        if not api_key:
            raise ValueError("API_KEY environment variable is required")
        if not discord_user_id:
            raise ValueError("DISCORD_USER_ID environment variable is required")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        if not github_repo:
            raise ValueError("GITHUB_REPO environment variable is required")

        # Optional configuration with defaults
        github_branch = os.getenv("GITHUB_BRANCH", "main")
        site_base_url = os.getenv("SITE_BASE_URL")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        environment = os.getenv("ENVIRONMENT", "development")

        return cls(
            api_key=api_key,
            discord_user_id=discord_user_id,
            github_token=github_token,
            github_repo=github_repo,
            github_branch=github_branch,
            site_base_url=site_base_url,
            log_level=log_level,
            environment=environment,
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if len(self.api_key) < 16:
            raise ValueError("API key must be at least 16 characters long")

        if not self.discord_user_id.isdigit():
            raise ValueError("Discord user ID must be numeric")

        if not self.github_token.startswith(("ghp_", "github_pat_")):
            raise ValueError("Invalid GitHub token format")

        if "/" not in self.github_repo:
            raise ValueError("GitHub repo must be in format 'owner/repository'")

        if self.site_base_url and not self.site_base_url.startswith(
            ("http://", "https://")
        ):
            raise ValueError("Site base URL must start with http:// or https://")

    @property
    def github_repo_owner(self) -> str:
        """Extract repository owner from github_repo."""
        return self.github_repo.split("/")[0]

    @property
    def github_repo_name(self) -> str:
        """Extract repository name from github_repo."""
        return self.github_repo.split("/")[1]
