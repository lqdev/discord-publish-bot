"""
Storage service factory for dynamic provider selection.

Provides centralized logic for selecting storage providers based on configuration.
"""

import logging
from typing import Optional, Protocol

from ..config import get_settings

logger = logging.getLogger(__name__)


class StorageServiceProtocol(Protocol):
    """Protocol defining the interface all storage services must implement."""
    
    async def upload_discord_attachment(
        self,
        discord_url: str,
        filename: str,
        guild_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """Upload Discord attachment and return permanent URL."""
        ...


def get_storage_service() -> StorageServiceProtocol:
    """
    Get the configured storage service based on settings.
    
    Returns the appropriate storage service instance based on:
    1. storage_provider setting (azure or linode)
    2. Provider-specific enabled flag
    
    Raises:
        ValueError: If no storage service is properly configured
        ImportError: If required dependencies are missing
    """
    settings = get_settings()
    
    if settings.storage_provider == "linode" and settings.linode_storage.enabled:
        try:
            from .linode_storage import LinodeStorageService
            logger.info("Using Linode Object Storage service")
            return LinodeStorageService()
        except ImportError as e:
            logger.error(f"Linode storage dependencies not available: {e}")
            raise ImportError(
                "Linode storage requires boto3. Install with: pip install boto3 botocore"
            ) from e
    
    elif settings.storage_provider == "azure" and settings.azure_storage.enabled:
        try:
            from .azure_storage import AzureStorageService
            logger.info("Using Azure Blob Storage service")
            return AzureStorageService()
        except ImportError as e:
            logger.error(f"Azure storage dependencies not available: {e}")
            raise ImportError(
                "Azure storage requires azure-storage-blob. Install with: pip install azure-storage-blob azure-identity"
            ) from e
    
    else:
        provider = settings.storage_provider
        enabled_status = {
            "azure": settings.azure_storage.enabled,
            "linode": settings.linode_storage.enabled
        }
        
        raise ValueError(
            f"No storage service configured. "
            f"Provider: {provider}, "
            f"Enabled status: {enabled_status}. "
            f"Please configure STORAGE_PROVIDER and enable the corresponding service."
        )


def is_storage_enabled() -> bool:
    """
    Check if any storage service is enabled and properly configured.
    
    Returns:
        bool: True if a storage service is available, False otherwise
    """
    try:
        get_storage_service()
        return True
    except (ValueError, ImportError):
        return False


def get_storage_provider_name() -> str:
    """
    Get the name of the currently configured storage provider.
    
    Returns:
        str: Name of the storage provider ("azure", "linode", or "none")
    """
    settings = get_settings()
    
    if is_storage_enabled():
        return settings.storage_provider
    else:
        return "none"
