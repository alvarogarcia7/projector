"""Tests for .projectorignore support in caching mechanism."""

import tempfile
from pathlib import Path

from projector.cache import _is_projector_ignored, _read_projector_ignore


class TestProjectorIgnore:
    """Test .projectorignore file reading and pattern matching."""

    def test_read_projectorignore_file_does_not_exist(self):
        """Test reading when .projectorignore doesn't exist returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)
                patterns = _read_projector_ignore()
                assert patterns == []
            finally:
                os.chdir(original_cwd)

    def test_read_projectorignore_basic_patterns(self):
        """Test reading basic patterns from .projectorignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)

                # Create .projector directory and .projectorignore file
                projector_dir = Path.cwd() / ".projector"
                projector_dir.mkdir()

                ignore_file = projector_dir / ".projectorignore"
                ignore_file.write_text("*.log\ndist/\nnode_modules/\n")

                patterns = _read_projector_ignore()
                assert patterns == ["*.log", "dist/", "node_modules/"]
            finally:
                os.chdir(original_cwd)

    def test_read_projectorignore_with_comments(self):
        """Test that comments are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)

                projector_dir = Path.cwd() / ".projector"
                projector_dir.mkdir()

                ignore_file = projector_dir / ".projectorignore"
                ignore_file.write_text("# This is a comment\n*.log\n# Another comment\ndist/\n")

                patterns = _read_projector_ignore()
                assert patterns == ["*.log", "dist/"]
            finally:
                os.chdir(original_cwd)

    def test_read_projectorignore_with_empty_lines(self):
        """Test that empty lines are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)

                projector_dir = Path.cwd() / ".projector"
                projector_dir.mkdir()

                ignore_file = projector_dir / ".projectorignore"
                ignore_file.write_text("*.log\n\ndist/\n   \nnode_modules/\n")

                patterns = _read_projector_ignore()
                assert patterns == ["*.log", "dist/", "node_modules/"]
            finally:
                os.chdir(original_cwd)

    def test_is_projector_ignored_exact_pattern(self):
        """Test exact pattern matching."""
        patterns = ["*.log", "*.tmp"]

        assert _is_projector_ignored("debug.log", patterns)
        assert _is_projector_ignored("build.tmp", patterns)
        assert not _is_projector_ignored("README.md", patterns)

    def test_is_projector_ignored_glob_pattern(self):
        """Test glob pattern matching."""
        patterns = ["dist/*", "build/*"]

        assert _is_projector_ignored("dist/index.js", patterns)
        assert _is_projector_ignored("build/output.o", patterns)
        assert not _is_projector_ignored("src/main.py", patterns)

    def test_is_projector_ignored_basename_matching(self):
        """Test matching on basename (filename without path)."""
        patterns = ["*.log"]

        # Should match even when nested in directories
        assert _is_projector_ignored("logs/debug.log", patterns)
        assert _is_projector_ignored("nested/path/to/debug.log", patterns)
        assert not _is_projector_ignored("logs/debug.txt", patterns)

    def test_is_projector_ignored_multiple_patterns(self):
        """Test matching against multiple patterns."""
        patterns = ["*.log", "dist/*", "*.tmp", "node_modules/*"]

        test_cases = [
            ("app.log", True),
            ("dist/index.html", True),
            ("cache.tmp", True),
            ("node_modules/package/index.js", True),
            ("src/main.py", False),
            ("README.md", False),
        ]

        for filepath, should_match in test_cases:
            assert _is_projector_ignored(filepath, patterns) == should_match
