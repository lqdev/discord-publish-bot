"""
Publishing service for processing Discord messages and creating markdown files.

Implements content processing, frontmatter generation, and GitHub publishing.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import yaml

from .config import APIConfig
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class PublishingService:
    """Service for processing Discord posts and publishing to GitHub."""

    # Post type to folder mapping
    POST_TYPE_FOLDERS = {
        "note": "notes",
        "response": "responses",
        "bookmark": "bookmarks",
        "media": "media",
    }

    def __init__(self, github_client: GitHubClient, config: APIConfig):
        self.github_client = github_client
        self.config = config

    async def publish_post(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Process Discord message and publish to GitHub.

        Args:
            message: Discord command message with content
            user_id: Discord user ID

        Returns:
            Dictionary with publishing result information

        Raises:
            ValueError: If message format is invalid
            Exception: If publishing fails
        """
        # Parse message
        post_type, frontmatter, content = self.parse_discord_message(message)

        # Validate post type
        if post_type not in self.POST_TYPE_FOLDERS:
            raise ValueError(f"Invalid post type: {post_type}")

        # Generate markdown content
        markdown_content = self.build_markdown_file(frontmatter, content)

        # Generate filename and filepath
        filename = self.generate_filename(post_type, frontmatter, content)
        folder = self.POST_TYPE_FOLDERS[post_type]
        filepath = f"posts/{folder}/{filename}"

        # Commit to GitHub
        commit_message = f"Add {post_type} post from Discord user {user_id}"
        commit_sha = await self.github_client.commit_file(
            filepath=filepath,
            content=markdown_content,
            commit_message=commit_message,
            branch=self.config.github_branch,
        )

        # Build response
        result = {"status": "success", "filepath": filepath, "commit_sha": commit_sha}

        # Add site URL if configured
        if self.config.site_base_url:
            slug = filename.replace(".md", "")
            result["site_url"] = f"{self.config.site_base_url}/posts/{folder}/{slug}"

        return result

    def parse_discord_message(self, message: str) -> Tuple[str, Dict[str, Any], str]:
        """
        Parse Discord message into post type, frontmatter, and content.

        Args:
            message: Discord command message

        Returns:
            Tuple of (post_type, frontmatter_dict, content_string)

        Raises:
            ValueError: If message format is invalid
        """
        lines = message.strip().split("\n")

        if not lines:
            raise ValueError("Empty message")

        # Extract post type from command line
        command_line = lines[0].strip()
        if not command_line.startswith("/post "):
            raise ValueError("Message must start with '/post' command")

        command_parts = command_line.split()
        if len(command_parts) < 2:
            raise ValueError("Post type not specified in command")

        post_type = command_parts[1].lower()

        # Initialize frontmatter with defaults
        frontmatter = {"type": post_type, "date": datetime.utcnow().isoformat() + "Z"}

        content_start = 1

        # Parse frontmatter if present
        if len(lines) > 1 and lines[1].strip() == "---":
            frontmatter_end = None

            # Find end of frontmatter
            for i, line in enumerate(lines[2:], start=2):
                if line.strip() == "---":
                    frontmatter_end = i
                    content_start = i + 1
                    break

            if frontmatter_end is None:
                raise ValueError("Unclosed frontmatter section")

            # Parse frontmatter lines
            for line in lines[2:frontmatter_end]:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if ":" not in line:
                    continue

                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Handle special value types
                if value.startswith("[") and value.endswith("]"):
                    # Parse array values
                    try:
                        frontmatter[key] = yaml.safe_load(value)
                    except yaml.YAMLError:
                        frontmatter[key] = value
                else:
                    frontmatter[key] = value

        # Extract content
        content = "\n".join(lines[content_start:]).strip()

        # Generate slug if not provided
        if "slug" not in frontmatter:
            frontmatter["slug"] = self.generate_slug(
                content or frontmatter.get("title", "")
            )

        # Generate title if not provided and content exists
        if "title" not in frontmatter and content:
            first_line = content.strip().split("\n")[0]
            # Remove markdown formatting for title
            title = re.sub(r"[#*`_\[\]()]", "", first_line)
            frontmatter["title"] = title[:80].strip()

        return post_type, frontmatter, content

    def build_markdown_file(self, frontmatter: Dict[str, Any], content: str) -> str:
        """
        Build complete markdown file with YAML frontmatter.

        Args:
            frontmatter: Frontmatter dictionary
            content: Content string

        Returns:
            Complete markdown file content
        """
        # Generate YAML frontmatter
        yaml_content = yaml.safe_dump(
            frontmatter, sort_keys=False, allow_unicode=True, default_flow_style=False
        )

        # Combine frontmatter and content
        return f"---\n{yaml_content}---\n\n{content}"

    def generate_slug(self, text: str) -> str:
        """
        Generate URL-friendly slug from text.

        Args:
            text: Input text

        Returns:
            URL-friendly slug
        """
        if not text:
            return "untitled"

        # Take first 50 characters
        snippet = text.strip()[:50].lower()

        # Remove markdown formatting
        snippet = re.sub(r"[#*`_\[\]()]", "", snippet)

        # Replace non-alphanumeric characters with hyphens
        slug = re.sub(r"[^a-z0-9\s-]", "", snippet)
        slug = re.sub(r"\s+", "-", slug.strip())
        slug = re.sub(r"-+", "-", slug)

        # Remove leading/trailing hyphens
        slug = slug.strip("-")

        return slug or "untitled"

    def generate_filename(
        self, post_type: str, frontmatter: Dict[str, Any], content: str
    ) -> str:
        """
        Generate filename with date prefix and slug.

        Args:
            post_type: Type of post
            frontmatter: Frontmatter dictionary
            content: Content string

        Returns:
            Generated filename
        """
        # Use date from frontmatter or current date
        date_str = frontmatter.get("date", datetime.utcnow().isoformat() + "Z")

        # Parse date and format as YYYY-MM-DD
        try:
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date_prefix = date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_prefix = datetime.utcnow().strftime("%Y-%m-%d")

        # Get slug
        slug = frontmatter.get("slug", self.generate_slug(content))

        return f"{date_prefix}-{slug}.md"

    def validate_post_type_requirements(
        self, post_type: str, frontmatter: Dict[str, Any]
    ) -> None:
        """
        Validate that required fields are present for post type.

        Args:
            post_type: Type of post
            frontmatter: Frontmatter dictionary

        Raises:
            ValueError: If required fields are missing
        """
        requirements = {
            "note": [],  # No specific requirements
            "response": ["response_type"],
            "bookmark": ["url"],
            "media": ["media_url"],
        }

        required_fields = requirements.get(post_type, [])

        for field in required_fields:
            if field not in frontmatter or not frontmatter[field]:
                raise ValueError(
                    f"Required field '{field}' missing for {post_type} post"
                )
