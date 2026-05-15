"""Tests for check execution caching mechanism."""

import tempfile
import uuid
from pathlib import Path

from projector.db import Database


class TestCheckCaching:
    """Test caching mechanism for check execution."""

    def setup_method(self):
        """Set up test database and environment."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.original_cwd = Path.cwd()
        import os

        os.chdir(self.test_dir.name)
        self.unique_id = str(uuid.uuid4())[:8]

    def teardown_method(self):
        """Clean up test environment."""
        import os

        os.chdir(self.original_cwd)
        self.test_dir.cleanup()

    def _unique_name(self, base: str) -> str:
        """Generate a unique name for this test."""
        return f"{base}-{self.unique_id}"

    def test_cache_entry_creation_and_retrieval(self):
        """Test creating and retrieving a cache entry."""
        db = Database()
        db.init_schema()

        # Create test data
        proj_id = db.insert_and_get_id("projects", name=self._unique_name("test-project"), description="Test")
        wt_id = db.insert_and_get_id("worktrees", project_id=proj_id, name="main")

        # Import cache functions
        from projector.cache import get_cache_entry, save_cache_entry

        # Save a cache entry
        save_cache_entry(
            db,
            proj_id,
            wt_id,
            "check_test",
            "abc123def456",
            "check passed",
            "",
            0,
            1.23,
            "test-machine",
        )

        # Retrieve the cache entry
        entry = get_cache_entry(db, proj_id, wt_id, "check_test", "abc123def456")

        assert entry is not None
        assert entry["stdout"] == "check passed"
        assert entry["stderr"] == ""
        assert entry["exit_code"] == 0
        assert entry["execution_time"] == 1.23

    def test_cache_entry_update(self):
        """Test updating an existing cache entry."""
        db = Database()
        db.init_schema()

        proj_id = db.insert_and_get_id("projects", name=self._unique_name("test-project"), description="Test")
        wt_id = db.insert_and_get_id("worktrees", project_id=proj_id, name="main")

        from projector.cache import get_cache_entry, save_cache_entry

        # Save initial entry
        save_cache_entry(db, proj_id, wt_id, "check_test", "abc123", "first run", "", 0, 1.0, "machine1")

        # Update the same entry
        save_cache_entry(
            db,
            proj_id,
            wt_id,
            "check_test",
            "abc123",
            "second run",
            "error output",
            1,
            2.0,
            "machine2",
        )

        # Verify it's updated, not duplicated
        entry = get_cache_entry(db, proj_id, wt_id, "check_test", "abc123")
        assert entry["stdout"] == "second run"
        assert entry["stderr"] == "error output"
        assert entry["exit_code"] == 1
        assert entry["execution_time"] == 2.0

        # Verify only one entry exists
        cursor = db.connect().cursor()
        query = (
            "SELECT COUNT(*) FROM command_cache "
            "WHERE project_id = ? AND worktree_id = ? AND command = ? AND files_hash = ?"
        )
        cursor.execute(query, (proj_id, wt_id, "check_test", "abc123"))
        count = cursor.fetchone()[0]
        assert count == 1

    def test_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        db = Database()
        db.init_schema()

        proj_id = db.insert_and_get_id("projects", name=self._unique_name("test-project"), description="Test")
        wt_id = db.insert_and_get_id("worktrees", project_id=proj_id, name="main")

        from projector.cache import get_cache_entry

        # Try to get non-existent entry
        entry = get_cache_entry(db, proj_id, wt_id, "check_nonexistent", "abc123")
        assert entry is None

    def test_cache_different_hashes_are_separate(self):
        """Test that different file hashes result in separate cache entries."""
        db = Database()
        db.init_schema()

        proj_id = db.insert_and_get_id("projects", name=self._unique_name("test-project"), description="Test")
        wt_id = db.insert_and_get_id("worktrees", project_id=proj_id, name="main")

        from projector.cache import get_cache_entry, save_cache_entry

        # Save entry for hash1
        save_cache_entry(db, proj_id, wt_id, "check_test", "hash1", "output1", "", 0, 1.0, "m1")

        # Save entry for hash2
        save_cache_entry(db, proj_id, wt_id, "check_test", "hash2", "output2", "", 0, 1.0, "m1")

        # Verify they are separate
        entry1 = get_cache_entry(db, proj_id, wt_id, "check_test", "hash1")
        entry2 = get_cache_entry(db, proj_id, wt_id, "check_test", "hash2")

        assert entry1 is not None
        assert entry2 is not None
        assert entry1["stdout"] == "output1"
        assert entry2["stdout"] == "output2"

    def test_clear_cache_entry(self):
        """Test clearing cache entries for a command."""
        db = Database()
        db.init_schema()

        proj_id = db.insert_and_get_id("projects", name=self._unique_name("test-project"), description="Test")
        wt_id = db.insert_and_get_id("worktrees", project_id=proj_id, name="main")

        from projector.cache import clear_cache_entry, get_cache_entry, save_cache_entry

        # Save two entries
        save_cache_entry(db, proj_id, wt_id, "check_test", "hash1", "output1", "", 0, 1.0, "m1")
        save_cache_entry(db, proj_id, wt_id, "check_test", "hash2", "output2", "", 0, 1.0, "m1")

        # Verify they exist
        assert get_cache_entry(db, proj_id, wt_id, "check_test", "hash1") is not None
        assert get_cache_entry(db, proj_id, wt_id, "check_test", "hash2") is not None

        # Clear all entries for this command
        clear_cache_entry(db, proj_id, wt_id, "check_test")

        # Verify they're gone
        assert get_cache_entry(db, proj_id, wt_id, "check_test", "hash1") is None
        assert get_cache_entry(db, proj_id, wt_id, "check_test", "hash2") is None

    def test_cache_different_projects_isolated(self):
        """Test that cache is isolated between projects."""
        db = Database()
        db.init_schema()

        proj1_id = db.insert_and_get_id("projects", name=self._unique_name("project1"), description="Test")
        proj2_id = db.insert_and_get_id("projects", name=self._unique_name("project2"), description="Test")

        wt1_id = db.insert_and_get_id("worktrees", project_id=proj1_id, name="main")
        wt2_id = db.insert_and_get_id("worktrees", project_id=proj2_id, name="main")

        from projector.cache import get_cache_entry, save_cache_entry

        # Save entry for project 1
        save_cache_entry(db, proj1_id, wt1_id, "check_test", "hash1", "proj1", "", 0, 1.0, "m1")

        # Save entry for project 2
        save_cache_entry(db, proj2_id, wt2_id, "check_test", "hash1", "proj2", "", 0, 1.0, "m1")

        # Verify they are separate
        entry1 = get_cache_entry(db, proj1_id, wt1_id, "check_test", "hash1")
        entry2 = get_cache_entry(db, proj2_id, wt2_id, "check_test", "hash1")

        assert entry1["stdout"] == "proj1"
        assert entry2["stdout"] == "proj2"

    def test_cache_entry_with_special_characters(self):
        """Test cache with special characters in output."""
        db = Database()
        db.init_schema()

        proj_id = db.insert_and_get_id("projects", name=self._unique_name("test-project"), description="Test")
        wt_id = db.insert_and_get_id("worktrees", project_id=proj_id, name="main")

        from projector.cache import get_cache_entry, save_cache_entry

        special_output = "Test with special chars: ✓ ✗ → ← ™ © ® 中文"
        special_error = "Error: 日本語 한국어 Русский"

        save_cache_entry(
            db,
            proj_id,
            wt_id,
            "check_test",
            "hash1",
            special_output,
            special_error,
            0,
            1.0,
            "machine",
        )

        entry = get_cache_entry(db, proj_id, wt_id, "check_test", "hash1")
        assert entry["stdout"] == special_output
        assert entry["stderr"] == special_error
