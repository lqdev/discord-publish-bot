"""
Azure Blob Storage service for Discord media management.

This service handles uploading Discord attachments to Azure Blob Storage
and generating permanent URLs for long-term access.
"""

import asyncio
import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient

from ..config import get_settings

logger = logging.getLogger(__name__)


class AzureStorageService:
    """
    Azure Blob Storage service for Discord media management.
    
    Provides functionality to:
    - Upload Discord attachments to permanent storage
    - Generate long-lived public URLs 
    - Organize media by Discord server/channel hierarchy
    """
    
    def __init__(self):
        """Initialize Azure Storage service with managed identity authentication."""
        self.settings = get_settings()
        
        # Use Managed Identity for authentication (secure for Azure Container Apps)
        self.credential = DefaultAzureCredential()
        
        # Get storage account configuration from settings
        storage_config = self.settings.azure_storage
        self.account_name = storage_config.account_name
        self.container_name = storage_config.container_name
        self.cdn_endpoint = storage_config.cdn_endpoint
        self.sas_expiry_hours = storage_config.sas_expiry_hours
        
        if not self.account_name:
            raise ValueError("Azure Storage account name is required. Set AZURE_STORAGE_ACCOUNT_NAME environment variable.")
        
        # Initialize blob service client
        self.account_url = f"https://{self.account_name}.blob.core.windows.net"
        self.blob_service_client = BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        )
        
        # Async client for upload operations
        self.async_blob_service_client = AsyncBlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        )
        
        logger.info(f"Azure Storage service initialized for account: {self.account_name}")
    
    async def upload_discord_attachment(
        self,
        discord_url: str,
        filename: str,
        guild_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload Discord attachment to Azure Blob Storage and return permanent URL.
        
        Args:
            discord_url: The ephemeral Discord CDN URL
            filename: Original filename from Discord
            guild_id: Discord guild/server ID for organization
            channel_id: Discord channel ID for organization  
            content_type: MIME type of the content
            
        Returns:
            Permanent Azure Blob Storage URL with SAS token
            
        Raises:
            AzureError: If upload fails
            aiohttp.ClientError: If downloading from Discord fails
        """
        
        try:
            # Download content from Discord URL
            logger.info(f"Downloading attachment from Discord: {filename}")
            content, detected_content_type = await self._download_discord_content(discord_url)
            
            # Use detected content type if not provided
            if not content_type:
                content_type = detected_content_type
            
            # Generate organized blob path based on media type
            blob_path = self._generate_blob_path(filename, guild_id, channel_id, content_type)
            
            # Upload to Azure Blob Storage
            logger.info(f"Uploading to Azure Storage: {blob_path}")
            await self._upload_blob(blob_path, content, content_type)
            
            # Generate permanent URL with SAS token
            permanent_url = self._generate_permanent_url(blob_path)
            
            logger.info(f"Successfully uploaded {filename} -> {blob_path}")
            return permanent_url
            
        except Exception as e:
            logger.error(f"Failed to upload Discord attachment {filename}: {e}")
            raise
    
    async def _download_discord_content(self, discord_url: str) -> Tuple[bytes, Optional[str]]:
        """Download content from Discord CDN using requests with asyncio."""
        
        # Use synchronous requests in thread pool to avoid aiohttp connection issues
        import requests
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def sync_download():
            """Synchronous download function to run in thread pool."""
            response = requests.get(discord_url, timeout=30)
            response.raise_for_status()
            
            content = response.content
            content_type = response.headers.get('Content-Type')
            
            logger.debug(f"Downloaded {len(content)} bytes, content-type: {content_type}")
            return content, content_type
        
        # Run synchronous download in thread pool to maintain async interface
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            content, content_type = await loop.run_in_executor(executor, sync_download)
            return content, content_type
    
    def _generate_blob_path(
        self, 
        filename: str, 
        guild_id: Optional[str] = None, 
        channel_id: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Generate media-type organized blob path for Discord media.
        
        Pattern: {media_type_folder}/{timestamp}_{filename}
        
        Examples:
        - images/20250812_143052_photo.jpg
        - videos/20250812_143052_video.mp4
        - audio/20250812_143052_sound.mp3
        """
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Generate timestamp prefix to avoid conflicts
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        timestamped_filename = f"{timestamp}_{safe_filename}"
        
        # Determine media type folder based on content type and filename
        media_folder = self._get_media_type_folder(filename, content_type)
        
        return f"{media_folder}/{timestamped_filename}"
    
    def _get_media_type_folder(self, filename: str, content_type: Optional[str] = None) -> str:
        """
        Determine the appropriate folder based on file type.
        
        Returns folder name from configuration based on media type.
        """
        storage_config = self.settings.azure_storage
        
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
        """Sanitize filename for blob storage."""
        
        # Remove or replace problematic characters
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in ".-_":
                safe_chars.append(char)
            else:
                safe_chars.append("_")
        
        safe_filename = "".join(safe_chars)
        
        # Ensure reasonable length (Azure limit is 1024, but keep practical)
        if len(safe_filename) > 100:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:100-len(ext)] + ext
            
        return safe_filename
    
    async def _upload_blob(self, blob_path: str, content: bytes, content_type: Optional[str]):
        """Upload content to Azure Blob Storage."""
        
        try:
            blob_client = self.async_blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            # Set content type for proper browser handling
            content_settings = None
            if content_type:
                from azure.storage.blob import ContentSettings
                content_settings = ContentSettings(content_type=content_type)
            
            await blob_client.upload_blob(
                content,
                content_settings=content_settings,
                overwrite=True
            )
            
        except AzureError as e:
            logger.error(f"Azure upload failed for {blob_path}: {e}")
            raise
    
    def _generate_permanent_url(self, blob_path: str) -> str:
        """
        Generate permanent URL for blob.
        
        Returns either:
        - Relative path (/{container}/{path}) for domain-mapped containers
        - Direct URL (for public containers without SAS tokens)
        - SAS-signed URL (for private containers with SAS tokens)
        """
        
        try:
            # Check if we should use relative paths (domain-mapped containers)
            if self.settings.azure_storage.use_relative_paths:
                # Return relative path for domain-mapped container
                relative_path = f"/{self.container_name}/{blob_path}"
                logger.info(f"Returning relative path for domain-mapped container: {relative_path}")
                return relative_path
            
            # Generate full URLs for CDN or direct blob access
            # Base URL construction
            if self.settings.azure_storage.cdn_endpoint:
                base_url = f"{self.settings.azure_storage.cdn_endpoint.rstrip('/')}/{self.container_name}"
            else:
                base_url = f"{self.account_url}/{self.container_name}"
            
            blob_url = f"{base_url}/{blob_path}"
            
            # Return direct URL if SAS tokens are disabled (requires public container)
            if not self.settings.azure_storage.use_sas_tokens:
                logger.info(f"Returning direct URL (no SAS token): {blob_path}")
                return blob_url
            
            # Generate SAS token for secure access (recommended for private containers)
            logger.debug(f"Generating SAS token for blob: {blob_path}")
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=blob_path,
                account_key=None,  # Use credential instead
                user_delegation_key=None,  # Could enhance with user delegation for better security
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=self.settings.azure_storage.sas_expiry_hours)
            )
            
            return f"{blob_url}?{sas_token}"
            
        except Exception as e:
            logger.error(f"Failed to generate URL for {blob_path}: {e}")
            # Fallback based on configuration
            if self.settings.azure_storage.use_relative_paths:
                return f"/{self.container_name}/{blob_path}"
            else:
                return f"{self.account_url}/{self.container_name}/{blob_path}"
    
    async def cleanup_expired_content(self, days_old: int = 365) -> int:
        """
        Clean up old media content based on age.
        
        Args:
            days_old: Remove content older than this many days
            
        Returns:
            Number of blobs deleted
        """
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        deleted_count = 0
        
        try:
            container_client = self.async_blob_service_client.get_container_client(self.container_name)
            
            async for blob in container_client.list_blobs():
                if blob.last_modified and blob.last_modified.replace(tzinfo=None) < cutoff_date:
                    blob_client = container_client.get_blob_client(blob.name)
                    await blob_client.delete_blob()
                    deleted_count += 1
                    logger.info(f"Deleted expired blob: {blob.name}")
            
            logger.info(f"Cleanup completed: {deleted_count} blobs deleted")
            return deleted_count
            
        except AzureError as e:
            logger.error(f"Cleanup operation failed: {e}")
            raise
    
    async def get_storage_stats(self) -> dict:
        """Get storage usage statistics."""
        
        try:
            container_client = self.async_blob_service_client.get_container_client(self.container_name)
            
            blob_count = 0
            total_size = 0
            
            async for blob in container_client.list_blobs():
                blob_count += 1
                if blob.size:
                    total_size += blob.size
            
            return {
                "blob_count": blob_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "container_name": self.container_name,
                "account_name": self.account_name
            }
            
        except AzureError as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}


# Convenience function for easy import
async def upload_discord_media(
    discord_url: str,
    filename: str,
    guild_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    content_type: Optional[str] = None
) -> str:
    """
    Convenience function to upload Discord media to Azure Storage.
    
    Returns permanent URL for the uploaded content.
    """
    
    storage_service = AzureStorageService()
    return await storage_service.upload_discord_attachment(
        discord_url=discord_url,
        filename=filename,
        guild_id=guild_id,
        channel_id=channel_id,
        content_type=content_type
    )
