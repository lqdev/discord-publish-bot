#!/usr/bin/env python3
"""
Discord Publish Bot - Entry Point Script

Run this script to start the Discord bot with proper Python path configuration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path so absolute imports work
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now we can import and run the bot
if __name__ == "__main__":
    from src.discord_bot.main import main
    
    # Run the async bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)
