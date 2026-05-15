# Decision 1: Command Execution Caching Architecture

**Date**: 2026-05-15
**Status**: Approved
**Impact**: PROJ-1, PROJ-1.1

## Problem Statement

Executing the same command multiple times in a git repository with unchanged files causes redundant work. Users need a way to avoid re-running commands when nothing has changed, while ensuring cache invalidation when files are modified.

## Solution Overview

Implement a centralized caching mechanism in `projector/cache.py` that:
1. Computes a deterministic hash based on git state (HEAD SHA + modified files)
2. Stores execution results keyed by this hash
3. Supports file filtering via `.projectorignore`
4. Provides cache bypass via `-B` flag
5. Works across both `runner` and `check` commands

## Architecture

### Core Module: `projector/cache.py`

**Functions:**
- `get_git_changed_files_hash()` - Computes cache key based on git state
- `get_cache_entry()` - Retrieves cached result from database
- `save_cache_entry()` - Stores execution result in cache
- `clear_cache_entry()` - Removes cache entries
- `_read_projector_ignore()` - Reads `.projector/.projectorignore` patterns
- `_is_projector_ignored()` - Checks if file matches ignore patterns

### Cache Key Computation

The cache key is a SHA256 hash combining:

1. **HEAD Commit SHA** - Identifies the current commit
2. **Modified Files** - Content hash of all changed/untracked files
3. **File Filtering** - Respect `.projector/.projectorignore` patterns

**Algorithm:**
```
if working_directory is clean:
    cache_key = HEAD_SHA
else:
    cache_key = SHA256(HEAD_SHA + sorted_files_with_content)
```

**Benefits:**
- Same command across commits with identical file changes returns cached result
- Automatic invalidation when files are modified
- Respects user-defined ignore patterns
- Deterministic and reproducible

### Integration Points

#### Runner Command (`projector/commands/runner.py`)
- Uses cache for arbitrary command execution
- `-B` flag bypasses cache
- Caches: stdout, stderr, exit_code, execution_time
- Database isolation by project and worktree

#### Check Command (`projector/commands/run.py`)
- Extended caching to check execution
- Cache key: `check_<check_name>`
- Supports same `-B` bypass flag
- Integrated with existing check execution flow

### Database Schema

**Table: `command_cache`**
```sql
CREATE TABLE command_cache (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    worktree_id INTEGER NOT NULL,
    command TEXT NOT NULL,
    files_hash TEXT NOT NULL,
    stdout TEXT,
    stderr TEXT,
    exit_code INTEGER,
    execution_time REAL,
    cached_at DATETIME,
    machine_id TEXT,
    UNIQUE(project_id, worktree_id, command, files_hash),
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(worktree_id) REFERENCES worktrees(id)
)
```

**Composite Key:** (project_id, worktree_id, command, files_hash)
- Ensures cache isolation between projects and worktrees
- Allows multiple cache entries for same command with different file hashes

## `.projectorignore` Support

**File Location:** `.projector/.projectorignore`

**Format:**
```
# Ignore patterns (one per line, # for comments)
*.log
node_modules/*
dist/*
.env
```

**Behavior:**
- Patterns use fnmatch glob syntax
- Ignored files don't affect cache hash computation
- Useful for build artifacts, logs, and environment-specific files
- Prevents cache invalidation on irrelevant file changes

## Testing Strategy

### Unit Tests (15 tests total)

**test_cache_projectorignore.py (8 tests)**
- Pattern file reading and parsing
- Comment handling and empty lines
- Exact pattern matching
- Glob pattern matching
- Basename matching
- Multiple patterns

**test_check_caching.py (7 tests)**
- Cache entry creation and retrieval
- Entry updates (upsert behavior)
- Cache misses return None
- Different hashes stored separately
- Cache clearing functionality
- Project/worktree isolation
- Special character handling

### Test Isolation
- Uses UUID-based unique names per test instance
- Temporary directories for test isolation
- Prevents database constraint violations across test runs

### Integration Tests (E2E)
- All 45 E2E tests passing
- Tests verify overall system behavior with caching enabled
- Cache bypass functionality tested through `-B` flag

## Usage Examples

### Runner Command
```bash
# First run - executes and caches
proj runner sleep 10  # takes 10 seconds

# Second run - returns cached result
proj runner sleep 10  # takes 0 seconds

# Bypass cache
proj runner -B sleep 10  # takes 10 seconds again
```

### Check Command
```bash
# First run - executes and caches check
proj check build  # executes build check

# Subsequent runs with same git state - returns cached result
proj check build  # returns cached result

# Force re-execution
proj run -B  # forces check execution
```

### With .projectorignore
```bash
# .projector/.projectorignore
dist/*
*.log
node_modules/*
```

Cache remains valid even if these files change.

## Trade-offs and Decisions

### Why SHA256 for git state?
- Deterministic and reproducible across machines
- Efficiently detects file changes
- Works across commits with identical modifications

### Why composite key in database?
- Enables project isolation for multi-tenant scenarios
- Allows cache reuse across different worktrees
- Supports multiple independent command histories

### Why machine_id in cache?
- Future enhancement for distributed cache analysis
- Helps debug cache behavior across different machines
- No current functional impact

### Why .projectorignore instead of .gitignore?
- Git ignores are for version control, not build artifacts
- Projector ignores are specific to cache computation
- Keeps concerns separated and explicit
- Users can safely commit .projectorignore

## Future Enhancements

1. **Cache Expiration** - Time-based cache invalidation
2. **Cache Statistics** - Track hit/miss ratios
3. **Distributed Cache** - Share cache across team members
4. **Cache Compression** - Reduce database size for large outputs
5. **Selective Caching** - Per-command cache control

## Implementation Status

- ✅ Core caching mechanism implemented
- ✅ Integration with runner command
- ✅ Integration with check command
- ✅ .projectorignore support
- ✅ Comprehensive test coverage (15 unit tests)
- ✅ All 45 E2E tests passing
- ✅ Linting clean (ruff)
- ✅ Documentation complete

## Related Tasks

- PROJ-1: Cache the execution result
- PROJ-1.1: Caching both for runner and for checks
