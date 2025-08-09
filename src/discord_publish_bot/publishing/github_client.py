"""
GitHub client for repository operations.

Modernized GitHub client with async support and proper error handling.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from github import Github, GithubException
from github.GitRef import GitRef
from github.PullRequest import PullRequest
from github.Repository import Repository

from ..shared import (
    GitHubError, 
    GitHubAuthenticationError, 
    GitHubRepositoryError,
    mask_sensitive_data
)

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Modern GitHub client with async support and proper error handling.
    
    Provides repository operations for content publishing workflows.
    """

    def __init__(self, token: str, repository: str):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token
            repository: Repository in format 'owner/repo'
        """
        self.token = token
        self.repository = repository
        self._github = None
        self._repo = None
        
        logger.info(f"Initialized GitHub client for repository: {repository}")

    @property
    def github(self) -> Github:
        """Get or create GitHub client instance."""
        if self._github is None:
            try:
                self._github = Github(self.token)
                # Test authentication by getting user info
                user = self._github.get_user()
                logger.debug(f"Authenticated as GitHub user: {user.login}")
            except Exception as e:
                logger.error(f"GitHub authentication failed: {e}")
                raise GitHubAuthenticationError(f"Failed to authenticate with GitHub: {e}")
        return self._github

    @property
    def repo(self) -> Repository:
        """Get or create repository instance."""
        if self._repo is None:
            try:
                self._repo = self.github.get_repo(self.repository)
                logger.debug(f"Connected to repository: {self.repository}")
            except Exception as e:
                logger.error(f"Failed to access repository {self.repository}: {e}")
                raise GitHubRepositoryError(
                    f"Failed to access repository {self.repository}: {e}",
                    repository=self.repository
                )
        return self._repo

    async def check_connectivity(self) -> bool:
        """
        Check if GitHub API is accessible and repository exists.

        Returns:
            True if connection is successful
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.repo.name)
            logger.info("GitHub connectivity check successful")
            return True
        except Exception as e:
            logger.error(f"GitHub connectivity check failed: {e}")
            return False

    async def create_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a new file in the repository.

        Args:
            path: File path in repository
            content: File content
            message: Commit message
            branch: Target branch

        Returns:
            Dictionary with commit information

        Raises:
            GitHubError: If file creation fails
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.repo.create_file(path, message, content, branch=branch)
            )
            
            commit_info = {
                "sha": result["commit"].sha,
                "path": path,
                "branch": branch,
                "message": message,
                "url": result["content"].html_url
            }
            
            logger.info(f"Created file {path} on branch {branch}: {result['commit'].sha}")
            return commit_info
            
        except GithubException as e:
            logger.error(f"Failed to create file {path}: {e}")
            raise GitHubError(f"Failed to create file {path}: {e}", operation="create_file")
        except Exception as e:
            logger.error(f"Unexpected error creating file {path}: {e}")
            raise GitHubError(f"Unexpected error creating file: {e}", operation="create_file")

    async def update_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Update an existing file in the repository.

        Args:
            path: File path in repository
            content: New file content
            message: Commit message
            branch: Target branch

        Returns:
            Dictionary with commit information

        Raises:
            GitHubError: If file update fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Get current file to get SHA
            current_file = await loop.run_in_executor(
                None,
                lambda: self.repo.get_contents(path, ref=branch)
            )
            
            result = await loop.run_in_executor(
                None,
                lambda: self.repo.update_file(
                    path, message, content, current_file.sha, branch=branch
                )
            )
            
            commit_info = {
                "sha": result["commit"].sha,
                "path": path,
                "branch": branch,
                "message": message,
                "url": result["content"].html_url
            }
            
            logger.info(f"Updated file {path} on branch {branch}: {result['commit'].sha}")
            return commit_info
            
        except GithubException as e:
            if e.status == 404:
                # File doesn't exist, create it instead
                logger.info(f"File {path} not found, creating new file")
                return await self.create_file(path, content, message, branch)
            else:
                logger.error(f"Failed to update file {path}: {e}")
                raise GitHubError(f"Failed to update file {path}: {e}", operation="update_file")
        except Exception as e:
            logger.error(f"Unexpected error updating file {path}: {e}")
            raise GitHubError(f"Unexpected error updating file: {e}", operation="update_file")

    async def create_commit(
        self,
        filename: str,
        content: str,
        message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create or update a file with a commit.

        Args:
            filename: Name of the file
            content: File content
            message: Commit message
            branch: Target branch

        Returns:
            Dictionary with commit information
        """
        try:
            # Try to update first, fallback to create
            return await self.update_file(filename, content, message, branch)
        except GitHubError as e:
            if "404" in str(e):
                return await self.create_file(filename, content, message, branch)
            else:
                raise

    async def create_branch(self, branch_name: str, source_branch: str = "main") -> GitRef:
        """
        Create a new branch.

        Args:
            branch_name: Name of the new branch
            source_branch: Source branch to branch from

        Returns:
            GitRef object for the new branch

        Raises:
            GitHubError: If branch creation fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Get source branch SHA
            source_ref = await loop.run_in_executor(
                None,
                lambda: self.repo.get_git_ref(f"heads/{source_branch}")
            )
            
            # Create new branch
            new_ref = await loop.run_in_executor(
                None,
                lambda: self.repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}",
                    sha=source_ref.object.sha
                )
            )
            
            logger.info(f"Created branch {branch_name} from {source_branch}")
            return new_ref
            
        except GithubException as e:
            if e.status == 422 and "already exists" in str(e):
                logger.warning(f"Branch {branch_name} already exists")
                return await loop.run_in_executor(
                    None,
                    lambda: self.repo.get_git_ref(f"heads/{branch_name}")
                )
            else:
                logger.error(f"Failed to create branch {branch_name}: {e}")
                raise GitHubError(f"Failed to create branch: {e}", operation="create_branch")
        except Exception as e:
            logger.error(f"Unexpected error creating branch {branch_name}: {e}")
            raise GitHubError(f"Unexpected error creating branch: {e}", operation="create_branch")

    async def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> PullRequest:
        """
        Create a pull request.

        Args:
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch

        Returns:
            PullRequest object

        Raises:
            GitHubError: If PR creation fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            pr = await loop.run_in_executor(
                None,
                lambda: self.repo.create_pull(
                    title=title,
                    body=body,
                    head=head_branch,
                    base=base_branch
                )
            )
            
            logger.info(f"Created pull request #{pr.number}: {title}")
            return pr
            
        except GithubException as e:
            logger.error(f"Failed to create pull request: {e}")
            raise GitHubError(f"Failed to create pull request: {e}", operation="create_pull_request")
        except Exception as e:
            logger.error(f"Unexpected error creating pull request: {e}")
            raise GitHubError(f"Unexpected error creating pull request: {e}", operation="create_pull_request")

    async def list_files(self, path: str = "", branch: str = "main") -> List[Dict[str, Any]]:
        """
        List files in a directory.

        Args:
            path: Directory path (empty for root)
            branch: Branch to list files from

        Returns:
            List of file information dictionaries

        Raises:
            GitHubError: If listing fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            contents = await loop.run_in_executor(
                None,
                lambda: self.repo.get_contents(path, ref=branch)
            )
            
            # Handle both single file and directory contents
            if not isinstance(contents, list):
                contents = [contents]
            
            files = [
                {
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": item.size,
                    "sha": item.sha,
                    "url": item.html_url
                }
                for item in contents
            ]
            
            logger.debug(f"Listed {len(files)} files in {path or 'root'}")
            return files
            
        except GithubException as e:
            if e.status == 404:
                logger.warning(f"Path {path} not found in repository")
                return []
            else:
                logger.error(f"Failed to list files in {path}: {e}")
                raise GitHubError(f"Failed to list files: {e}", operation="list_files")
        except Exception as e:
            logger.error(f"Unexpected error listing files in {path}: {e}")
            raise GitHubError(f"Unexpected error listing files: {e}", operation="list_files")

    async def delete_branch(self, branch_name: str) -> bool:
        """
        Delete a branch.

        Args:
            branch_name: Name of the branch to delete

        Returns:
            True if deletion was successful

        Raises:
            GitHubError: If branch deletion fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            ref = await loop.run_in_executor(
                None,
                lambda: self.repo.get_git_ref(f"heads/{branch_name}")
            )
            
            await loop.run_in_executor(None, ref.delete)
            
            logger.info(f"Deleted branch {branch_name}")
            return True
            
        except GithubException as e:
            if e.status == 404:
                logger.warning(f"Branch {branch_name} not found")
                return True  # Consider missing branch as successfully deleted
            else:
                logger.error(f"Failed to delete branch {branch_name}: {e}")
                raise GitHubError(f"Failed to delete branch: {e}", operation="delete_branch")
        except Exception as e:
            logger.error(f"Unexpected error deleting branch {branch_name}: {e}")
            raise GitHubError(f"Unexpected error deleting branch: {e}", operation="delete_branch")

    def __repr__(self) -> str:
        """String representation for debugging."""
        token_masked = mask_sensitive_data(self.token)
        return f"GitHubClient(repository='{self.repository}', token='{token_masked}')"
