# Projector Self-Monitoring Setup

This directory contains a complete Projector setup for monitoring the Projector project itself.

## What's Included

### Configuration
- **projector-self-config.yaml** - Complete project configuration with 5 projects and 40+ checks

### Check Commands
- **bin/check_*** - 17 check implementations for comprehensive project health monitoring

## Projects Monitored

### 1. projector-core
Tracks the core Projector implementation and utilities.

**Checks:**
- `build` - Build Python package with UV (mandatory)
- `tests` - Run unit tests with pytest
- `lint` - Lint Python code (pylint, black, isort)
- `type-check` - Static type checking with mypy
- `security` - Security scanning (bandit, safety)
- `imports` - Verify all imports are resolvable
- `coverage` - Check test coverage >= 80%
- `cli-help` - Verify all CLI commands have help text
- `samples-valid` - Validate all YAML sample files (mandatory)
- `docs` - Build and validate documentation
- `database-schema` - Verify database schema integrity
- `git-integration` - Test git integration functions (mandatory)

### 2. projector-cli
Tracks CLI commands and user interface.

**Checks:**
- `cli-syntax` - Verify CLI syntax and argument parsing (mandatory)
- `cli-commands` - Test all CLI commands execute (mandatory)
- `help-text` - Verify help text for all commands
- `error-handling` - Test error handling and edge cases
- `output-formats` - Test JSON, CSV, and Table output formats (mandatory)
- `rich-formatting` - Verify Rich terminal formatting

### 3. projector-docs
Tracks documentation quality.

**Checks:**
- `markdown-syntax` - Validate markdown files syntax
- `links-valid` - Check all documentation links are valid
- `samples-loadable` - Verify YAML samples are loadable (mandatory)
- `code-examples` - Validate code examples in documentation
- `readme-complete` - Verify README has all required sections
- `quickref-current` - Verify quick reference matches CLI

### 4. projector-database
Tracks database layer and schema.

**Checks:**
- `schema-create` - Test database schema creation (mandatory)
- `schema-migrate` - Test database migrations
- `queries-valid` - Verify all SQL queries are valid (mandatory)
- `transactions` - Test transaction handling
- `concurrent-access` - Test concurrent database access
- `data-integrity` - Verify data constraints and integrity

### 5. projector-integration
Tracks integration tests and workflows.

**Checks:**
- `full-workflow` - Test complete workflow (mandatory)
- `yaml-loading` - Test YAML configuration loading (mandatory)
- `check-execution` - Test check execution and result recording (mandatory)
- `mandatory-enforcement` - Test mandatory check enforcement (mandatory)
- `json-storage` - Test JSON detail storage in database (mandatory)
- `report-generation` - Test report generation in all formats
- `cross-machine-sync` - Test cross-machine database sync
- `conflict-resolution` - Test conflict detection and resolution

## Quick Start

### 1. Load Configuration
```bash
# Load the Projector self-monitoring configuration
uv run proj configure --file projector-self-config.yaml
```

### 2. Run All Checks
```bash
# Add bin directory to PATH
export PATH="$PWD/bin:$PATH"

# Run all checks for the core project
uv run proj run projector-core main

# Run checks for specific projects
uv run proj run projector-cli main
uv run proj run projector-docs main
uv run proj run projector-database main
uv run proj run projector-integration main
```

### 3. View Results
```bash
# Table format
uv run proj report projector-core

# JSON format (detailed)
uv run proj report projector-core --format json

# CSV format (export)
uv run proj report projector-core --format csv
```

### 4. Run Specific Checks
```bash
# Run only the build check
uv run proj run projector-core main --check build

# Run only CLI syntax check
uv run proj run projector-cli main --check cli-syntax
```

## Check Implementations

### Core Checks (projector-core)

**check_build**
- Runs `uv sync` to build the package
- Mandatory for ensuring dependencies are available

**check_tests**
- Runs pytest if available
- Gracefully handles missing test directory

**check_lint**
- Runs black for formatting
- Runs isort for import ordering
- Handles missing tools gracefully

**check_type-check**
- Runs mypy on projector/ directory
- Ignores missing imports in external packages

**check_security**
- Runs bandit for code security
- Runs safety for dependency vulnerabilities
- Continues if tools not available

**check_samples-valid**
- Validates all YAML sample files
- Checks syntax and structure
- Uses PyYAML for validation

**check_git-integration**
- Tests git SHA retrieval
- Tests commit message access
- Tests author detection
- Tests git status checking

### CLI Checks (projector-cli)

**check_cli-syntax**
- Tests main help command
- Tests all subcommand help text
- Verifies argument parsing

**check_cli-commands**
- Tests init command
- Tests project management
- Tests worktree management
- Tests check management
- Uses temporary database for isolation

**check_output-formats**
- Tests table format output
- Tests JSON format parsing
- Tests CSV format generation
- Verifies output is valid

### Integration Checks (projector-integration)

**check_full-workflow**
- Initialize → Configure → Report workflow
- Tests end-to-end functionality

**check_yaml-loading**
- Tests loading multiple sample files
- Verifies configuration idempotency

**check_check-execution**
- Tests running checks
- Verifies results are recorded
- Tests report contains results

**check_mandatory-enforcement**
- Tests mandatory passing check succeeds
- Tests mandatory failing check exits with error

**check_json-storage**
- Verifies JSON details are stored
- Checks all required fields present
- Tests status, exit_code, time, git_status, machine

**check_report-generation**
- Tests all three output formats
- Verifies report content is valid

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Projector Health Checks
  run: |
    export PATH="$PWD/bin:$PATH"
    uv run proj run projector-core main
    uv run proj run projector-cli main
    uv run proj run projector-integration main
```

### GitLab CI Example
```yaml
projector-checks:
  script:
    - export PATH="$PWD/bin:$PATH"
    - uv run proj run projector-core main
    - uv run proj run projector-cli main
    - uv run proj run projector-integration main
```

## Database Location

By default, Projector stores the database at:
```bash
~/.projector/projector.db
```

To use a temporary database for testing:
```bash
export PROJECTOR_DB=/tmp/projector-test.db
uv run proj run projector-core main
```

## Viewing Execution Details

The JSON storage includes detailed execution information:

```bash
uv run proj report projector-core --format json | jq '.[] | .details'
```

Output:
```json
{
  "status": "pass",
  "exit_code": 0,
  "time": 0.45,
  "git_status": "modified",
  "machine": "hostname"
}
```

## Troubleshooting

### Check Not Found
```bash
# Verify check script exists and is executable
ls -la bin/check_<name>

# Add bin to PATH
export PATH="$PWD/bin:$PATH"
which check_<name>
```

### Database Issues
```bash
# Reset database
rm ~/.projector/projector.db
uv run proj init
uv run proj configure --file projector-self-config.yaml
```

### Dependency Issues
```bash
# Reinstall dependencies
uv sync

# Verify installation
uv run proj --help
```

## Best Practices

1. **Run regularly** - Add to CI/CD for continuous monitoring
2. **Monitor trends** - Track results over time
3. **Mandatory checks** - Keep only critical checks mandatory
4. **Fast checks** - Keep check execution time reasonable
5. **Clear descriptions** - Document what each check verifies

## Extending the Setup

### Add New Checks
1. Create check script in `bin/check_<name>`
2. Add check to `projector-self-config.yaml`
3. Make script executable: `chmod +x bin/check_<name>`
4. Run with `proj run`

### Add New Projects
1. Add project to `projector-self-config.yaml`
2. Load with `proj configure --file projector-self-config.yaml`
3. Create check scripts for new checks
4. Run with `proj run <project> main`

## Example Output

### Table Report
```
                                     Report
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Worktree ┃ SHA     ┃ Check    ┃ Status ┃ Comment          ┃ Logged At      ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ main     │ 3b11f18 │ build    │ ✓ pass │ {"status":       │ 2026-03-11    │
│          │         │          │        │ "pass",          │ 06:32:47      │
│          │         │          │        │ "exit_code": 0}  │               │
└──────────┴─────────┴──────────┴────────┴──────────────────┴────────────────┘
```

### JSON Report
```json
[
  {
    "worktree": "main",
    "sha": "3b11f18",
    "check": "build",
    "status": "pass",
    "details": {
      "status": "pass",
      "exit_code": 0,
      "time": 0.45,
      "git_status": "modified",
      "machine": "hostname"
    },
    "logged_at": "2026-03-11 06:32:47"
  }
]
```

## File Structure

```
projector/
├── projector-self-config.yaml      # Configuration file
├── PROJECTOR_SELF_SETUP.md        # This file
└── bin/
    ├── check_build                 # Core checks
    ├── check_tests
    ├── check_lint
    ├── check_type-check
    ├── check_security
    ├── check_samples-valid
    ├── check_git-integration
    ├── check_cli-syntax            # CLI checks
    ├── check_cli-commands
    ├── check_output-formats
    ├── check_samples-loadable      # Doc checks
    ├── check_yaml-loading          # Integration checks
    ├── check_full-workflow
    ├── check_check-execution
    ├── check_mandatory-enforcement
    ├── check_json-storage
    └── check_report-generation
```

## Next Steps

1. Load the configuration: `uv run proj configure --file projector-self-config.yaml`
2. Add bin/ to PATH: `export PATH="$PWD/bin:$PATH"`
3. Run checks: `uv run proj run projector-core main`
4. View results: `uv run proj report projector-core --format json`
5. Integrate into CI/CD pipeline
6. Monitor trends and trends over time

## Support

For issues or questions:
- Check individual check script comments
- Review QUICKREF.md for command syntax
- See samples/IMPLEMENTATION_GUIDE.md for check creation details
