"""
HTTP Interactions API Client

Handles communication with the publishing API from HTTP interactions.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import aiohttp
from dataclasses import dataclass


@dataclass
class PostData:
    """Data structure for post creation."""
    title: str
    content: str
    post_type: str
    tags: Optional[str] = None
    reply_to_url: Optional[str] = None
    bookmark_url: Optional[str] = None
    media_url: Optional[str] = None


class InteractionsAPIClient:
    """
    API client for HTTP interactions to communicate with publishing API.
    
    This handles the async API calls that need to happen after deferred responses.
    """
    
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
    
    async def create_post(self, post_data: PostData) -> Dict[str, Any]:
        """
        Create a post via the publishing API.
        
        Args:
            post_data: Post data to create
            
        Returns:
            API response data
        """
        # Prepare API payload
        payload = {
            "title": post_data.title,
            "content": post_data.content,
            "type": post_data.post_type,
        }
        
        # Add tags if provided
        if post_data.tags:
            # Split tags and clean them
            tag_list = [tag.strip() for tag in post_data.tags.split(',') if tag.strip()]
            if tag_list:
                payload["tags"] = tag_list
        
        # Add type-specific fields
        if post_data.post_type == "response" and post_data.reply_to_url:
            payload["reply_to_url"] = post_data.reply_to_url
        elif post_data.post_type == "bookmark" and post_data.bookmark_url:
            payload["bookmark_url"] = post_data.bookmark_url
        elif post_data.post_type == "media" and post_data.media_url:
            payload["media_url"] = post_data.media_url
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_endpoint}/posts",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.info(f"Post created successfully: {data.get('url', 'Unknown URL')}")
                        return {
                            "success": True,
                            "url": data.get("url"),
                            "message": data.get("message", "Post created successfully")
                        }
                    else:
                        error_text = await response.text()
                        self.logger.error(f"API error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"API error {response.status}: {error_text}"
                        }
        
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP client error: {e}")
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def send_followup_message(self, application_id: str, interaction_token: str, 
                                  content: str, ephemeral: bool = True) -> bool:
        """
        Send a followup message to a deferred interaction.
        
        Args:
            application_id: Discord application ID
            interaction_token: Token from the original interaction
            content: Message content to send
            ephemeral: Whether message should be ephemeral
            
        Returns:
            True if successful, False otherwise
        """
        url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
        
        payload = {
            "content": content
        }
        
        if ephemeral:
            payload["flags"] = 64  # Ephemeral flag
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status in [200, 204]:
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Discord followup error {response.status}: {error_text}")
                        return False
        
        except Exception as e:
            self.logger.error(f"Error sending followup message: {e}")
            return False
