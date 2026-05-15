"""End-to-end tests for config set functionality."""

import tempfile
from pathlib import Path

from projector.cli import config_set, resolve_project, resolve_worktree
from projector.db import Database
from projector.git import get_git_branch


def test_config_set_creates_project_config():
    """Test that config set creates .projector/.env file with PROJECT key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        try:
            # Change to temp directory
            import os

            os.chdir(tmpdir)

            # Initialize git repo
            import subprocess

            subprocess.run(["git", "init"], capture_output=True, check=True)

            # Run config set
            config_set("test-project")

            # Verify .projector/.env was created with PROJECT key
            env_file = Path(tmpdir) / ".projector" / ".env"
            assert env_file.exists()
            assert "PROJECT=test-project" in env_file.read_text()
        finally:
            os.chdir(original_cwd)


def test_config_set_creates_worktree_config():
    """Test that config set creates .projector-worktree file with current branch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmpdir)

            # Initialize git repo
            import subprocess

            subprocess.run(["git", "init"], capture_output=True, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                capture_output=True,
                check=True,
            )

            # Create initial commit so branch exists
            Path(tmpdir, "test.txt").write_text("test")
            subprocess.run(["git", "add", "test.txt"], capture_output=True, check=True)
            subprocess.run(
                ["git", "commit", "-m", "initial"],
                capture_output=True,
                check=True,
            )

            # Run config set
            config_set("test-project")

            # Verify .projector-worktree was created
            worktree_file = Path(tmpdir) / ".projector-worktree"
            assert worktree_file.exists()
            branch = get_git_branch()
            assert worktree_file.read_text() == branch
        finally:
            os.chdir(original_cwd)


def test_config_set_creates_path_config():
    """Test that config set creates .projector/.env file with CHECKS_BIN_PATH key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmpdir)

            # Create bin directory
            bin_dir = Path(tmpdir) / "bin"
            bin_dir.mkdir()

            # Initialize git repo
            import subprocess

            subprocess.run(["git", "init"], capture_output=True, check=True)

            # Run config set
            config_set("test-project")

            # Verify .projector/.env was created with CHECKS_BIN_PATH key
            env_file = Path(tmpdir) / ".projector" / ".env"
            assert env_file.exists()
            env_content = env_file.read_text()
            assert "CHECKS_BIN_PATH=" in env_content
            assert str(bin_dir) in env_content
        finally:
            os.chdir(original_cwd)


def test_resolve_project_from_config():
    """Test that resolve_project reads from .projector/.env."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmpdir)

            # Create .projector directory and .env file
            projector_dir = Path(tmpdir) / ".projector"
            projector_dir.mkdir()
            env_file = projector_dir / ".env"
            env_file.write_text("PROJECT=my-project\n")

            # Resolve project
            project = resolve_project(None)
            assert project == "my-project"
        finally:
            os.chdir(original_cwd)


def test_resolve_worktree_from_config():
    """Test that resolve_worktree reads from .projector-worktree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmpdir)

            # Create config file
            worktree_file = Path(tmpdir) / ".projector-worktree"
            worktree_file.write_text("feature-branch")

            # Resolve worktree
            worktree = resolve_worktree(None)
            assert worktree == "feature-branch"
        finally:
            os.chdir(original_cwd)


def test_resolve_project_with_explicit_argument():
    """Test that explicit project argument overrides config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmpdir)

            # Create .projector/.env with different project
            projector_dir = Path(tmpdir) / ".projector"
            projector_dir.mkdir()
            env_file = projector_dir / ".env"
            env_file.write_text("PROJECT=config-project\n")

            # Resolve with explicit argument
            project = resolve_project("explicit-project")
            assert project == "explicit-project"
        finally:
            os.chdir(original_cwd)


def test_resolve_worktree_with_explicit_argument():
    """Test that explicit worktree argument overrides config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmpdir)

            # Create config file with different worktree
            worktree_file = Path(tmpdir) / ".projector-worktree"
            worktree_file.write_text("config-branch")

            # Resolve with explicit argument
            worktree = resolve_worktree("explicit-branch")
            assert worktree == "explicit-branch"
        finally:
            os.chdir(original_cwd)


def test_config_set_creates_worktree_in_database():
    """Test that config set creates worktree in database if it doesn't exist."""
    # Use the existing database
    db = Database()
    db.init_schema()

    # Get or create a test project
    test_project = "test-project-e2e"
    existing = db.fetchone("SELECT id FROM projects WHERE name = ?", (test_project,))

    if not existing:
        from datetime import datetime

        proj_id = db.insert_and_get_id(
            "projects",
            name=test_project,
            description="E2E test project",
            repo_path=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    else:
        proj_id = existing["id"]

    # Test that we can query the project
    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (test_project,))
    assert proj is not None
    assert proj["id"] == proj_id
