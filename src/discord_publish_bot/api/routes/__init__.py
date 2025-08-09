"""
API routes module for Discord Publish Bot.

Organizes route modules for clean imports.
"""

from . import health, discord, publishing

__all__ = ["health", "discord", "publishing"]
