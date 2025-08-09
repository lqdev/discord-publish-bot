"""
Publishing service for processing Discord posts and creating markdown files.

Modernized publishing service with proper type safety and error handling.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

import yaml

from ..config import GitHubSettings, PublishingSettings
from ..shared import (
    PostData, 
    PostType, 
    PublishResult, 
    PublishingError,
    ContentValidationError,
    FrontmatterError,
    generate_filename,
    format_frontmatter,
    parse_tags,
    sanitize_content,
    validate_url
)
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class PublishingService:
    """
    Modern publishing service for processing Discord posts and creating markdown files.
    
    Handles content processing, frontmatter generation, and GitHub publishing
    with proper validation and error handling.
    """

    # Content type to source directory mapping
    CONTENT_TYPE_DIRECTORIES = {
        PostType.NOTE: "_src/feed",
        PostType.RESPONSE: "_src/responses", 
        PostType.BOOKMARK: "_src/responses",  # Bookmarks are responses with response_type
        PostType.MEDIA: "_src/media",
    }

    # Frontmatter schema templates for target site compliance
    FRONTMATTER_SCHEMAS = {
        PostType.NOTE: {
            "required_fields": ["post_type", "title", "published_date"],
            "optional_fields": ["tags"],
            "field_mappings": {
                "type": "post_type",
                "date": "published_date",
            }
        },
        PostType.RESPONSE: {
            "required_fields": ["title", "target_url", "response_type", "dt_published", "dt_updated"],
            "optional_fields": ["tags"],
            "field_mappings": {
                "type": "response_type",
                "date": "dt_published",
            }
        },
        PostType.BOOKMARK: {
            "required_fields": ["title", "target_url", "response_type", "dt_published", "dt_updated"],
            "optional_fields": ["tags"],
            "field_mappings": {
                "type": "response_type",
                "date": "dt_published",
                "url": "target_url",
            }
        },
        PostType.MEDIA: {
            "required_fields": ["post_type", "title", "published_date"],
            "optional_fields": ["tags", "media_url", "media_type"],
            "field_mappings": {
                "type": "post_type", 
                "date": "published_date",
            }
        }
    }

    def __init__(
        self, 
        github_client: GitHubClient, 
        github_settings: GitHubSettings,
        publishing_settings: PublishingSettings
    ):
        """
        Initialize publishing service.
        
        Args:
            github_client: GitHub client for repository operations
            github_settings: GitHub configuration settings
            publishing_settings: Publishing configuration settings
        """
        self.github_client = github_client
        self.github_settings = github_settings
        self.publishing_settings = publishing_settings

    async def publish_post(self, post_data: PostData) -> PublishResult:
        """
        Process post data and publish to GitHub.

        Args:
            post_data: Structured post data

        Returns:
            Publishing result with success/failure information

        Raises:
            PublishingError: If publishing fails
        """
        try:
            logger.info(f"Publishing {post_data.post_type} post: {post_data.title}")
            
            # Validate post data
            self._validate_post_data(post_data)
            
            # Generate frontmatter
            frontmatter = self._generate_frontmatter(post_data)
            
            # Build markdown content
            content = self._build_markdown_content(frontmatter, post_data.content)
            
            # Generate filename and path
            filename = generate_filename(post_data.post_type, post_data.title)
            directory = self.CONTENT_TYPE_DIRECTORIES[post_data.post_type]
            filepath = f"{directory}/{filename}"
            
            # Commit to GitHub
            commit_info = await self.github_client.create_commit(
                filename=filepath,
                content=content,
                message=f"Add {post_data.post_type.value} post: {post_data.title}",
                branch=self.github_settings.branch
            )
            
            # Generate site URL
            site_url = self._generate_site_url(filepath)
            
            result = PublishResult(
                success=True,
                message=f"{post_data.post_type.value.title()} post published successfully",
                filename=filename,
                filepath=filepath,
                commit_sha=commit_info["sha"],
                branch_name=self.github_settings.branch,
                file_url=commit_info["url"],
                site_url=site_url
            )
            
            logger.info(f"Successfully published post: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to publish post: {e}")
            return PublishResult(
                success=False,
                message=f"Failed to publish post: {str(e)}",
                error_code="PUBLISHING_FAILED",
                error_details={"error": str(e), "post_type": post_data.post_type.value}
            )

    async def publish_from_discord_message(
        self, 
        message: str, 
        user_id: str
    ) -> PublishResult:
        """
        Process Discord message format and publish to GitHub.

        Args:
            message: Discord command message with content
            user_id: Discord user ID

        Returns:
            Publishing result

        Raises:
            PublishingError: If message parsing or publishing fails
        """
        try:
            # Parse Discord message format
            post_data = self._parse_discord_message(message, user_id)
            
            # Publish using structured data
            return await self.publish_post(post_data)
            
        except Exception as e:
            logger.error(f"Failed to publish from Discord message: {e}")
            return PublishResult(
                success=False,
                message=f"Failed to parse Discord message: {str(e)}",
                error_code="MESSAGE_PARSING_FAILED",
                error_details={"error": str(e), "user_id": user_id}
            )

    def _validate_post_data(self, post_data: PostData) -> None:
        """
        Validate post data according to type requirements.
        
        Args:
            post_data: Post data to validate
            
        Raises:
            ContentValidationError: If validation fails
        """
        if not post_data.title.strip():
            raise ContentValidationError("Title is required", field="title")
        
        if not post_data.content.strip():
            raise ContentValidationError("Content is required", field="content")
        
        # Type-specific validation
        if post_data.post_type in (PostType.RESPONSE, PostType.BOOKMARK):
            if not post_data.target_url:
                raise ContentValidationError(
                    f"{post_data.post_type.value} posts require a target URL",
                    field="target_url"
                )
            if not validate_url(post_data.target_url):
                raise ContentValidationError(
                    "Invalid target URL format",
                    field="target_url"
                )
        
        if post_data.post_type == PostType.MEDIA:
            if post_data.media_url and not validate_url(post_data.media_url):
                raise ContentValidationError(
                    "Invalid media URL format",
                    field="media_url"
                )

    def _generate_frontmatter(self, post_data: PostData) -> Dict[str, Any]:
        """
        Generate frontmatter for post type.
        
        Args:
            post_data: Post data
            
        Returns:
            Frontmatter dictionary
            
        Raises:
            FrontmatterError: If frontmatter generation fails
        """
        try:
            now = datetime.now(timezone.utc)
            schema = self.FRONTMATTER_SCHEMAS[post_data.post_type]
            
            # Base frontmatter
            frontmatter = {
                "title": post_data.title,
            }
            
            # Type-specific fields
            if post_data.post_type == PostType.NOTE:
                frontmatter.update({
                    "post_type": "note",
                    "published_date": now.isoformat(),
                })
            
            elif post_data.post_type in (PostType.RESPONSE, PostType.BOOKMARK):
                response_type = "bookmark" if post_data.post_type == PostType.BOOKMARK else "reply"
                frontmatter.update({
                    "target_url": post_data.target_url,
                    "response_type": response_type,
                    "dt_published": now.isoformat(),
                    "dt_updated": now.isoformat(),
                })
            
            elif post_data.post_type == PostType.MEDIA:
                frontmatter.update({
                    "post_type": "media",
                    "published_date": now.isoformat(),
                })
                if post_data.media_url:
                    frontmatter["media_url"] = post_data.media_url
            
            # Add tags if present
            if post_data.tags:
                frontmatter["tags"] = post_data.tags
            
            # Add author if configured
            if self.publishing_settings.default_author:
                frontmatter["author"] = self.publishing_settings.default_author
            
            return frontmatter
            
        except Exception as e:
            logger.error(f"Failed to generate frontmatter: {e}")
            raise FrontmatterError(f"Failed to generate frontmatter: {e}", frontmatter=frontmatter)

    def _build_markdown_content(self, frontmatter: Dict[str, Any], content: str) -> str:
        """
        Build complete markdown file content.
        
        Args:
            frontmatter: Post frontmatter
            content: Post content
            
        Returns:
            Complete markdown content
        """
        # Sanitize content
        clean_content = sanitize_content(content)
        
        # Format frontmatter as YAML
        yaml_frontmatter = format_frontmatter(frontmatter)
        
        # Combine into markdown
        markdown_content = f"---\n{yaml_frontmatter}\n---\n\n{clean_content}\n"
        
        return markdown_content

    def _parse_discord_message(self, message: str, user_id: str) -> PostData:
        """
        Parse Discord command message into structured post data.
        
        Args:
            message: Discord message content
            user_id: Discord user ID
            
        Returns:
            Structured post data
            
        Raises:
            ContentValidationError: If message format is invalid
        """
        lines = message.strip().split('\n')
        
        if not lines:
            raise ContentValidationError("Empty message")
        
        # Parse command line
        command_line = lines[0].strip()
        if not command_line.startswith('/post'):
            raise ContentValidationError("Message must start with /post command")
        
        # Extract post type from command
        command_parts = command_line.split()
        if len(command_parts) < 2:
            raise ContentValidationError("Post type is required")
        
        try:
            post_type = PostType(command_parts[1])
        except ValueError:
            raise ContentValidationError(f"Invalid post type: {command_parts[1]}")
        
        # Parse frontmatter if present
        frontmatter = {}
        content_start_idx = 1
        
        if len(lines) > 1 and lines[1] == '---':
            # Find end of frontmatter
            end_idx = None
            for i, line in enumerate(lines[2:], start=2):
                if line == '---':
                    end_idx = i
                    break
            
            if end_idx is not None:
                try:
                    frontmatter_text = '\n'.join(lines[2:end_idx])
                    frontmatter = yaml.safe_load(frontmatter_text) or {}
                    content_start_idx = end_idx + 1
                except yaml.YAMLError as e:
                    raise ContentValidationError(f"Invalid frontmatter YAML: {e}")
        
        # Extract content
        content_lines = lines[content_start_idx:]
        content = '\n'.join(content_lines).strip()
        
        if not content:
            raise ContentValidationError("Post content is required")
        
        # Extract structured data
        title = frontmatter.get('title', '')
        if not title:
            # Generate title from first line of content
            title = content.split('\n')[0][:100].strip()
        
        tags = frontmatter.get('tags', [])
        if isinstance(tags, str):
            tags = parse_tags(tags)
        
        # Handle field mapping fixes (reply_to_url/bookmark_url -> target_url)
        target_url = frontmatter.get('target_url')
        if not target_url:
            target_url = frontmatter.get('reply_to_url') or frontmatter.get('bookmark_url')
        
        return PostData(
            title=title,
            content=content,
            post_type=post_type,
            tags=tags,
            target_url=target_url,
            media_url=frontmatter.get('media_url'),
            created_by=user_id
        )

    def _generate_site_url(self, filepath: str) -> Optional[str]:
        """
        Generate site URL for published content.
        
        Args:
            filepath: File path in repository
            
        Returns:
            Site URL or None if base URL not configured
        """
        if not self.publishing_settings.site_base_url:
            return None
        
        # Convert repository path to site URL
        # Remove _src/ prefix and change .md to .html
        site_path = filepath.replace('_src/', '').replace('.md', '.html')
        
        base_url = self.publishing_settings.site_base_url.rstrip('/')
        return f"{base_url}/{site_path}"

    async def list_recent_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent posts from all content directories.
        
        Args:
            limit: Maximum number of posts to return
            
        Returns:
            List of post information
        """
        try:
            all_posts = []
            
            for post_type, directory in self.CONTENT_TYPE_DIRECTORIES.items():
                try:
                    files = await self.github_client.list_files(directory)
                    for file_info in files:
                        if file_info["name"].endswith(".md"):
                            all_posts.append({
                                "type": post_type.value,
                                "name": file_info["name"],
                                "path": file_info["path"],
                                "url": file_info["url"],
                                "size": file_info["size"]
                            })
                except Exception as e:
                    logger.warning(f"Failed to list files in {directory}: {e}")
                    continue
            
            # Sort by name (which includes date) and limit
            all_posts.sort(key=lambda x: x["name"], reverse=True)
            return all_posts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list recent posts: {e}")
            return []
