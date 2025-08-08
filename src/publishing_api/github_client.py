"""
GitHub client for repository operations.

Handles file creation, updates, and commits to GitHub repositories.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from github import Github, GithubException
from github.GitRef import GitRef
from github.Repository import Repository

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for GitHub repository operations."""

    def __init__(self, token: str, repo_name: str):
        self.token = token
        self.repo_name = repo_name
        self._github = None
        self._repo = None

    @property
    def github(self) -> Github:
        """Get or create GitHub client instance."""
        if self._github is None:
            self._github = Github(self.token)
        return self._github

    @property
    def repo(self) -> Repository:
        """Get or create repository instance."""
        if self._repo is None:
            self._repo = self.github.get_repo(self.repo_name)
        return self._repo

    async def check_connectivity(self) -> bool:
        """
        Check if GitHub API is accessible and repository exists.

        Returns:
            True if connection is successful

        Raises:
            Exception if connection fails
        """
        try:
            # Run in thread pool to avoid blocking async loop
            def check():
                repo = self.repo
                repo.get_branch("main")  # Try to access default branch
                return True

            return await asyncio.get_event_loop().run_in_executor(None, check)

        except GithubException as e:
            if e.status == 404:
                raise Exception(
                    f"Repository {self.repo_name} not found or not accessible"
                )
            elif e.status == 401:
                raise Exception("Invalid GitHub token or insufficient permissions")
            else:
                raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
        except Exception as e:
            raise Exception(f"Failed to connect to GitHub: {str(e)}")

    async def commit_file(
        self, filepath: str, content: str, commit_message: str, branch: str = "main"
    ) -> str:
        """
        Create or update a file in the repository.

        Args:
            filepath: Path to file in repository
            content: File content
            commit_message: Commit message
            branch: Target branch

        Returns:
            Commit SHA

        Raises:
            Exception if commit fails
        """
        try:

            def commit():
                try:
                    # Try to get existing file
                    existing_file = self.repo.get_contents(filepath, ref=branch)

                    # Update existing file
                    commit_result = self.repo.update_file(
                        path=filepath,
                        message=commit_message,
                        content=content,
                        sha=existing_file.sha,
                        branch=branch,
                    )
                    logger.info(f"Updated existing file: {filepath}")

                except GithubException as e:
                    if e.status == 404:
                        # File doesn't exist, create new
                        commit_result = self.repo.create_file(
                            path=filepath,
                            message=commit_message,
                            content=content,
                            branch=branch,
                        )
                        logger.info(f"Created new file: {filepath}")
                    else:
                        raise

                return commit_result["commit"].sha

            # Run in thread pool
            commit_sha = await asyncio.get_event_loop().run_in_executor(None, commit)
            logger.info(f"Successfully committed {filepath} with SHA {commit_sha}")
            return commit_sha

        except GithubException as e:
            error_msg = f"GitHub API error: {e.data.get('message', str(e))}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to commit file: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def get_file_content(
        self, filepath: str, branch: str = "main"
    ) -> Optional[str]:
        """
        Get content of a file from the repository.

        Args:
            filepath: Path to file in repository
            branch: Branch to read from

        Returns:
            File content as string, or None if file doesn't exist
        """
        try:

            def get_content():
                try:
                    file_content = self.repo.get_contents(filepath, ref=branch)
                    return file_content.decoded_content.decode("utf-8")
                except GithubException as e:
                    if e.status == 404:
                        return None
                    raise

            return await asyncio.get_event_loop().run_in_executor(None, get_content)

        except Exception as e:
            logger.error(f"Failed to get file content: {str(e)}")
            return None

    async def list_files(self, directory: str = "", branch: str = "main") -> list:
        """
        List files in a directory.

        Args:
            directory: Directory path (empty for root)
            branch: Branch to list from

        Returns:
            List of file paths
        """
        try:

            def list_dir():
                contents = self.repo.get_contents(directory, ref=branch)
                if not isinstance(contents, list):
                    contents = [contents]

                files = []
                for item in contents:
                    if item.type == "file":
                        files.append(item.path)
                    elif item.type == "dir":
                        # Recursively list subdirectory
                        subfiles = self.repo.get_contents(item.path, ref=branch)
                        for subitem in subfiles:
                            if subitem.type == "file":
                                files.append(subitem.path)

                return files

            return await asyncio.get_event_loop().run_in_executor(None, list_dir)

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []
