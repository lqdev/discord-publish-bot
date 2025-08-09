#!/usr/bin/env python3
"""
Test API connectivity using aiohttp.
"""

import asyncio
import aiohttp

async def test_api():
    """Test API health endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                print(f"Status: {response.status}")
                data = await response.json()
                print(f"Response: {data}")
                return response.status == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_api())
    print(f"API accessible: {result}")
