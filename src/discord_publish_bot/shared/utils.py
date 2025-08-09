"""
Shared utilities for Discord Publish Bot.

Common utility functions used across multiple modules.
"""

import hashlib
import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from .types import PostType


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up structured logging for the application.
    
    Args:
        level: Logging level
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )
    
    return logging.getLogger("discord_publish_bot")


def slugify(text: str, max_length: int = 100) -> str:
    """
    Convert text to URL-safe slug.
    
    Args:
        text: Input text to slugify
        max_length: Maximum length of resulting slug
        
    Returns:
        URL-safe slug
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Convert to lowercase and replace spaces/special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    
    # Truncate to max length and remove trailing hyphens
    text = text[:max_length].rstrip('-')
    
    return text


def generate_filename(
    post_type: PostType, 
    title: str, 
    timestamp: Optional[datetime] = None
) -> str:
    """
    Generate filename for post based on type and title.
    
    Args:
        post_type: Type of post
        title: Post title
        timestamp: Optional timestamp (defaults to now)
        
    Returns:
        Generated filename with .md extension
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    # Format: YYYY-MM-DD-title-slug.md
    date_prefix = timestamp.strftime("%Y-%m-%d")
    title_slug = slugify(title, max_length=80)
    
    return f"{date_prefix}-{title_slug}.md"


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain or None if invalid URL
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None


def sanitize_content(content: str) -> str:
    """
    Sanitize content for safe publication.
    
    Args:
        content: Raw content
        
    Returns:
        Sanitized content
    """
    # Remove potential script injections and clean up whitespace
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
    content = content.strip()
    
    return content


def parse_tags(tags_input: Optional[str]) -> List[str]:
    """
    Parse comma-separated tags input.
    
    Args:
        tags_input: Comma-separated tags string
        
    Returns:
        List of cleaned tag strings
    """
    if not tags_input:
        return []
    
    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag)
    
    return unique_tags


def format_frontmatter(data: Dict[str, Any]) -> str:
    """
    Format dictionary as YAML frontmatter.
    
    Args:
        data: Dictionary to format
        
    Returns:
        YAML frontmatter string
    """
    import yaml
    
    # Custom representer for cleaner YAML output
    def str_presenter(dumper, data):
        if '\n' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    
    yaml.add_representer(str, str_presenter)
    
    return yaml.dump(data, default_flow_style=False, allow_unicode=True).strip()


def calculate_content_hash(content: str) -> str:
    """
    Calculate SHA-256 hash of content for deduplication.
    
    Args:
        content: Content to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """
    Format datetime for consistent display.
    
    Args:
        dt: Datetime to format
        format_str: Format string
        
    Returns:
        Formatted datetime string
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime(format_str)


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging.
    
    Args:
        data: Sensitive data to mask
        visible_chars: Number of characters to keep visible
        
    Returns:
        Masked data string
    """
    if len(data) <= visible_chars:
        return "*" * len(data)
    
    return data[:visible_chars] + "*" * (len(data) - visible_chars)
