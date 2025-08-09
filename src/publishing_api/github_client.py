"""
GitHub client for repository operations.

Handles file creation, updates, commits, branch management, and pull request creation.
Enhanced for automated content publishing with branch-based workflows.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from github import Github, GithubException
from github.GitRef import GitRef
from github.PullRequest import PullRequest
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

    async def create_branch(
        self, branch_name: str, base_branch: str = "main"
    ) -> Tuple[bool, str]:
        """
        Create a new branch from base branch.

        Args:
            branch_name: Name of the new branch
            base_branch: Base branch to create from

        Returns:
            Tuple of (success, message)
        """
        try:

            def create():
                # Get the base branch reference
                base_ref = self.repo.get_git_ref(f"heads/{base_branch}")
                base_sha = base_ref.object.sha

                # Check if branch already exists
                try:
                    existing_ref = self.repo.get_git_ref(f"heads/{branch_name}")
                    return False, f"Branch {branch_name} already exists"
                except GithubException as e:
                    if e.status != 404:
                        raise

                # Create new branch
                new_ref = self.repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}", sha=base_sha
                )
                
                logger.info(f"Created branch {branch_name} from {base_branch}")
                return True, f"Successfully created branch {branch_name}"

            return await asyncio.get_event_loop().run_in_executor(None, create)

        except GithubException as e:
            error_msg = f"GitHub API error creating branch: {e.data.get('message', str(e))}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to create branch: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a pull request.

        Args:
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch
            draft: Whether to create as draft

        Returns:
            Tuple of (success, message, pr_url)
        """
        try:

            def create_pr():
                # Create pull request
                pr = self.repo.create_pull(
                    title=title, body=body, head=head_branch, base=base_branch, draft=draft
                )
                
                logger.info(f"Created PR #{pr.number}: {title}")
                return True, f"Successfully created PR #{pr.number}", pr.html_url

            return await asyncio.get_event_loop().run_in_executor(None, create_pr)

        except GithubException as e:
            error_msg = f"GitHub API error creating PR: {e.data.get('message', str(e))}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Failed to create PR: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    async def get_branch_info(self, branch_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a branch.

        Args:
            branch_name: Name of the branch

        Returns:
            Branch information dict or None if not found
        """
        try:

            def get_info():
                try:
                    branch = self.repo.get_branch(branch_name)
                    return {
                        "name": branch.name,
                        "sha": branch.commit.sha,
                        "protected": branch.protected,
                        "commit_message": branch.commit.commit.message,
                        "commit_date": branch.commit.commit.author.date.isoformat(),
                    }
                except GithubException as e:
                    if e.status == 404:
                        return None
                    raise

            return await asyncio.get_event_loop().run_in_executor(None, get_info)

        except Exception as e:
            logger.error(f"Failed to get branch info: {str(e)}")
            return None

    async def delete_branch(self, branch_name: str) -> Tuple[bool, str]:
        """
        Delete a branch.

        Args:
            branch_name: Name of the branch to delete

        Returns:
            Tuple of (success, message)
        """
        try:

            def delete():
                # Check if branch exists
                try:
                    branch_ref = self.repo.get_git_ref(f"heads/{branch_name}")
                except GithubException as e:
                    if e.status == 404:
                        return False, f"Branch {branch_name} does not exist"
                    raise

                # Delete the branch
                branch_ref.delete()
                logger.info(f"Deleted branch {branch_name}")
                return True, f"Successfully deleted branch {branch_name}"

            return await asyncio.get_event_loop().run_in_executor(None, delete)

        except GithubException as e:
            error_msg = f"GitHub API error deleting branch: {e.data.get('message', str(e))}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to delete branch: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def generate_branch_name(
        self, content_type: str, message_id: str, user_id: str = None
    ) -> str:
        """
        Generate branch name following established conventions.

        Args:
            content_type: Type of content (note, response, bookmark, media)
            message_id: Discord message ID
            user_id: Optional Discord user ID

        Returns:
            Generated branch name
        """
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        if user_id:
            return f"content/discord-bot/{date_str}/{content_type}/{user_id}-{message_id}"
        else:
            return f"content/discord-bot/{date_str}/{content_type}/{message_id}"

    def generate_pr_template(
        self,
        content_type: str,
        content_preview: str,
        user_id: str,
        message_id: str,
        validation_results: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        """
        Generate PR title and body using established template.

        Args:
            content_type: Type of content
            content_preview: Preview of content
            user_id: Discord user ID
            message_id: Discord message ID
            validation_results: Optional validation results

        Returns:
            Tuple of (title, body)
        """
        # Generate title
        preview_snippet = content_preview[:50].strip()
        if len(content_preview) > 50:
            preview_snippet += "..."
        
        title = f"Add {content_type} post: {preview_snippet}"
        
        # Generate body
        body = f"""## 📝 Automated Content Publication

**Content Type**: {content_type}
**Source**: Discord Bot
**User ID**: {user_id}
**Message ID**: {message_id}
**Date**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

### Content Preview
```
{content_preview[:200]}{"..." if len(content_preview) > 200 else ""}
```

### Validation Status
"""
        
        if validation_results:
            for check, result in validation_results.items():
                status = "✅" if result.get("passed", False) else "❌"
                body += f"- {status} {check}: {result.get('message', 'Unknown')}\n"
        else:
            body += "- ⏳ Validation pending\n"
        
        body += f"""
### Review Instructions
- Verify content quality and appropriateness
- Check frontmatter schema compliance
- Validate directory structure placement
- Confirm no sensitive information is exposed

### Actions Available
- **Approve and Merge**: Content will be published to site
- **Request Changes**: Provide feedback for content improvement  
- **Close**: Reject publication (branch will be cleaned up)

### Emergency Contact
If urgent issues arise, contact the repository maintainer immediately.

---
*This PR was created automatically by the Discord Publishing Bot*
"""
        
        return title, body

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

    async def commit_file_to_branch(
        self,
        filepath: str,
        content: str,
        commit_message: str,
        branch_name: str,
        create_pr: bool = True,
        pr_title: str = None,
        pr_body: str = None,
    ) -> Dict[str, Any]:
        """
        Enhanced commit workflow: create branch, commit file, and optionally create PR.

        Args:
            filepath: Path to file in repository
            content: File content
            commit_message: Commit message
            branch_name: Name of branch to create and commit to
            create_pr: Whether to create a PR after commit
            pr_title: PR title (generated if not provided)
            pr_body: PR body (generated if not provided)

        Returns:
            Dictionary with operation results

        Raises:
            Exception if any operation fails
        """
        result = {
            "branch_created": False,
            "file_committed": False,
            "pr_created": False,
            "branch_name": branch_name,
            "commit_sha": None,
            "pr_url": None,
            "error": None,
        }

        try:
            # Step 1: Create branch
            branch_success, branch_message = await self.create_branch(branch_name)
            if not branch_success:
                result["error"] = f"Branch creation failed: {branch_message}"
                return result
            
            result["branch_created"] = True
            logger.info(f"Created branch: {branch_name}")

            # Step 2: Commit file to new branch
            commit_sha = await self.commit_file(
                filepath=filepath,
                content=content,
                commit_message=commit_message,
                branch=branch_name,
            )
            
            result["file_committed"] = True
            result["commit_sha"] = commit_sha
            logger.info(f"Committed file {filepath} to branch {branch_name}")

            # Step 3: Create PR if requested
            if create_pr:
                if not pr_title:
                    pr_title = f"Add content: {filepath}"
                if not pr_body:
                    pr_body = f"Automated content publication\n\nFile: {filepath}\nBranch: {branch_name}\nCommit: {commit_sha}"

                pr_success, pr_message, pr_url = await self.create_pull_request(
                    title=pr_title,
                    body=pr_body,
                    head_branch=branch_name,
                    base_branch="main",
                    draft=False,
                )
                
                if pr_success:
                    result["pr_created"] = True
                    result["pr_url"] = pr_url
                    logger.info(f"Created PR: {pr_url}")
                else:
                    result["error"] = f"PR creation failed: {pr_message}"
                    # Note: Branch and commit were successful, so this is a partial success

            return result

        except Exception as e:
            error_msg = f"Enhanced commit workflow failed: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            
            # Attempt cleanup if branch was created but commit failed
            if result["branch_created"] and not result["file_committed"]:
                try:
                    await self.delete_branch(branch_name)
                    logger.info(f"Cleaned up failed branch: {branch_name}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup branch {branch_name}: {cleanup_error}")
            
            raise Exception(error_msg)
