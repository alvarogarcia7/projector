"""Command execution cache for runner."""

import fnmatch
import hashlib
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _read_projector_ignore() -> list:
    """Read patterns from .projector/.projectorignore file."""
    ignore_path = Path.cwd() / ".projector" / ".projectorignore"
    if not ignore_path.exists():
        return []
    try:
        with open(ignore_path) as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except Exception:
        return []


def _is_projector_ignored(filepath: str, patterns: list) -> bool:
    """Check if a filepath matches any .projectorignore pattern."""
    return any(
        fnmatch.fnmatch(filepath, p) or fnmatch.fnmatch(os.path.basename(filepath), p)
        for p in patterns
    )


def get_git_changed_files_hash() -> Optional[str]:
    """
    Compute SHA256 hash based on git HEAD and any modified/untracked files.
    For a clean working directory, returns the HEAD SHA.
    For modified files, computes a hash combining HEAD SHA and file contents.
    Returns None if not in a git repo or on error.
    """
    logger.debug("Computing git changed files hash for cache")
    try:
        # Get HEAD SHA
        logger.debug("Executing: git rev-parse HEAD")
        head_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        head_sha = head_result.stdout.strip()
        logger.debug(f"HEAD SHA: {head_sha[:7]}")

        # Check git status
        logger.debug("Executing: git status --porcelain")
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )

        status_output = status_result.stdout.strip()

        if not status_output:
            logger.debug(f"Working directory clean, using HEAD SHA as hash: {head_sha[:7]}")
            return head_sha

        # Working directory has changes, compute hash with file contents
        logger.debug("Working directory has changes, computing hash with file contents")
        hasher = hashlib.sha256()
        hasher.update(head_sha.encode())

        logger.debug("Executing: git ls-files -m -o --exclude-standard")
        files_result = subprocess.run(
            ["git", "ls-files", "-m", "-o", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        )
        changed_files = [f for f in files_result.stdout.strip().split("\n") if f]
        logger.debug(f"Found {len(changed_files)} changed/untracked files")

        ignore_patterns = _read_projector_ignore()
        if ignore_patterns:
            before = len(changed_files)
            changed_files = [f for f in changed_files if not _is_projector_ignored(f, ignore_patterns)]
            filtered = before - len(changed_files)
            logger.debug(f".projectorignore filtered {filtered} file(s), {len(changed_files)} remain")

        files_hashed = 0
        for filepath in sorted(changed_files):
            try:
                with open(filepath, "rb") as f:
                    hasher.update(filepath.encode())
                    hasher.update(f.read())
                    files_hashed += 1
            except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
                logger.debug(f"Could not hash file {filepath}: {e}")

        final_hash = hasher.hexdigest()
        logger.debug(f"Computed hash from HEAD + {files_hashed} file(s): {final_hash[:7]}")
        return final_hash
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to compute git hash: {e}")
        return None
    except FileNotFoundError:
        logger.error("git command not found. Is git installed and in PATH?")
        return None


def get_cache_entry(db, project_id: int, worktree_id: int, command: str, files_hash: str) -> Optional[dict]:
    """
    Retrieve cached command execution result if available.
    Returns None if no cache entry exists.
    """
    return db.fetchone(
        """
        SELECT stdout, stderr, exit_code, execution_time, cached_at
        FROM command_cache
        WHERE project_id = ? AND worktree_id = ? AND command = ? AND files_hash = ?
        ORDER BY cached_at DESC
        LIMIT 1
        """,
        (project_id, worktree_id, command, files_hash),
    )


def save_cache_entry(
    db,
    project_id: int,
    worktree_id: int,
    command: str,
    files_hash: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    execution_time: float,
    machine_id: str,
) -> None:
    """Save a command execution result to cache."""
    from datetime import datetime

    existing = db.fetchone(
        """
        SELECT id FROM command_cache
        WHERE project_id = ? AND worktree_id = ? AND command = ? AND files_hash = ?
        """,
        (project_id, worktree_id, command, files_hash),
    )

    if existing:
        db.execute(
            """
            UPDATE command_cache
            SET stdout = ?, stderr = ?, exit_code = ?, execution_time = ?, cached_at = ?, machine_id = ?
            WHERE id = ?
            """,
            (stdout, stderr, exit_code, execution_time, datetime.now(), machine_id, existing["id"]),
        )
    else:
        db.insert_and_get_id(
            "command_cache",
            project_id=project_id,
            worktree_id=worktree_id,
            command=command,
            files_hash=files_hash,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time=execution_time,
            cached_at=datetime.now(),
            machine_id=machine_id,
        )
    db.commit()


def clear_cache_entry(db, project_id: int, worktree_id: int, command: str) -> None:
    """Clear all cache entries for a specific command."""
    db.execute(
        "DELETE FROM command_cache WHERE project_id = ? AND worktree_id = ? AND command = ?",
        (project_id, worktree_id, command),
    )
    db.commit()
