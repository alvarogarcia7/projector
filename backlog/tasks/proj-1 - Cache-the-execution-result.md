---
id: PROJ-1
title: Cache the execution result
status: Done
assignee: []
created_date: '2026-03-25 10:32'
completed_date: '2026-03-25'
labels: []
dependencies: []
---

## Description

Implement command execution caching for the `runner` command that caches results based on git repository state. When running the same command without changing files, cached results should be returned instantly.

## Implementation Details

### New Files Created:
- **`projector/cache.py`** - Core caching functionality with SHA256-based git state hashing
- **`projector/commands/runner.py`** - New runner command with caching support

### Modified Files:
- **`projector/db.py`** - Added `command_cache` table schema
- **`projector/models.py`** - Added `CommandCache` dataclass
- **`projector/cli.py`** - Integrated runner command with `-B` flag
- **`README.md`** - Added comprehensive documentation

### Features:
- Caches command stdout, stderr, exit code, and execution time
- Uses SHA256 hash of git HEAD + modified files as cache key
- Automatic cache invalidation on file changes or new commits
- `-B` flag to bypass cache and force re-execution
- Auto-detects project and worktree from git state

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementation completed successfully. The runner command now supports intelligent caching:

```bash
# Setup
uv run python3 -m projector.cli project add projector
uv run python3 -m projector.cli worktree add projector eW688AmPx6UdoD4VCa7Fe

# First run - executes and caches
uv run python3 -m projector.cli runner -p projector -w eW688AmPx6UdoD4VCa7Fe sleep 10 # takes 10 seconds

# Second run - returns cached result
uv run python3 -m projector.cli runner -p projector -w eW688AmPx6UdoD4VCa7Fe sleep 10 # takes 0 seconds

# Bypass cache - forces re-execution
uv run python3 -m projector.cli runner -p projector -w eW688AmPx6UdoD4VCa7Fe -B sleep 10 # takes 10 seconds again
```

All tests pass, linting clean, documentation added to README.md.
<!-- SECTION:FINAL_SUMMARY:END -->

## Validation

- ✅ Linting: `uv run ruff check projector tests` - All checks passed
- ✅ Tests: `uv run pytest tests -v` - 2/2 tests passed
- ✅ CLI Integration: `proj runner --help` shows `-B` flag
- ✅ Documentation: README.md updated with examples and usage
