"""Git integration for auto-detecting SHA, message, and author."""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def is_git_repo(path: Path = None) -> bool:
    """Check if we're inside a git repository."""
    if path is None:
        path = Path.cwd()

    logger.debug(f"Checking if git repository at {path}")
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=str(path),
            capture_output=True,
            check=True,
        )
        logger.debug(f"Git repository found at {path}")
        return True
    except subprocess.CalledProcessError:
        logger.debug(f"Not a git repository at {path}: git command failed")
        return False
    except FileNotFoundError:
        logger.error("git command not found. Is git installed and in PATH?")
        return False


def get_git_branch() -> Optional[str]:
    """
    Get the current git branch name.
    Returns the branch name or None if not in a git repo.
    """
    if not is_git_repo():
        logger.debug("Not in a git repository, cannot get branch")
        return None

    logger.debug("Retrieving current git branch")
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip() or None
        logger.debug(f"Current git branch: {branch}")
        return branch
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get git branch: {e}")
        return None
    except FileNotFoundError:
        logger.error("git command not found. Is git installed and in PATH?")
        return None


def get_git_info() -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    """
    Auto-detect current git SHA, commit message, and author.
    Returns tuple of (sha, message, author) or None if not in a git repo.
    """
    if not is_git_repo():
        logger.debug("Not in a git repository, cannot get git info")
        return None

    logger.debug("Retrieving git information (SHA, message, author)")
    try:
        # Get SHA
        logger.debug("Executing: git rev-parse HEAD")
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        sha = sha_result.stdout.strip()
        logger.debug(f"Git SHA: {sha[:7]}")

        # Get commit message
        logger.debug("Executing: git log -1 --pretty=%B")
        message_result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            capture_output=True,
            text=True,
            check=True,
        )
        message = message_result.stdout.strip() or None
        logger.debug(f"Git message: {message[:50] if message else '(none)'}")

        # Get author
        logger.debug("Executing: git log -1 --pretty=%an")
        author_result = subprocess.run(
            ["git", "log", "-1", "--pretty=%an"],
            capture_output=True,
            text=True,
            check=True,
        )
        author = author_result.stdout.strip() or None
        logger.debug(f"Git author: {author}")

        logger.debug(f"Successfully retrieved git info: sha={sha[:7]}, author={author}")
        return sha, message, author
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to retrieve git information: {e}")
        return None
    except FileNotFoundError:
        logger.error("git command not found. Is git installed and in PATH?")
        return None
