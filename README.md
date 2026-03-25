# Projector

A CLI tool for tracking software project health across multiple machines, worktrees, and commits. Built in Python, stored in SQLite.

## Installation

### Using UV (Recommended)

```bash
git clone https://github.com/you/projector
cd projector

# Install UV if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install projector
uv pip install -e .
```

### Using pip

```bash
git clone https://github.com/you/projector
cd projector
pip install -e .
```

See [INSTALLATION.md](INSTALLATION.md) for more options.

## Quick Start

### Initialize Database

```bash
# Global database (recommended)
proj init

# Or local per-repo database
proj init --local
```

### Set Up a Project

```bash
# Create a project
proj project add my-api --description "Backend REST API" --repo /path/to/repo

# Add worktrees
proj worktree add my-api main
proj worktree add my-api feature/auth

# Define checks
proj check add my-api build --mandatory
proj check add my-api tests --mandatory
proj check add my-api lint
proj check add my-api deploy
```

### Log Commit Results

```bash
# Interactive mode (auto-detects git info if in a repo)
cd /path/to/repo
git checkout main
proj log my-api main

# Or provide details explicitly
proj log my-api main \
  --sha abc123def456 \
  --message "Fixed authentication" \
  --author "John Doe"

# CI mode (non-interactive)
proj log my-api main \
  --sha $(git rev-parse HEAD) \
  --ci build=pass \
  --ci tests=fail:"coverage dropped" \
  --ci lint=warn:"3 style issues"
```

### View Status

```bash
# Latest status for all worktrees
proj status my-api

# Full history for a worktree
proj status my-api main

# Specific commit details
proj status my-api main abc123def456
```

### Generate Reports

```bash
# Full report as table
proj report my-api

# Export as CSV
proj report my-api --format csv

# Export as JSON
proj report my-api --format json

# Filter by worktree and date
proj report my-api --worktree main --since 2024-01-01 --format json
```

### Sync Across Machines

```bash
# Export database
proj sync export --output ~/Dropbox/projector.db

# On another machine, import it
proj sync import ~/Dropbox/projector.db

# Or use SSH
scp user@machineA:~/.projector/projector.db /tmp/remote.db
proj sync import /tmp/remote.db
```

### Command Caching with Runner

The `runner` command executes arbitrary commands with intelligent caching based on git repository state. Cached results are returned instantly on subsequent runs when the git state hasn't changed.

```bash
# Set up project and worktree
uv run python3 -m projector.cli project add projector
uv run python3 -m projector.cli worktree add projector eW688AmPx6UdoD4VCa7Fe

# First run - executes the command and caches results
uv run python3 -m projector.cli runner -p projector -w eW688AmPx6UdoD4VCa7Fe sleep 10
# Takes 10 seconds

# Second run - returns cached results instantly
uv run python3 -m projector.cli runner -p projector -w eW688AmPx6UdoD4VCa7Fe sleep 10
# Takes 0 seconds (cached)

# Bypass cache - forces re-execution
uv run python3 -m projector.cli runner -p projector -w eW688AmPx6UdoD4VCa7Fe -B sleep 10
# Takes 10 seconds again (cache bypassed)
```

#### How Command Caching Works

The caching system uses SHA256 hashing to identify git repository state:

- **Clean repository**: Uses the git HEAD SHA as the cache key
- **Modified files**: Computes a hash combining HEAD SHA and contents of all modified/untracked files

The cache is automatically invalidated when:
- Any tracked file is modified
- New untracked files are added
- You commit changes (new HEAD SHA)

#### Runner Usage

```bash
proj runner [OPTIONS] COMMAND [ARGS]...

Options:
  -p, --project TEXT   Project name (or set with: proj config set PROJECT)
  -w, --worktree TEXT  Worktree name (or auto-detected from git branch)
  -B                   Bypass cache and force re-execution
```

#### Runner Examples

```bash
# Run build with caching (auto-detects project/worktree)
proj runner make build

# Run tests with caching
proj runner npm test

# Run with explicit project/worktree
proj runner -p myproject -w main pytest tests/

# Force re-execution (bypass cache)
proj runner -B make clean build
```

#### When to Use Cache Bypass (`-B`)

Use the `-B` flag when you need to:
- Force a clean rebuild
- Debug caching issues
- Run commands that depend on external state (network, time, etc.)
- Clear stale cache entries

## Concepts

- **Project**: A named software project with defined checks
- **Worktree**: A branch or git worktree within a project
- **Check**: A named metric (mandatory or optional)
- **Commit Entry**: A snapshot of all check results for a specific commit
- **Status**: pass, fail, warn, or skip

## Features

- **Check Archival**: Soft-delete checks without losing historical data
- **Mandatory Checks**: CI mode exits with error code 1 if mandatory checks fail
- **Cross-Machine Sync**: Merge databases from multiple machines with conflict resolution
- **Name-Based Merge**: Resilient merging by project/worktree/check names, not IDs
- **Interactive & CI Modes**: Flexible logging for manual and automated workflows

## Database

SQLite database stored at:
- Global: `~/.projector/projector.db`
- Local (per-repo): `.projector.db`

Local databases take precedence over global ones.

## Tech Stack

- **CLI**: [Typer](https://typer.tiangolo.com/) — Modern, typed Python CLI framework
- **Database**: SQLite (stdlib) — Zero dependencies
- **Tables**: [Rich](https://rich.readthedocs.io/) — Beautiful terminal output
- **Git Integration**: `subprocess` — No extra dependencies
