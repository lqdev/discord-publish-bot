"""
Main entry points for Discord Publish Bot.

Provides command-line interfaces for different deployment modes.
"""

import asyncio
import logging
import sys
from typing import Optional

import click
import uvicorn

from .config import get_settings, reset_settings
from .shared import setup_logging, PostData
from .discord import DiscordBot, DiscordInteractionsHandler
from .api import app, get_publishing_service
from .publishing import GitHubClient, PublishingService

logger = logging.getLogger(__name__)


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
@click.option('--environment', help='Override environment setting')
def cli(log_level: str, environment: Optional[str]):
    """Discord Publish Bot - Multi-mode content publishing system."""
    # Reset settings to pick up any changes
    reset_settings()
    
    # Set up logging
    setup_logging(log_level)
    
    if environment:
        import os
        os.environ['ENVIRONMENT'] = environment


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
def api(host: str, port: int, reload: bool):
    """Start the FastAPI server for HTTP interactions and API access."""
    settings = get_settings()
    
    logger.info(f"Starting {settings.app_name} API server")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Server: http://{host}:{port}")
    
    if settings.is_development and not reload:
        logger.info("Development mode detected - consider using --reload flag")
    
    uvicorn.run(
        "discord_publish_bot.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower()
    )


@cli.command()
async def bot():
    """Start the Discord WebSocket bot (development/testing mode)."""
    settings = get_settings()
    
    if not settings.discord.bot_token:
        logger.error("Discord bot token not configured")
        sys.exit(1)
    
    logger.info(f"Starting Discord WebSocket bot")
    logger.info(f"Environment: {settings.environment}")
    
    # Create post handler that uses publishing service
    async def handle_post(post_data: PostData) -> str:
        try:
            github_client = GitHubClient(
                token=settings.github.token,
                repository=settings.github.repository
            )
            
            publishing_service = PublishingService(
                github_client=github_client,
                github_settings=settings.github,
                publishing_settings=settings.publishing
            )
            
            result = await publishing_service.publish_post(post_data)
            
            if result.success:
                message = f"✅ {post_data.post_type.value.title()} post published successfully!"
                if result.site_url:
                    message += f"\n🔗 {result.site_url}"
                return message
            else:
                return f"❌ {result.message}"
                
        except Exception as e:
            logger.error(f"Error in post handler: {e}")
            return f"❌ Error publishing post: {str(e)}"
    
    # Create and start bot
    discord_bot = DiscordBot(settings.discord, post_handler=handle_post)
    
    try:
        await discord_bot.start_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('title')
@click.argument('content')
@click.option('--type', 'post_type', default='note', help='Post type (note, response, bookmark, media)')
@click.option('--tags', help='Comma-separated tags')
@click.option('--target-url', help='Target URL for responses/bookmarks')
@click.option('--media-url', help='Media URL for media posts')
async def publish(
    title: str, 
    content: str, 
    post_type: str, 
    tags: Optional[str],
    target_url: Optional[str],
    media_url: Optional[str]
):
    """Publish content directly via CLI."""
    from .shared import PostType, parse_tags
    
    try:
        post_type_enum = PostType(post_type)
    except ValueError:
        logger.error(f"Invalid post type: {post_type}")
        sys.exit(1)
    
    settings = get_settings()
    
    # Create services
    github_client = GitHubClient(
        token=settings.github.token,
        repository=settings.github.repository
    )
    
    publishing_service = PublishingService(
        github_client=github_client,
        github_settings=settings.github,
        publishing_settings=settings.publishing
    )
    
    # Create post data
    post_data = PostData(
        title=title,
        content=content,
        post_type=post_type_enum,
        tags=parse_tags(tags) if tags else None,
        target_url=target_url,
        media_url=media_url
    )
    
    try:
        result = await publishing_service.publish_post(post_data)
        
        if result.success:
            click.echo(f"✅ Published: {result.filename}")
            if result.site_url:
                click.echo(f"🔗 Site URL: {result.site_url}")
        else:
            click.echo(f"❌ Failed: {result.message}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        sys.exit(1)


@cli.command()
async def health():
    """Check system health and configuration."""
    settings = get_settings()
    
    click.echo(f"🤖 {settings.app_name} v{settings.version}")
    click.echo(f"📍 Environment: {settings.environment}")
    click.echo()
    
    # Check Discord configuration
    click.echo("Discord Configuration:")
    if settings.discord.bot_token:
        click.echo(f"  ✅ Bot token configured")
    else:
        click.echo(f"  ❌ Bot token missing")
    
    if settings.discord_interactions_enabled:
        click.echo(f"  ✅ HTTP interactions enabled")
    else:
        click.echo(f"  ⚠️  HTTP interactions not configured")
    
    click.echo()
    
    # Check GitHub configuration
    click.echo("GitHub Configuration:")
    if settings.github.token and settings.github.repository:
        click.echo(f"  ✅ GitHub configured for {settings.github.repository}")
        
        # Test connectivity
        try:
            github_client = GitHubClient(
                token=settings.github.token,
                repository=settings.github.repository
            )
            
            if await github_client.check_connectivity():
                click.echo(f"  ✅ GitHub connectivity verified")
            else:
                click.echo(f"  ❌ GitHub connectivity failed")
        except Exception as e:
            click.echo(f"  ❌ GitHub error: {e}")
    else:
        click.echo(f"  ❌ GitHub not configured")


def main():
    """Main CLI entry point."""
    # Make async commands work with click
    def async_wrapper(async_func):
        def wrapper(*args, **kwargs):
            return asyncio.run(async_func(*args, **kwargs))
        return wrapper
    
    # Wrap async commands
    cli.commands['bot'].callback = async_wrapper(cli.commands['bot'].callback)
    cli.commands['publish'].callback = async_wrapper(cli.commands['publish'].callback)
    cli.commands['health'].callback = async_wrapper(cli.commands['health'].callback)
    
    cli()


# Legacy entry points for backwards compatibility
def cli_main():
    """Legacy CLI entry point."""
    main()


def api_main():
    """Legacy API entry point."""
    settings = get_settings()
    uvicorn.run(
        "discord_publish_bot.api:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
