"""
Discord module for Discord Publish Bot.

Provides both WebSocket (development) and HTTP interactions (production) for Discord integration.
"""

from .bot import DiscordBot
from .interactions import DiscordInteractionsHandler

__all__ = [
    "DiscordBot",
    "DiscordInteractionsHandler",
]
