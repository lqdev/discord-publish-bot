#!/usr/bin/env python3
"""
GitHub Issue Forms Media Upload Processor
Converts GitHub-hosted attachments to permanent Linode S3 storage
and transforms markdown to custom :::media blocks

Adapted from discord-publish-bot for luisquintanilla.me
"""

import boto3
import os
import re
import requests
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
from urllib.parse import urlparse

class MediaAttachment:
    """Represents a media file extracted from issue markdown"""
    def __init__(self, alt_text: str, github_url: str, filename: str):
        self.alt_text = alt_text
        self.github_url = github_url
        self.filename = filename
        self.permanent_url: Optional[str] = None
        self.media_type: Optional[str] = None

class LinodeMediaUploader:
    """Simplified version of LinodeStorageService from discord-publish-bot"""

    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=os.environ['LINODE_ENDPOINT'],
            aws_access_key_id=os.environ['LINODE_ACCESS_KEY'],
            aws_secret_access_key=os.environ['LINODE_SECRET_KEY'],
            config=boto3.session.Config(signature_version='s3v4')
        )
        self.bucket = os.environ['LINODE_BUCKET']
        self.custom_domain = os.environ.get('CUSTOM_DOMAIN', '').rstrip('/')
        self.base_path = os.environ.get('BASE_PATH', 'files')

    def _sanitize_filename(self, filename: str) -> str:
        """
        From discord-publish-bot/storage/linode_storage.py:234-249
        Sanitize filename for S3 storage
        """
        # Replace spaces with underscores
        sanitized = filename.replace(' ', '_')

        # Keep only alphanumeric, dots, underscores, hyphens
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in '._-')

        # Fallback if empty
        if not sanitized:
            sanitized = 'file'

        # Limit length to 100 chars, preserving extension
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:100-len(ext)] + ext

        return sanitized

    def _get_media_type_folder(self, filename: str, content_type: Optional[str] = None) -> str:
        """
        From discord-publish-bot/storage/linode_storage.py:176-232
        Categorize media into folders based on type
        """
        filename_lower = filename.lower()

        # Check content type first (if provided)
        if content_type:
            if content_type.startswith('image/'):
                return 'images'
            elif content_type.startswith('video/'):
                return 'videos'
            elif content_type.startswith('audio/'):
                return 'audio'
            elif content_type.startswith('application/pdf'):
                return 'documents'

        # Fallback to file extension
        ext = Path(filename_lower).suffix

        # Image extensions
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif'}
        if ext in image_exts:
            return 'images'

        # Video extensions
        video_exts = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.mpg', '.mpeg'}
        if ext in video_exts:
            return 'videos'

        # Audio extensions
        audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'}
        if ext in audio_exts:
            return 'audio'

        # Document extensions
        doc_exts = {'.pdf', '.doc', '.docx', '.txt', '.csv', '.rtf'}
        if ext in doc_exts:
            return 'documents'

        # Default
        return 'other'

    def _detect_media_type(self, filename: str, content_type: Optional[str] = None) -> str:
        """
        From discord-publish-bot/publishing/service.py:551-560
        Detect media type for :::media block
        """
        filename_lower = filename.lower()

        # Check content type
        if content_type:
            if content_type.startswith('video/'):
                return 'video'
            elif content_type.startswith('audio/'):
                return 'audio'
            elif content_type.startswith('image/'):
                return 'image'

        # Check extension
        if any(ext in filename_lower for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv', '.m4v']):
            return 'video'
        elif any(ext in filename_lower for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac']):
            return 'audio'
        else:
            return 'image'  # Default

    def upload_from_github(self, github_url: str, original_filename: str) -> Tuple[str, str]:
        """
        Download from GitHub attachments and upload to Linode S3
        Returns: (permanent_url, media_type)
        """
        print(f"📥 Downloading: {original_filename}")

        # Download from GitHub
        response = requests.get(github_url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type')
        print(f"   Content-Type: {content_type}")

        # Sanitize filename
        sanitized_filename = self._sanitize_filename(original_filename)
        print(f"   Sanitized: {sanitized_filename}")

        # Determine folder and media type
        media_folder = self._get_media_type_folder(sanitized_filename, content_type)
        media_type = self._detect_media_type(sanitized_filename, content_type)
        print(f"   Category: {media_folder} ({media_type})")

        # Generate S3 key with date-based path
        timestamp = datetime.now().strftime('%Y/%m/%d')
        s3_key = f"{self.base_path}/{media_folder}/{timestamp}/{sanitized_filename}"

        # Upload to S3 with public-read ACL
        print(f"📤 Uploading to S3: {s3_key}")
        self.client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=response.content,
            ContentType=content_type or 'application/octet-stream',
            ACL='public-read'
        )

        # Generate permanent CDN URL
        if self.custom_domain:
            permanent_url = f"{self.custom_domain}/{s3_key}"
        else:
            permanent_url = f"{os.environ['LINODE_ENDPOINT']}/{self.bucket}/{s3_key}"

        print(f"✅ Uploaded: {permanent_url}\n")
        return permanent_url, media_type


def parse_markdown_for_attachments(markdown: str) -> List[MediaAttachment]:
    """
    Extract all markdown images from issue body
    Pattern: ![alt text](https://github.com/user-attachments/...)
    """
    attachments = []

    # Regex to match markdown images/links
    # Matches: ![alt](url) or [alt](url) for videos/audio
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)|^\[([^\]]+)\]\(([^)]+)\)'

    for match in re.finditer(pattern, markdown, re.MULTILINE):
        if match.group(1) is not None:  # Image syntax ![alt](url)
            alt_text = match.group(1)
            url = match.group(2)
        else:  # Link syntax [text](url)
            alt_text = match.group(3)
            url = match.group(4)

        # Only process GitHub-hosted attachments
        if 'github.com' in url and ('user-attachments' in url or 'assets' in url):
            # Extract filename from URL
            filename = Path(urlparse(url).path).name
            if not filename:
                filename = 'attachment'

            attachment = MediaAttachment(
                alt_text=alt_text or filename,
                github_url=url,
                filename=filename
            )
            attachments.append(attachment)
            print(f"Found attachment: {filename} ({url})")

    return attachments


def transform_markdown_to_media_blocks(content: str, attachments: List[MediaAttachment]) -> str:
    """
    Replace markdown ![alt](url) with :::media blocks
    From discord-publish-bot/publishing/service.py:_generate_media_block()
    """
    transformed = content

    for attachment in attachments:
        if not attachment.permanent_url:
            continue

        # Find original markdown pattern
        # Match both ![alt](github-url) and [text](github-url)
        patterns = [
            f'![{re.escape(attachment.alt_text)}]({re.escape(attachment.github_url)})',
            f'[{re.escape(attachment.alt_text)}]({re.escape(attachment.github_url)})'
        ]

        # Create :::media block
        media_block = f''':::media
- url: "{attachment.permanent_url}"
  alt: "{attachment.alt_text}"
  mediaType: "{attachment.media_type}"
  aspectRatio: "landscape"
  caption: "{attachment.alt_text}"
:::media'''

        # Replace first matching pattern
        for pattern in patterns:
            if pattern in transformed:
                transformed = transformed.replace(pattern, media_block, 1)
                break

    return transformed


def generate_markdown_file(issue_data: dict, transformed_content: str) -> str:
    """
    Generate final markdown file with frontmatter
    From discord-publish-bot/publishing/service.py
    """
    title = issue_data.get('title', '').replace('[Media] ', '').strip()
    tags_str = issue_data.get('tags', '')
    tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []

    date = datetime.now()
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]

    # Generate filename
    filename = f"_src/media/{date.year:04d}-{date.month:02d}-{date.day:02d}-{slug}.md"

    # Build frontmatter (YAML)
    frontmatter = f"""---
title: "{title}"
date: {date.isoformat()}
tags: {json.dumps(tags) if tags else '[]'}
---

{transformed_content}
"""

    # Ensure directory exists
    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    # Write file
    Path(filename).write_text(frontmatter, encoding='utf-8')
    print(f"📝 Generated: {filename}")

    return filename


def main():
    parser = argparse.ArgumentParser(description='Process GitHub issue media attachments')
    parser.add_argument('--issue-json', required=True, help='Path to issue data JSON file')
    args = parser.parse_args()

    # Load issue data
    with open(args.issue_json, 'r') as f:
        issue_data = json.load(f)

    print("=" * 60)
    print("GITHUB ISSUE MEDIA PROCESSOR")
    print("=" * 60)
    print(f"Issue: {issue_data.get('title')}")
    print(f"Number: #{issue_data.get('number')}")
    print()

    # Get issue body (content)
    content = issue_data.get('body', '')

    # Parse markdown for attachments
    print("🔍 Scanning for media attachments...")
    attachments = parse_markdown_for_attachments(content)

    if not attachments:
        print("⚠️  No GitHub-hosted attachments found")
        print("   Users can drag-and-drop files into issue textarea")
        return

    print(f"📎 Found {len(attachments)} attachment(s)\n")

    # Upload to S3
    uploader = LinodeMediaUploader()

    for attachment in attachments:
        try:
            permanent_url, media_type = uploader.upload_from_github(
                attachment.github_url,
                attachment.filename
            )
            attachment.permanent_url = permanent_url
            attachment.media_type = media_type
        except Exception as e:
            print(f"❌ Failed to upload {attachment.filename}: {e}")
            # Keep original GitHub URL as fallback
            attachment.permanent_url = attachment.github_url
            attachment.media_type = 'image'

    # Transform markdown
    print("🔄 Transforming markdown to :::media blocks...")
    transformed_content = transform_markdown_to_media_blocks(content, attachments)

    # Generate markdown file
    print()
    markdown_file = generate_markdown_file(issue_data, transformed_content)

    # Output for GitHub Actions
    print()
    print("=" * 60)
    print("✅ Processing complete!")
    print(f"   File: {markdown_file}")
    print(f"   Attachments: {len(attachments)}")
    print("=" * 60)

    # Write outputs for GitHub Actions
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"markdown_file={markdown_file}\n")
            f.write(f"attachment_count={len(attachments)}\n")


if __name__ == '__main__':
    main()
