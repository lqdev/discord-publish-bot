"""
Linode Object Storage service for Discord media management.

This service handles uploading Discord attachments to Linode Object Storage
and generating permanent URLs with custom domain support.
"""

import asyncio
import hashlib
import logging
import mimetypes
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlparse

import aiohttp
import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from ..config import get_settings

logger = logging.getLogger(__name__)


class LinodeStorageService:
    """
    Linode Object Storage service for Discord media management.
    
    Provides functionality to:
    - Upload Discord attachments to S3-compatible storage
    - Generate permanent URLs with custom domain support
    - Organize media by type hierarchy
    - Set public-read ACL for immediate CDN access
    """
    
    def __init__(self):
        """Initialize Linode Object Storage service with S3-compatible client."""
        self.settings = get_settings()
        storage_config = self.settings.linode_storage
        
        # Validate required configuration
        if not storage_config.access_key_id:
            raise ValueError("Linode Storage access key ID is required. Set LINODE_STORAGE_ACCESS_KEY_ID environment variable.")
        
        if not storage_config.secret_access_key:
            raise ValueError("Linode Storage secret access key is required. Set LINODE_STORAGE_SECRET_ACCESS_KEY environment variable.")
        
        if not storage_config.bucket_name:
            raise ValueError("Linode Storage bucket name is required. Set LINODE_STORAGE_BUCKET_NAME environment variable.")
        
        # Store configuration
        self.bucket_name = storage_config.bucket_name
        self.endpoint_url = storage_config.endpoint_url
        self.region = storage_config.region
        self.custom_domain = storage_config.custom_domain
        self.use_custom_domain = storage_config.use_custom_domain
        self.base_path = storage_config.base_path
        
        # Initialize S3-compatible client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=storage_config.access_key_id,
            aws_secret_access_key=storage_config.secret_access_key,
            region_name=self.region,
            config=Config(
                signature_version='s3v4',
                s3={
                    'addressing_style': 'virtual'
                }
            )
        )
        
        logger.info(f"Linode Object Storage service initialized for bucket: {self.bucket_name}")
        logger.info(f"Custom domain: {self.custom_domain}, Use custom domain: {self.use_custom_domain}")
    
    async def upload_discord_attachment(
        self,
        discord_url: str,
        filename: str,
        guild_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload Discord attachment to Linode Object Storage with public read access.
        
        Args:
            discord_url: Discord CDN URL to download
            filename: Original filename from Discord
            guild_id: Discord guild ID (optional)
            channel_id: Discord channel ID (optional)
            content_type: MIME type hint (optional)
            
        Returns:
            Permanent URL for the uploaded content
            
        Raises:
            Exception: If upload fails
        """
        try:
            # Download content from Discord
            logger.info(f"Downloading Discord attachment: {discord_url}")
            content, detected_content_type = await self._download_discord_content(discord_url)
            
            if not content_type:
                content_type = detected_content_type
            
            # Generate organized object key based on media type
            object_key = self._generate_object_key(filename, guild_id, channel_id, content_type)
            
            # Upload to Linode Object Storage with public read ACL
            logger.info(f"Uploading to Linode Object Storage: {object_key}")
            await self._upload_object(object_key, content, content_type)
            
            # Generate permanent URL with custom domain
            permanent_url = self._generate_permanent_url(object_key)
            
            logger.info(f"Successfully uploaded {filename} -> {object_key}")
            logger.info(f"Permanent URL: {permanent_url}")
            return permanent_url
            
        except Exception as e:
            logger.error(f"Failed to upload Discord attachment {filename}: {e}")
            raise
    
    async def _download_discord_content(self, discord_url: str) -> Tuple[bytes, Optional[str]]:
        """Download content from Discord CDN using aiohttp."""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(discord_url) as response:
                response.raise_for_status()
                
                # Get content type from response headers
                content_type = response.headers.get('content-type')
                
                # Read content
                content = await response.read()
                
                logger.debug(f"Downloaded {len(content)} bytes, content-type: {content_type}")
                return content, content_type
    
    def _generate_object_key(
        self, 
        filename: str, 
        guild_id: Optional[str] = None, 
        channel_id: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Generate S3 object key for Discord media with media type organization.
        
        Pattern: {base_path}/{media_type_folder}/{timestamp}_{filename}
        
        Examples:
        - files/images/20250910_143052_photo.jpg
        - files/videos/20250910_143052_video.mp4
        - files/audio/20250910_143052_sound.mp3
        """
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Generate timestamp prefix to avoid conflicts
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        timestamped_filename = f"{timestamp}_{safe_filename}"
        
        # Determine media type folder based on content type and filename
        media_folder = self._get_media_type_folder(filename, content_type)
        
        # Return full object key path
        return f"{self.base_path}/{media_folder}/{timestamped_filename}"
    
    def _get_media_type_folder(self, filename: str, content_type: Optional[str] = None) -> str:
        """
        Determine the appropriate folder based on file type.
        
        Returns folder name from configuration based on media type.
        """
        storage_config = self.settings.linode_storage
        
        # Get file extension
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Check content type first, then fall back to file extension
        if content_type:
            content_type = content_type.lower()
            
            # Image types
            if content_type.startswith('image/'):
                return storage_config.images_folder
            
            # Video types
            elif content_type.startswith('video/'):
                return storage_config.videos_folder
            
            # Audio types
            elif content_type.startswith('audio/'):
                return storage_config.audio_folder
            
            # Document types
            elif content_type in ['application/pdf', 'application/msword', 
                                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                'application/vnd.ms-excel',
                                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                'application/vnd.ms-powerpoint',
                                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                                'text/plain', 'text/csv']:
                return storage_config.documents_folder
        
        # Fall back to file extension detection
        # Image extensions
        if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif']:
            return storage_config.images_folder
        
        # Video extensions
        elif file_ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp', 'mpg', 'mpeg']:
            return storage_config.videos_folder
        
        # Audio extensions
        elif file_ext in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus']:
            return storage_config.audio_folder
        
        # Document extensions
        elif file_ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'rtf']:
            return storage_config.documents_folder
        
        # Default to other folder for unknown types
        else:
            return storage_config.other_folder
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for S3 object storage."""
        # Replace problematic characters
        sanitized = filename.replace(' ', '_')
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in '._-')
        
        # Ensure it's not empty and has reasonable length
        if not sanitized:
            sanitized = 'file'
        
        # Truncate if too long (keep extension)
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:100-len(ext)] + ext
        
        return sanitized
    
    async def _upload_object(self, object_key: str, content: bytes, content_type: Optional[str]):
        """Upload content to Linode Object Storage with public read ACL."""
        
        try:
            # Prepare upload parameters
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': object_key,
                'Body': content,
                'ACL': 'public-read'  # Make immediately publicly accessible
            }
            
            # Set content type for proper browser handling
            if content_type:
                upload_params['ContentType'] = content_type
            else:
                # Try to guess content type from filename
                guessed_type, _ = mimetypes.guess_type(object_key)
                if guessed_type:
                    upload_params['ContentType'] = guessed_type
            
            # Upload using boto3 S3 client
            # Run in thread pool since boto3 is synchronous
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.put_object(**upload_params)
            )
            
            logger.info(f"Successfully uploaded {object_key} with public-read ACL")
            
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Linode Object Storage upload failed for {object_key}: {e}")
            raise
    
    def _generate_permanent_url(self, object_key: str) -> str:
        """
        Generate permanent URL using custom domain.
        
        Returns full custom domain URL for immediate access.
        """
        
        if self.use_custom_domain:
            # Return full custom domain URL
            # object_key: "files/images/20250910_143052_photo.jpg"
            # result: "https://cdn.lqdev.tech/files/images/20250910_143052_photo.jpg"
            return f"{self.custom_domain}/{object_key}"
        else:
            # Fallback to direct Linode Object Storage URL
            return f"{self.endpoint_url.replace('https://', f'https://{self.bucket_name}.')}/{object_key}"
    
    async def cleanup_expired_content(self, days_old: int = 365) -> int:
        """
        Clean up old content from storage (optional maintenance function).
        
        Args:
            days_old: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            deleted_count = 0
            
            # List objects in bucket
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        await loop.run_in_executor(
                            None,
                            lambda: self.s3_client.delete_object(
                                Bucket=self.bucket_name,
                                Key=obj['Key']
                            )
                        )
                        deleted_count += 1
                        logger.info(f"Deleted expired object: {obj['Key']}")
            
            logger.info(f"Cleanup completed: {deleted_count} files deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise
    
    async def get_storage_stats(self) -> dict:
        """Get storage usage statistics."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            )
            
            total_files = 0
            total_size = 0
            file_types = {}
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    total_files += 1
                    total_size += obj['Size']
                    
                    # Count by media type folder
                    key_parts = obj['Key'].split('/')
                    if len(key_parts) >= 2:
                        media_type = key_parts[1]  # e.g., 'images', 'videos'
                        file_types[media_type] = file_types.get(media_type, 0) + 1
            
            return {
                "bucket_name": self.bucket_name,
                "endpoint_url": self.endpoint_url,
                "custom_domain": self.custom_domain,
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            raise


# Convenience function for easy import
async def upload_discord_media(
    discord_url: str,
    filename: str,
    guild_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    content_type: Optional[str] = None
) -> str:
    """
    Convenience function to upload Discord media to Linode Object Storage.
    
    Returns permanent URL for the uploaded content.
    """
    
    storage_service = LinodeStorageService()
    return await storage_service.upload_discord_attachment(
        discord_url=discord_url,
        filename=filename,
        guild_id=guild_id,
        channel_id=channel_id,
        content_type=content_type
    )
