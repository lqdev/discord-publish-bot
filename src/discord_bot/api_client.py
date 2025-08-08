"""
API client for communicating with the Publishing API.

Handles HTTP requests to the FastAPI publishing service.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

import aiohttp
from aiohttp import ClientSession, ClientTimeout

logger = logging.getLogger(__name__)


class PublishingAPIClient:
    """Client for communicating with the Publishing API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session: Optional[ClientSession] = None

        # Configure timeout
        self.timeout = ClientTimeout(total=30.0)

    async def _get_session(self) -> ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = ClientSession(
                timeout=self.timeout,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                    "User-Agent": "DiscordBot/1.0",
                },
            )
        return self.session

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def publish_post(
        self, message: str, user_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Publish a post via the API.

        Args:
            message: Discord message content with post data
            user_id: Discord user ID

        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        session = await self._get_session()

        payload = {"message": message, "user_id": user_id}

        try:
            async with session.post(
                f"{self.base_url}/publish", json=payload
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    logger.info(
                        f"Successfully published post: {response_data.get('filepath')}"
                    )
                    return True, response_data
                else:
                    error_msg = response_data.get("error", {}).get(
                        "message", "Unknown error"
                    )
                    logger.error(f"API error {response.status}: {error_msg}")
                    return False, {"error": error_msg}

        except asyncio.TimeoutError:
            logger.error("API request timed out")
            return False, {"error": "Request timed out. Please try again."}
        except aiohttp.ClientError as e:
            logger.error(f"API client error: {e}")
            return False, {"error": "Failed to connect to publishing service."}
        except Exception as e:
            logger.error(f"Unexpected error in API call: {e}")
            return False, {"error": "An unexpected error occurred."}

    async def check_health(self) -> bool:
        """
        Check if the API is healthy.

        Returns:
            True if API is healthy, False otherwise
        """
        session = await self._get_session()

        try:
            async with session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def __del__(self):
        """Cleanup on destruction."""
        if self.session and not self.session.closed:
            # Try to close session, but don't fail if event loop is closed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.close())
            except Exception:
                pass
