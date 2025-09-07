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
        PostType.NOTE: "_src/notes",
        PostType.RESPONSE: "_src/responses", 
        PostType.BOOKMARK: "_src/bookmarks",
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
        Process post data and publish to GitHub using PR workflow.

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
            
            # Upload media to Azure Storage if needed (replaces ephemeral Discord URLs)
            post_data = await self._process_media_uploads(post_data)
            
            # Generate frontmatter
            frontmatter = self._generate_frontmatter(post_data)
            
            # Build markdown content
            content = self._build_markdown_content(frontmatter, post_data.content, post_data)
            
            # Generate filename and path
            filename = generate_filename(post_data.post_type, post_data.title, post_data.slug)
            directory = self.CONTENT_TYPE_DIRECTORIES[post_data.post_type]
            filepath = f"{directory}/{filename}"
            
            # Create branch for PR workflow
            now = datetime.now(timezone.utc)
            branch_name = f"content/discord-bot/{now.strftime('%Y-%m-%d')}/{post_data.post_type.value}/{filename.replace('.md', '')}"
            
            try:
                # Create feature branch
                await self.github_client.create_branch(branch_name, self.github_settings.branch)
                logger.info(f"Created branch: {branch_name}")
                
                # Create file on branch
                commit_info = await self.github_client.create_file(
                    path=filepath,
                    content=content,
                    message=f"Add {post_data.post_type.value} post: {post_data.title}",
                    branch=branch_name
                )
                
                # Create pull request
                pr_title = f"Add {post_data.post_type.value} post: {post_data.title}"
                pr_body = f"""## New {post_data.post_type.value.title()} Post

**Title:** {post_data.title}
**Type:** {post_data.post_type.value}
**File:** `{filepath}`

### Content Preview
{post_data.content[:200]}{'...' if len(post_data.content) > 200 else ''}

### Frontmatter Validation
- ✅ Title: {post_data.title}
- ✅ Type: {post_data.post_type.value}
- ✅ Tags: {', '.join(post_data.tags) if post_data.tags else 'None'}

**Created via Discord Publishing Bot**"""

                pr = await self.github_client.create_pull_request(
                    title=pr_title,
                    body=pr_body,
                    head_branch=branch_name,
                    base_branch=self.github_settings.branch
                )
                
                # Generate site URL
                site_url = self._generate_site_url(filepath)
                
                result = PublishResult(
                    success=True,
                    message=f"{post_data.post_type.value.title()} post created successfully! PR #{pr.number}",
                    filename=filename,
                    filepath=filepath,
                    commit_sha=commit_info["sha"],
                    branch_name=branch_name,
                    file_url=commit_info["url"],
                    site_url=site_url,
                    pull_request_url=pr.html_url
                )
                
                logger.info(f"Successfully created post PR #{pr.number}: {filename}")
                return result
                
            except Exception as pr_error:
                # If PR workflow fails, clean up the branch
                try:
                    await self.github_client.delete_branch(branch_name)
                    logger.info(f"Cleaned up branch {branch_name} after PR failure")
                except:
                    pass  # Don't fail if cleanup fails
                raise pr_error
            
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

    async def _process_media_uploads(self, post_data: PostData) -> PostData:
        """
        Process media uploads to Azure Storage, replacing ephemeral Discord URLs with permanent ones.
        
        This method:
        1. Detects Discord URLs in media_url and content
        2. Uploads them to Azure Storage 
        3. Replaces URLs with permanent Azure URLs
        4. Returns updated PostData with permanent URLs
        
        Args:
            post_data: Original post data potentially containing Discord URLs
            
        Returns:
            Updated post data with permanent URLs
        """
        try:
            from ..storage import AzureStorageService
            from ..config import get_settings
            
            settings = get_settings()
            
            # Skip processing if Azure Storage is not enabled
            if not settings.azure_storage.enabled:
                logger.info("Azure Storage not enabled, keeping original URLs")
                return post_data
            
            # Create a copy of post_data to modify
            updated_data = post_data.model_copy()
            storage_service = AzureStorageService()
            
            # Process media_url if it's a Discord URL
            if updated_data.media_url and self._is_discord_url(updated_data.media_url):
                logger.info(f"Uploading Discord media to Azure Storage: {updated_data.media_url}")
                
                try:
                    # Extract filename from Discord URL
                    filename = self._extract_filename_from_discord_url(updated_data.media_url)
                    
                    # Upload to Azure Storage
                    permanent_url = await storage_service.upload_discord_attachment(
                        discord_url=updated_data.media_url,
                        filename=filename,
                        guild_id=None,  # Could extract from URL if needed
                        channel_id=None,  # Could extract from URL if needed
                        content_type=None  # Will be detected during download
                    )
                    
                    updated_data.media_url = permanent_url
                    logger.info(f"Successfully replaced Discord URL with Azure URL: {permanent_url}")
                    
                except Exception as e:
                    logger.error(f"Failed to upload media to Azure Storage: {e}")
                    logger.warning("Keeping original Discord URL as fallback")
            
            # TODO: Process Discord URLs in content text as well (future enhancement)
            # This would require parsing markdown/text content for Discord CDN URLs
            
            return updated_data
            
        except Exception as e:
            logger.error(f"Error processing media uploads: {e}")
            logger.warning("Keeping original URLs due to processing error")
            return post_data

    def _is_discord_url(self, url: str) -> bool:
        """Check if URL is a Discord CDN URL."""
        return "cdn.discordapp.com" in url or "media.discordapp.net" in url

    def _extract_filename_from_discord_url(self, url: str) -> str:
        """Extract filename from Discord CDN URL."""
        from urllib.parse import urlparse, unquote
        
        parsed = urlparse(url)
        # Discord URLs typically end with the filename after the last slash
        path_parts = parsed.path.split('/')
        if path_parts:
            filename = unquote(path_parts[-1])
            # Remove Discord's attachment ID prefix if present (format: {id}_{filename})
            if '_' in filename and filename.split('_')[0].isdigit():
                filename = '_'.join(filename.split('_')[1:])
            return filename
        return "discord_attachment.bin"  # Fallback filename

    def _generate_frontmatter(self, post_data: PostData) -> Dict[str, Any]:
        """
        Generate frontmatter for post type using site's established schema format.
        
        Based on analysis of existing content:
        - Notes: post_type, title, published_date, tags array
        - Responses/Bookmarks: title, targeturl, response_type, dt_published, dt_updated, tags array  
        - Media: post_type, title, published_date, tags array
        - All dates use -05:00 timezone consistently
        - Tags are always arrays of strings ["tag1", "tag2"]
        
        Args:
            post_data: Post data
            
        Returns:
            Frontmatter dictionary
            
        Raises:
            FrontmatterError: If frontmatter generation fails
        """
        try:
            # Use Eastern timezone consistently regardless of server timezone
            # This ensures dates are always in Eastern time as expected by the site
            from datetime import timedelta
            eastern_tz = timezone(timedelta(hours=-5))
            now_eastern = datetime.now(eastern_tz)
            
            # Base frontmatter
            frontmatter = {
                "title": post_data.title,
            }
            
            # Generate date in Eastern timezone format
            base_date = now_eastern.strftime("%Y-%m-%d %H:%M")
            date_with_tz = f"{base_date} -05:00"
            
            # Type-specific fields using established site schema
            if post_data.post_type == PostType.NOTE:
                frontmatter.update({
                    "post_type": "note",
                    "published_date": date_with_tz,
                })
            
            elif post_data.post_type in (PostType.RESPONSE, PostType.BOOKMARK):
                # Use user-selected response type for responses, default to bookmark for bookmark posts
                if post_data.post_type == PostType.RESPONSE and post_data.response_type:
                    response_type = post_data.response_type.value
                else:
                    response_type = "bookmark" if post_data.post_type == PostType.BOOKMARK else "reply"
                
                frontmatter.update({
                    "targeturl": post_data.target_url,
                    "response_type": response_type,
                    "dt_published": date_with_tz,
                    "dt_updated": date_with_tz,
                })
            
            elif post_data.post_type == PostType.MEDIA:
                frontmatter.update({
                    "post_type": "media",
                    "published_date": date_with_tz,
                })
                # Note: media_url is handled in :::media block, not frontmatter
            
            # Add tags as inline array (site convention)
            if post_data.tags:
                # Use original tags only, no auto-additions
                tags = [str(tag) for tag in post_data.tags]
                frontmatter["tags"] = tags
            else:
                # No default tags - use empty array
                frontmatter["tags"] = []
            
            return frontmatter
            
        except Exception as e:
            logger.error(f"Failed to generate frontmatter: {e}")
            raise FrontmatterError(f"Failed to generate frontmatter: {e}", frontmatter={})

    def _format_frontmatter_inline(self, data: Dict[str, Any]) -> str:
        """
        Format frontmatter with inline array format for tags.
        
        Args:
            data: Frontmatter dictionary
            
        Returns:
            Formatted frontmatter string with inline arrays
        """
        lines = []
        for key, value in data.items():
            if isinstance(value, list):
                # Format as inline array: tags: ["tag1", "tag2"]
                if value:
                    formatted_items = [f'"{item}"' for item in value]
                    lines.append(f'{key}: [{", ".join(formatted_items)}]')
                else:
                    lines.append(f'{key}: []')
            elif isinstance(value, str):
                # Quote strings that might need it
                if any(char in value for char in ['"', "'", ':', '#', '\n']):
                    lines.append(f'{key}: "{value}"')
                else:
                    lines.append(f'{key}: {value}')
            else:
                lines.append(f'{key}: {value}')
        
        return '\n'.join(lines)

    def _build_markdown_content(self, frontmatter: Dict[str, Any], content: str, post_data: PostData) -> str:
        """
        Build complete markdown file content with media block support.
        
        Args:
            frontmatter: Post frontmatter
            content: Post content
            post_data: Complete post data for media block generation
            
        Returns:
            Complete markdown content
        """
        # Sanitize content
        clean_content = sanitize_content(content)
        
        # For media posts, append :::media block if media URL exists
        if post_data.post_type == PostType.MEDIA and post_data.media_url:
            media_block = self._generate_media_block(post_data)
            clean_content = f"{clean_content}\n\n{media_block}"
        
        # Format frontmatter as YAML
        yaml_frontmatter = self._format_frontmatter_inline(frontmatter)
        
        # Combine into markdown
        markdown_content = f"---\n{yaml_frontmatter}\n---\n\n{clean_content}\n"
        
        return markdown_content

    def _generate_media_block(self, post_data: PostData) -> str:
        """
        Generate :::media block for media posts.
        
        Args:
            post_data: Post data containing media information
            
        Returns:
            Formatted :::media block
        """
        lines = [":::media"]
        lines.append(f"- url: \"{post_data.media_url}\"")
        
        # Add alt text if provided
        if post_data.media_alt:
            lines.append(f"  alt: \"{post_data.media_alt}\"")
        
        # Detect media type from URL extension or default to image
        media_type = "image"
        if post_data.media_url:
            url_lower = post_data.media_url.lower()
            if any(ext in url_lower for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv']):
                media_type = "video"
            elif any(ext in url_lower for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
                media_type = "audio"
        
        lines.append(f"  mediaType: \"{media_type}\"")
        lines.append(f"  aspectRatio: \"landscape\"")  # Default aspect ratio
        
        # Use title as caption
        if post_data.title:
            lines.append(f"  caption: \"{post_data.title}\"")
        
        lines.append(":::media")
        return "\n".join(lines)

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
