"""Git integration for auto-detecting SHA, message, and author."""

import subprocess
from pathlib import Path
from typing import Optional, Tuple


def is_git_repo(path: Path = None) -> bool:
    """Check if we're inside a git repository."""
    if path is None:
        path = Path.cwd()

    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=str(path),
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_git_branch() -> Optional[str]:
    """
    Get the current git branch name.
    Returns the branch name or None if not in a git repo.
    """
    if not is_git_repo():
        return None

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_git_info() -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    """
    Auto-detect current git SHA, commit message, and author.
    Returns tuple of (sha, message, author) or None if not in a git repo.
    """
    if not is_git_repo():
        return None

    try:
        # Get SHA
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        sha = sha_result.stdout.strip()

        # Get commit message
        message_result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            capture_output=True,
            text=True,
            check=True,
        )
        message = message_result.stdout.strip() or None

        # Get author
        author_result = subprocess.run(
            ["git", "log", "-1", "--pretty=%an"],
            capture_output=True,
            text=True,
            check=True,
        )
        author = author_result.stdout.strip() or None

        return sha, message, author
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
