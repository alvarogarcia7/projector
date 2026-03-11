# Projector

A CLI tool for tracking software project health across multiple machines, worktrees, and commits. Built in Python, stored in SQLite.

## Installation

```bash
git clone https://github.com/you/projector
cd projector
pip install -e .
```

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
