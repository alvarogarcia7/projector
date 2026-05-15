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

## Implementation Details

### Cache Key Computation Flow

**File**: `projector/cache.py:get_git_changed_files_hash()`

```python
def get_git_changed_files_hash() -> Optional[str]:
    # 1. Get HEAD commit SHA
    head_sha = subprocess.run(["git", "rev-parse", "HEAD"], ...).stdout.strip()

    # 2. Check if working directory is modified
    status = subprocess.run(["git", "status", "--porcelain"], ...).stdout.strip()

    # 3a. Clean working directory
    if not status:
        return head_sha  # Cache key = HEAD SHA only

    # 3b. Modified files present
    # Get list of changed/untracked files
    changed_files = subprocess.run(
        ["git", "ls-files", "-m", "-o", "--exclude-standard"],
        ...
    ).stdout.strip().split("\n")

    # Filter by .projectorignore patterns
    ignore_patterns = _read_projector_ignore()
    changed_files = [f for f in changed_files
                     if not _is_projector_ignored(f, ignore_patterns)]

    # Compute hash
    hasher = hashlib.sha256()
    hasher.update(head_sha.encode())

    for filepath in sorted(changed_files):
        with open(filepath, "rb") as f:
            hasher.update(filepath.encode())
            hasher.update(f.read())

    return hasher.hexdigest()
```

### Cache Entry Operations

**Retrieve cached result** (`get_cache_entry`):
```python
def get_cache_entry(db, project_id: int, worktree_id: int,
                   command: str, files_hash: str) -> Optional[dict]:
    return db.fetchone(
        """SELECT stdout, stderr, exit_code, execution_time, cached_at
           FROM command_cache
           WHERE project_id = ? AND worktree_id = ?
                 AND command = ? AND files_hash = ?
           ORDER BY cached_at DESC LIMIT 1""",
        (project_id, worktree_id, command, files_hash)
    )
```

**Save cached result** (`save_cache_entry`):
```python
def save_cache_entry(db, project_id: int, worktree_id: int, command: str,
                    files_hash: str, stdout: str, stderr: str,
                    exit_code: int, execution_time: float, machine_id: str):
    # Check if entry exists
    existing = db.fetchone(
        "SELECT id FROM command_cache WHERE project_id = ? AND worktree_id = ? "
        "AND command = ? AND files_hash = ?",
        (project_id, worktree_id, command, files_hash)
    )

    if existing:
        # Update existing entry
        db.execute(
            "UPDATE command_cache SET stdout = ?, stderr = ?, exit_code = ?, "
            "execution_time = ?, cached_at = ?, machine_id = ? WHERE id = ?",
            (stdout, stderr, exit_code, execution_time, datetime.now(),
             machine_id, existing["id"])
        )
    else:
        # Insert new entry
        db.insert_and_get_id(
            "command_cache",
            project_id=project_id, worktree_id=worktree_id, command=command,
            files_hash=files_hash, stdout=stdout, stderr=stderr,
            exit_code=exit_code, execution_time=execution_time,
            cached_at=datetime.now(), machine_id=machine_id
        )
    db.commit()
```

### Runner Command Integration

**File**: `projector/commands/runner.py` (lines 91-163)

```python
# 1. Compute cache key
files_hash = get_git_changed_files_hash()

# 2. Check cache (unless -B flag set)
if not bypass_cache and files_hash:
    cache_entry = get_cache_entry(db, proj["id"], wt["id"],
                                  command, files_hash)
    if cache_entry:
        # Return cached result
        sys.stdout.write(cache_entry["stdout"])
        sys.stderr.write(cache_entry["stderr"])
        raise typer.Exit(cache_entry["exit_code"])

# 3. Execute command
result = subprocess.run(command, shell=True, capture_output=True, text=True)

# 4. Save result to cache
if files_hash:
    save_cache_entry(db, proj["id"], wt["id"], command, files_hash,
                    result.stdout, result.stderr, result.returncode,
                    elapsed, socket.gethostname())
```

### Check Command Integration

**File**: `projector/commands/run.py` (lines 49-370)

```python
# 1. Compute cache key once per run
files_hash = get_git_changed_files_hash()

# 2. For each check
cache_key = f"check_{check_name}"
if not bypass_cache and files_hash:
    cache_entry = get_cache_entry(db, proj["id"], wt["id"],
                                  cache_key, files_hash)
    if cache_entry:
        # Use cached result
        continue

# 3. Execute check and cache result
save_cache_entry(db, proj["id"], wt["id"], cache_key, files_hash,
                stdout, stderr, exit_code, elapsed, socket.gethostname())
```

### `.projectorignore` Implementation

**File**: `projector/cache.py` (lines 14-28)

```python
def _read_projector_ignore() -> list:
    """Read patterns from .projector/.projectorignore"""
    ignore_path = Path.cwd() / ".projector" / ".projectorignore"
    if not ignore_path.exists():
        return []

    patterns = []
    with open(ignore_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):  # Skip comments and empty lines
                patterns.append(line)
    return patterns

def _is_projector_ignored(filepath: str, patterns: list) -> bool:
    """Check if filepath matches any pattern using fnmatch"""
    return any(fnmatch.fnmatch(filepath, p) or
               fnmatch.fnmatch(os.path.basename(filepath), p)
               for p in patterns)
```

## Real-World Scenarios

### Scenario 1: Unchanged Code
```bash
# At COMMIT1, run expensive command
$ proj runner npm test
# Takes 30 seconds, caches result with hash=COMMIT1_SHA

# Same commit, no changes
$ proj runner npm test
# Cache hit! Returns result instantly
```

### Scenario 2: File Modifications
```bash
# Modify src/index.js
$ proj runner npm test
# Cache miss (file changed), executes and caches with hash=SHA256(COMMIT1 + index.js)

# Fix a typo in .env (in .projectorignore)
$ proj runner npm test
# Cache hit! .env is ignored, so hash unchanged
```

### Scenario 3: Commit and Continue
```bash
# At COMMIT1 with file.js modified
$ proj runner ./build.sh
# Caches with hash=SHA256(COMMIT1 + file.js)

# Commit changes (now at COMMIT2, clean working dir)
$ proj runner ./build.sh
# Cache miss (HEAD SHA changed from COMMIT1 to COMMIT2)
# Executes again
```

## Implementation Status

- ✅ Core caching mechanism implemented (`projector/cache.py`)
- ✅ Integration with runner command (`projector/commands/runner.py`)
- ✅ Integration with check command (`projector/commands/run.py`)
- ✅ `.projectorignore` support with fnmatch patterns
- ✅ Composite database key for isolation
- ✅ Cache bypass via `-B` flag
- ✅ Comprehensive test coverage (15 unit + 45 E2E tests)
- ✅ Linting clean (ruff)
- ✅ Debug logging throughout
- ✅ Documentation in decision and verification documents

## Related Tasks

- **PROJ-1**: Cache the execution result
  - Status: Done
  - Files: `projector/cache.py`, `projector/commands/runner.py`, `projector/db.py`

- **PROJ-1.1**: Caching both for runner and for checks
  - Status: Done
  - Files: `projector/commands/run.py`, `tests/test_*.py`
  - Features: `.projectorignore` support, check command caching
