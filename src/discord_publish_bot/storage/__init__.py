"""
Storage services for Discord Publish Bot.

This module provides storage abstractions for permanent media hosting.
"""

from .azure_storage import AzureStorageService

__all__ = ["AzureStorageService"]
