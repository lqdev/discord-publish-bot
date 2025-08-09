"""
Publishing service for processing Discord messages and creating markdown files.

Implements content processing, frontmatter generation, and GitHub publishing
with branch/PR workflow and target site schema compliance.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import yaml

from .config import APIConfig
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class PublishingService:
    """Service for processing Discord posts and publishing to GitHub with enhanced workflow."""

    # Content type to source directory mapping (luisquintanilla.me structure)
    CONTENT_TYPE_DIRECTORIES = {
        "note": "_src/feed",
        "response": "_src/responses", 
        "bookmark": "_src/responses",  # Bookmarks are responses with response_type
        "media": "_src/media",
    }

    # Frontmatter schema templates for target site compliance
    FRONTMATTER_SCHEMAS = {
        "note": {
            "required_fields": ["post_type", "title", "published_date"],
            "optional_fields": ["tags"],
            "field_mappings": {
                "type": "post_type",
                "date": "published_date",
            }
        },
        "response": {
            "required_fields": ["title", "response_type", "dt_published", "dt_updated"],
            "optional_fields": ["targeturl", "tags"],
            "field_mappings": {
                "type": "response_type",
                "date": "dt_published",
            }
        },
        "bookmark": {
            "required_fields": ["title", "targeturl", "response_type", "dt_published", "dt_updated"],
            "optional_fields": ["tags"],
            "field_mappings": {
                "type": "response_type",
                "date": "dt_published",
                "url": "targeturl",
            }
        },
        "media": {
            "required_fields": ["post_type", "title", "published_date"],
            "optional_fields": ["tags", "media_url", "media_type"],
            "field_mappings": {
                "type": "post_type", 
                "date": "published_date",
            }
        }
    }

    def __init__(self, github_client: GitHubClient, config: APIConfig):
        self.github_client = github_client
        self.config = config

    async def publish_post(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Process Discord message and publish to GitHub using branch/PR workflow.

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
        if post_type not in self.CONTENT_TYPE_DIRECTORIES:
            raise ValueError(f"Invalid post type: {post_type}")

        # Convert frontmatter to target site schema
        target_frontmatter = self.convert_to_target_schema(post_type, frontmatter, content)

        # Generate markdown content
        markdown_content = self.build_markdown_file(target_frontmatter, content)

        # Generate filename and filepath 
        filename = self.generate_filename(post_type, target_frontmatter, content)
        directory = self.CONTENT_TYPE_DIRECTORIES[post_type]
        filepath = f"{directory}/{filename}"

        # Generate branch name
        message_id = f"msg-{datetime.utcnow().strftime('%H%M%S')}"  # Simulate message ID
        branch_name = self.github_client.generate_branch_name(
            content_type=post_type,
            message_id=message_id,
            user_id=user_id
        )

        # Generate PR template
        content_preview = content[:100] if content else target_frontmatter.get("title", "Untitled")
        pr_title, pr_body = self.github_client.generate_pr_template(
            content_type=post_type,
            content_preview=content_preview,
            user_id=user_id,
            message_id=message_id,
            validation_results=self.validate_content(post_type, target_frontmatter, content)
        )

        # Commit message
        commit_message = f"Add {post_type} post from Discord user {user_id}"

        # Use enhanced commit workflow (branch + PR)
        try:
            workflow_result = await self.github_client.commit_file_to_branch(
                filepath=filepath,
                content=markdown_content,
                commit_message=commit_message,
                branch_name=branch_name,
                create_pr=True,
                pr_title=pr_title,
                pr_body=pr_body,
            )

            # Build response
            result = {
                "status": "success",
                "workflow": "branch_and_pr",
                "filepath": filepath,
                "branch_name": workflow_result["branch_name"],
                "commit_sha": workflow_result["commit_sha"],
                "pr_url": workflow_result["pr_url"],
                "directory": directory,
                "filename": filename,
            }

            # Add site URL if configured (will be available after PR merge)
            if self.config.site_base_url:
                slug = filename.replace(".md", "")
                # Map directory to URL structure
                url_path = directory.replace("_src/", "").replace("_src\\", "")
                result["site_url_after_merge"] = f"{self.config.site_base_url}/{url_path}/{slug}/"

            return result

        except Exception as e:
            logger.error(f"Enhanced publishing workflow failed: {str(e)}")
            raise Exception(f"Failed to publish post: {str(e)}")

    def convert_to_target_schema(
        self, post_type: str, source_frontmatter: Dict[str, Any], content: str
    ) -> Dict[str, Any]:
        """
        Convert frontmatter to match luisquintanilla.me schema exactly.
        Based on VS Code metadata snippets.

        Args:
            post_type: Type of post
            source_frontmatter: Original frontmatter from Discord parsing
            content: Post content

        Returns:
            Converted frontmatter following target site patterns
        """
        target_frontmatter = {}

        # Handle date conversion to target site format: "YYYY-MM-DD HH:MM -05:00"
        source_date = source_frontmatter.get("date")
        if source_date:
            try:
                dt = datetime.fromisoformat(source_date.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%Y-%m-%d %H:%M -05:00")
            except ValueError:
                # Fallback to current time
                now = datetime.now(timezone.utc)
                formatted_date = now.strftime("%Y-%m-%d %H:%M -05:00")
        else:
            now = datetime.now(timezone.utc)
            formatted_date = now.strftime("%Y-%m-%d %H:%M -05:00")

        # Handle title - clean and quote
        title = source_frontmatter.get("title")
        if title:
            # Remove any existing quotes
            if isinstance(title, str):
                title = title.strip('"\'')
        elif content:
            # Generate title from content
            first_line = content.strip().split("\n")[0]
            title = re.sub(r"[#*`_\[\]()]", "", first_line)[:80].strip()
        
        title = title or "Untitled"
        target_frontmatter["title"] = title  # Keep as string, YAML will handle quoting

        # Handle tags - always as array format ["tag1", "tag2"]
        tags = source_frontmatter.get("tags", [])
        if isinstance(tags, str):
            # Convert string to list
            tags = [tag.strip().strip('"\'') for tag in tags.split(",") if tag.strip()]
        if not tags:
            # Add default tags
            tags = ["discord", "automated"]
        target_frontmatter["tags"] = tags

        # Post type specific formatting based on VS Code snippets
        if post_type == "note":
            # Note Feed metadata format
            target_frontmatter["post_type"] = "note"
            target_frontmatter["published_date"] = formatted_date

        elif post_type == "media":
            # Media posts use photo format for images
            target_frontmatter["post_type"] = "photo"
            target_frontmatter["published_date"] = formatted_date
            
            # Add media-specific fields if available
            media_url = source_frontmatter.get("media_url")
            if media_url:
                target_frontmatter["media_url"] = media_url.strip('"\'') if isinstance(media_url, str) else media_url
            
            alt_text = source_frontmatter.get("alt_text")
            if alt_text:
                target_frontmatter["alt_text"] = alt_text.strip('"\'') if isinstance(alt_text, str) else alt_text

        elif post_type in ["response", "bookmark"]:
            # Response/Bookmark metadata format
            target_frontmatter["dt_published"] = formatted_date
            target_frontmatter["dt_updated"] = formatted_date
            
            # Set response_type
            if post_type == "bookmark":
                target_frontmatter["response_type"] = "bookmark"
            else:
                response_type = source_frontmatter.get("response_type", "reply")
                if isinstance(response_type, str):
                    response_type = response_type.strip('"\'')
                target_frontmatter["response_type"] = response_type
            
            # Handle target URL (targeturl in your schema)
            target_url = (source_frontmatter.get("url") or 
                         source_frontmatter.get("targeturl") or 
                         source_frontmatter.get("in_reply_to"))
            if target_url:
                if isinstance(target_url, str):
                    target_url = target_url.strip('"\'')
                target_frontmatter["targeturl"] = target_url

        return target_frontmatter

    def validate_content(
        self, post_type: str, frontmatter: Dict[str, Any], content: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate content against target site requirements.

        Args:
            post_type: Type of post
            frontmatter: Frontmatter dictionary
            content: Post content

        Returns:
            Dictionary of validation results
        """
        results = {}
        schema = self.FRONTMATTER_SCHEMAS.get(post_type, {})

        # Validate required fields
        required_fields = schema.get("required_fields", [])
        missing_fields = [field for field in required_fields if field not in frontmatter]
        
        results["required_fields"] = {
            "passed": len(missing_fields) == 0,
            "message": f"All required fields present" if len(missing_fields) == 0 else f"Missing: {', '.join(missing_fields)}"
        }

        # Validate content length
        content_length = len(content.strip()) if content else 0
        results["content_length"] = {
            "passed": content_length > 0,
            "message": f"Content length: {content_length} characters" if content_length > 0 else "No content provided"
        }

        # Validate specific post type requirements
        if post_type in ["response", "bookmark"]:
            has_targeturl = "targeturl" in frontmatter and frontmatter["targeturl"]
            results["target_url"] = {
                "passed": has_targeturl,
                "message": "Target URL provided" if has_targeturl else "Target URL missing for response/bookmark"
            }

        # Validate title
        has_title = "title" in frontmatter and frontmatter["title"] and frontmatter["title"] != "Untitled"
        results["title_quality"] = {
            "passed": has_title,
            "message": "Descriptive title provided" if has_title else "Generic or missing title"
        }

        return results

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
            content_for_slug = content or frontmatter.get("title", "")
            frontmatter["slug"] = self.generate_slug(content_for_slug)

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
        # Generate YAML frontmatter with proper formatting
        yaml_content = yaml.safe_dump(
            frontmatter, 
            sort_keys=False, 
            allow_unicode=True, 
            default_flow_style=False,
            width=float('inf')  # Prevent line wrapping
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
        date_str = (
            frontmatter.get("published_date") or 
            frontmatter.get("dt_published") or 
            datetime.utcnow().strftime("%Y-%m-%d %H:%M -05:00")
        )

        # Parse date and format as YYYY-MM-DD
        try:
            # Handle various date formats from target site
            if " " in date_str and not date_str.endswith("Z"):
                # Format: "2025-08-08 10:30 -05:00"
                date_part = date_str.split(" ")[0]
                date_obj = datetime.strptime(date_part, "%Y-%m-%d")
            else:
                # ISO format or other
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date_prefix = date_obj.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_prefix = datetime.utcnow().strftime("%Y-%m-%d")

        # Get slug
        slug = frontmatter.get("slug", self.generate_slug(content or frontmatter.get("title", "")))

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
