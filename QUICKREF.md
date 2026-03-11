# Projector Quick Reference

## Setup

```bash
# Initialize database
proj init                    # global ~/.projector/projector.db
proj init --local           # local .projector.db

# Create a project
proj project add my-app --description "My App" --repo /path/to/repo

# Add worktrees
proj worktree add my-app main
proj worktree add my-app feature/auth

# Define checks
proj check add my-app build --mandatory
proj check add my-app tests --mandatory
proj check add my-app lint
proj check add my-app deploy
```

## Viewing

```bash
# List projects/worktrees/checks
proj project list
proj worktree list my-app
proj check list my-app

# Show details
proj project show my-app
proj check list my-app --show-archived

# View status
proj status my-app                              # latest per worktree
proj status my-app main                         # history for worktree
proj status my-app main abc123def456            # specific commit
proj status my-app --show-archived              # include archived checks
```

## Logging

```bash
# Interactive (auto-detects git info)
proj log my-app main

# Explicit details
proj log my-app main --sha abc123 --message "Fix bug" --author "John"

# CI mode (non-interactive)
proj log my-app main \
  --sha $(git rev-parse HEAD) \
  --ci build=pass \
  --ci tests=fail:"coverage < 80%" \
  --ci lint=warn:"2 issues"
```

## Reporting

```bash
# Show in table
proj report my-app

# Export to CSV
proj report my-app --format csv > report.csv

# Export to JSON
proj report my-app --format json > report.json

# Filter
proj report my-app --worktree main --since 2024-01-01 --format json
```

## Managing Checks

```bash
# Archive a check (soft delete)
proj check archive my-app old-check

# Restore archived check
proj check restore my-app old-check

# List including archived
proj check list my-app --show-archived
```

## Sync

```bash
# Export for sharing
proj sync export --output ~/Dropbox/projector.db

# Import from another machine
proj sync import ~/Dropbox/projector.db

# Or via SSH
scp user@machineA:~/.projector/projector.db /tmp/remote.db
proj sync import /tmp/remote.db
```

## Cleanup

```bash
# Remove project (deletes all data)
proj project remove my-app --yes

# Remove worktree (deletes commits & results)
proj worktree remove my-app main --yes
```

## Check Statuses

- **pass** ✓ — Check passed
- **fail** ✗ — Check failed
- **warn** ⚠ — Check passed with warnings
- **skip** – — Check skipped

## Database Files

- **Global**: `~/.projector/projector.db` (all projects)
- **Local**: `.projector.db` (per-repo, takes precedence)

## Tips

### Auto-detect in CI

```bash
# Works in git repos
cd /path/to/repo
proj log my-app main              # auto SHA, message, author

# Or explicit
proj log my-app main --sha $SHA
```

### Mandatory Checks

- Exit code 1 if any mandatory check fails in CI mode
- Interactive mode prompts to confirm skipping mandatory checks

### Name-Based Merge

- Sync matches by name: project → worktree → check → commit SHA
- Resilient to different database IDs on different machines
- Conflicts logged to `conflict_log` table

### Table View Legend

```
project: my-app

┌──────────┬──────┬────────┬────────┐
│ worktree │ sha  │ build  │ tests  │
├──────────┼──────┼────────┼────────┤
│ main     │ a1b2 │ ✓ pass │ ✗ fail │
│ feature  │ 9f8e │ ✓ pass │ ✓ pass │
└──────────┴──────┴────────┴────────┘
```

Bold columns = mandatory checks
