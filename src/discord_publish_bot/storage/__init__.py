"""
Storage services for Discord Publish Bot.

This module provides storage abstractions for permanent media hosting.
"""

from .azure_storage import AzureStorageService
from .factory import get_storage_service, is_storage_enabled, get_storage_provider_name

# Linode storage will be added in Phase 2
# from .linode_storage import LinodeStorageService

__all__ = [
    "AzureStorageService",
    "get_storage_service", 
    "is_storage_enabled",
    "get_storage_provider_name"
]
