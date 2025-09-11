"""
Storage services for Discord Publish Bot.

This module provides storage abstractions for permanent media hosting.
"""

from .azure_storage import AzureStorageService
from .linode_storage import LinodeStorageService
from .factory import get_storage_service, is_storage_enabled, get_storage_provider_name

__all__ = [
    "AzureStorageService",
    "LinodeStorageService",
    "get_storage_service", 
    "is_storage_enabled",
    "get_storage_provider_name"
]
