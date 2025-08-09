"""
End-to-end tests for Discord Publish Bot.

Tests complete workflows from Discord interaction to published content.
"""

import pytest
import asyncio
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock

from discord_publish_bot.config import AppSettings
from discord_publish_bot.discord.interactions import DiscordInteractionsHandler
from discord_publish_bot.publishing.service import PublishingService
from discord_publish_bot.publishing.github_client import GitHubClient


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflow:
    """Test complete workflows from start to finish."""
    
    @pytest.fixture
    async def real_git_repo(self):
        """Create a real temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            
            # Create initial structure
            (repo_path / "posts").mkdir()
            (repo_path / "README.md").write_text("# Test Blog Repository")
            
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)
            
            yield repo_path
    
    @pytest.fixture
    def real_github_client(self, test_settings, real_git_repo):
        """Create a GitHub client that works with local git repo."""
        # Mock the GitHub API calls but use real file operations
        client = GitHubClient(
            token=test_settings.github.token,
            repository=test_settings.github.repository
        )
        
        # Override the create_file method to work with local repo
        async def mock_create_file(filename, content, commit_message, branch="main"):
            file_path = real_git_repo / "posts" / filename
            file_path.write_text(content, encoding='utf-8')
            
            # Add and commit the file
            subprocess.run(["git", "add", str(file_path)], cwd=real_git_repo, check=True)
            subprocess.run(["git", "commit", "-m", commit_message], cwd=real_git_repo, check=True)
            
            # Get commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], 
                cwd=real_git_repo, 
                capture_output=True, 
                text=True, 
                check=True
            )
            commit_sha = result.stdout.strip()
            
            return {
                "commit": {"sha": commit_sha},
                "content": {"html_url": f"file://{file_path}"}
            }
        
        client.create_file = mock_create_file
        client.check_connectivity = AsyncMock(return_value=True)
        
        return client
    
    @pytest.fixture
    def full_system(self, test_settings, real_github_client):
        """Create a complete system with real components."""
        publishing_service = PublishingService(
            github_client=real_github_client,
            settings=test_settings
        )
        
        discord_bot = DiscordInteractionsHandler(test_settings)
        discord_bot.publishing_service = publishing_service
        
        return {
            "discord_bot": discord_bot,
            "publishing_service": publishing_service,
            "github_client": real_github_client
        }
    
    @pytest.mark.asyncio
    async def test_complete_note_workflow(self, full_system, discord_interaction_payloads, real_git_repo):
        """Test complete workflow for creating and publishing a note."""
        discord_bot = full_system["discord_bot"]
        
        # Step 1: User triggers slash command
        command_payload = discord_interaction_payloads["slash_command"]
        command_payload["data"]["options"] = [{"name": "type", "value": "note"}]
        
        modal_response = await discord_bot.handle_interaction(command_payload)
        
        # Verify modal is returned
        assert modal_response["type"] == 9  # MODAL
        assert "note" in modal_response["data"]["custom_id"]
        
        # Step 2: User submits modal
        modal_payload = discord_interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = "post_modal_note"
        modal_payload["data"]["components"] = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": "My First Blog Post"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": "This is my first blog post created through Discord! It covers my thoughts on automated publishing and how it streamlines my workflow."
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "tags",
                    "value": "blogging, automation, discord, publishing"
                }]
            }
        ]
        
        publish_response = await discord_bot.handle_interaction(modal_payload)
        
        # Verify success response
        assert publish_response["type"] == 4  # CHANNEL_MESSAGE_WITH_SOURCE
        assert "successfully" in publish_response["data"]["content"]
        
        # Step 3: Verify file was created in git repo
        posts_dir = real_git_repo / "posts"
        post_files = list(posts_dir.glob("*.md"))
        
        assert len(post_files) == 1  # One post file created
        
        post_file = post_files[0]
        content = post_file.read_text(encoding='utf-8')
        
        # Verify frontmatter and content
        assert "---" in content  # YAML frontmatter delimiters
        assert "title: My First Blog Post" in content
        assert "post_type: note" in content
        assert "published_date:" in content
        assert "tags:" in content
        assert "- blogging" in content
        assert "- automation" in content
        assert "This is my first blog post" in content
        assert "automated publishing" in content
        
        # Step 4: Verify git commit was made
        result = subprocess.run(
            ["git", "log", "--oneline", "-1"], 
            cwd=real_git_repo, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        commit_message = result.stdout.strip()
        assert "My First Blog Post" in commit_message or "blog post" in commit_message.lower()
    
    @pytest.mark.asyncio
    async def test_complete_response_workflow(self, full_system, discord_interaction_payloads, real_git_repo):
        """Test complete workflow for creating a response post."""
        discord_bot = full_system["discord_bot"]
        
        # Slash command for response
        command_payload = discord_interaction_payloads["slash_command"]
        command_payload["data"]["options"] = [{"name": "type", "value": "response"}]
        
        modal_response = await discord_bot.handle_interaction(command_payload)
        assert modal_response["type"] == 9
        
        # Modal submission with response data
        modal_payload = discord_interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = "post_modal_response"
        modal_payload["data"]["components"] = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": "Re: Excellent article on Python testing"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": "Thank you for this comprehensive guide! The section on pytest fixtures was particularly helpful. I've been struggling with test organization and this gives me a clear path forward."
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "target_url",
                    "value": "https://realpython.com/pytest-python-testing/"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "tags",
                    "value": "response, python, testing, pytest"
                }]
            }
        ]
        
        publish_response = await discord_bot.handle_interaction(modal_payload)
        
        assert publish_response["type"] == 4
        assert "successfully" in publish_response["data"]["content"]
        
        # Verify response post file
        posts_dir = real_git_repo / "posts"
        post_files = list(posts_dir.glob("*.md"))
        
        assert len(post_files) == 1
        
        content = post_files[0].read_text(encoding='utf-8')
        
        # Verify response-specific frontmatter
        assert "response_type: response" in content
        assert "in_reply_to: https://realpython.com/pytest-python-testing/" in content
        assert "dt_published:" in content
        assert "- response" in content
        assert "- python" in content
        assert "pytest fixtures" in content
    
    @pytest.mark.asyncio 
    async def test_multiple_posts_workflow(self, full_system, discord_interaction_payloads, real_git_repo):
        """Test creating multiple posts in sequence."""
        discord_bot = full_system["discord_bot"]
        
        # Create first post (note)
        await self._create_test_post(
            discord_bot, 
            discord_interaction_payloads,
            post_type="note",
            title="First Post",
            content="This is my first post."
        )
        
        # Create second post (bookmark)
        await self._create_test_post(
            discord_bot,
            discord_interaction_payloads, 
            post_type="bookmark",
            title="Useful Resource",
            content="Found this helpful resource for Python development.",
            target_url="https://docs.python.org/3/"
        )
        
        # Verify both posts exist
        posts_dir = real_git_repo / "posts"
        post_files = list(posts_dir.glob("*.md"))
        
        assert len(post_files) == 2
        
        # Verify git history
        result = subprocess.run(
            ["git", "log", "--oneline"], 
            cwd=real_git_repo, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        commit_history = result.stdout
        assert "First Post" in commit_history or "first post" in commit_history.lower()
        assert "Useful Resource" in commit_history or "resource" in commit_history.lower()
    
    async def _create_test_post(self, discord_bot, interaction_payloads, post_type, title, content, target_url=None, media_url=None):
        """Helper method to create a test post."""
        # Slash command
        command_payload = interaction_payloads["slash_command"]
        command_payload["data"]["options"] = [{"name": "type", "value": post_type}]
        
        await discord_bot.handle_interaction(command_payload)
        
        # Modal submission
        modal_payload = interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = f"post_modal_{post_type}"
        
        components = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": title
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": content
                }]
            }
        ]
        
        if target_url:
            components.append({
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "target_url",
                    "value": target_url
                }]
            })
        
        if media_url:
            components.append({
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "media_url",
                    "value": media_url
                }]
            })
        
        # Add tags
        components.append({
            "type": 1,
            "components": [{
                "type": 4,
                "custom_id": "tags",
                "value": f"{post_type}, testing"
            }]
        })
        
        modal_payload["data"]["components"] = components
        
        return await discord_bot.handle_interaction(modal_payload)


@pytest.mark.e2e
@pytest.mark.slow
class TestErrorRecoveryWorkflows:
    """Test error handling and recovery in complete workflows."""
    
    @pytest.fixture
    def failing_system(self, test_settings):
        """Create a system that will fail at various points."""
        # GitHub client that fails
        failing_github_client = AsyncMock()
        failing_github_client.check_connectivity.return_value = False
        failing_github_client.create_file.side_effect = Exception("GitHub API Error")
        
        publishing_service = PublishingService(
            github_client=failing_github_client,
            settings=test_settings
        )
        
        discord_bot = DiscordInteractionsHandler(test_settings)
        discord_bot.publishing_service = publishing_service
        
        return {
            "discord_bot": discord_bot,
            "publishing_service": publishing_service,
            "github_client": failing_github_client
        }
    
    @pytest.mark.asyncio
    async def test_github_failure_workflow(self, failing_system, discord_interaction_payloads):
        """Test workflow when GitHub operations fail."""
        discord_bot = failing_system["discord_bot"]
        
        # Create modal submission
        modal_payload = discord_interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = "post_modal_note"
        modal_payload["data"]["components"] = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": "This Will Fail"
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": "This post will fail to publish due to GitHub error."
                }]
            }
        ]
        
        response = await discord_bot.handle_interaction(modal_payload)
        
        # Should return error message to user
        assert response["type"] == 4
        assert "error" in response["data"]["content"].lower()
        assert "github" in response["data"]["content"].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_data_workflow(self, full_system, discord_interaction_payloads):
        """Test workflow with invalid or missing data."""
        discord_bot = full_system["discord_bot"]
        
        # Modal with missing required fields
        modal_payload = discord_interaction_payloads["modal_submit"]
        modal_payload["data"]["custom_id"] = "post_modal_response"
        modal_payload["data"]["components"] = [
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "title",
                    "value": ""  # Empty title
                }]
            },
            {
                "type": 1,
                "components": [{
                    "type": 4,
                    "custom_id": "content",
                    "value": "Response without title or target URL"
                }]
            }
            # Missing target_url for response post
        ]
        
        response = await discord_bot.handle_interaction(modal_payload)
        
        # Should handle validation error gracefully
        assert response["type"] == 4
        assert "error" in response["data"]["content"].lower()


@pytest.mark.e2e
@pytest.mark.network
@pytest.mark.skipif(
    "not config.getoption('--run-network-tests')",
    reason="Network tests only run with --run-network-tests flag"
)
class TestRealSystemIntegration:
    """Test integration with real external systems (requires network)."""
    
    @pytest.mark.asyncio
    async def test_api_server_full_startup(self):
        """Test complete API server startup and basic functionality."""
        import subprocess
        import time
        import aiohttp
        import signal
        import os
        
        # Start the API server
        process = subprocess.Popen([
            "uv", "run", "dpb", "api", "--port", "8998"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            # Wait for startup
            await asyncio.sleep(5)
            
            # Test health endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8998/health") as response:
                    assert response.status == 200
                    
                    data = await response.json()
                    assert data["status"] == "healthy"
                    assert "version" in data
                    assert "environment" in data
                
                # Test root endpoint
                async with session.get("http://localhost:8998/") as response:
                    assert response.status == 200
                    
                    data = await response.json()
                    assert "service" in data
                    assert "endpoints" in data
        
        finally:
            # Clean shutdown
            if os.name == 'nt':
                process.terminate()
            else:
                process.send_signal(signal.SIGTERM)
            
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


# Pytest configuration for E2E tests
def pytest_configure(config):
    """Configure E2E test markers and options."""
    if not hasattr(config.option, 'run_network_tests'):
        config.addinivalue_line(
            "markers",
            "network: marks tests as requiring network connectivity"
        )
