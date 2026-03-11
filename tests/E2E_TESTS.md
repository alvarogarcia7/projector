# End-to-End Tests for Projector

This directory contains end-to-end (E2E) tests for the Projector CLI application.

## Overview

The `e2e_test.sh` script provides comprehensive testing of the main features and workflows of the Projector application. It verifies that all major commands work correctly end-to-end without relying on specific internal implementation details.

## Test Coverage

The E2E test suite covers the following major features:

### 1. **Database Initialization**
   - Verifies database creation with `proj init --local`
   - Checks that `.projector.db` file is created

### 2. **Project Management**
   - Creating new projects with `proj project add`
   - Listing all projects with `proj project list`
   - Viewing project details with `proj project show`
   - Removing projects with `proj project remove`

### 3. **Worktree Management**
   - Adding worktrees with `proj worktree add`
   - Listing worktrees with `proj worktree list`
   - Removing worktrees with `proj worktree remove`

### 4. **Check Management**
   - Adding checks (mandatory and optional) with `proj check add`
   - Listing checks with `proj check list`
   - Archiving checks with `proj check archive`
   - Restoring archived checks with `proj check restore`
   - Viewing archived checks with `--show-archived` flag

### 5. **Logging Check Results**
   - Recording check results in CI mode with `proj log`
   - Supporting multiple result statuses: pass, fail, warn, skip
   - Including optional messages with results

### 6. **Status Checking**
   - Viewing overall project status with `proj status`
   - Viewing worktree-specific status
   - Viewing commit-specific status

### 7. **Report Generation**
   - Generating reports in multiple formats (table, CSV, JSON)
   - Filtering reports by worktree
   - Filtering reports by date range

### 8. **Configuration Management**
   - Setting default project with `proj config set`
   - Retrieving configuration with `proj config get`
   - Clearing configuration with `proj config clear`

### 9. **Database Sync**
   - Exporting database with `proj sync export`
   - Verifying exported database file creation

### 10. **Dry-Run Mode**
   - Testing `proj run` command in dry-run mode

## Running the Tests

### Prerequisites

1. Install Projector:
```bash
uv pip install -e .
# or
pip install -e .
```

2. Ensure the `proj` command is available in your PATH:
```bash
which proj  # Should return the path to projector executable
```

### Run All Tests

```bash
bash tests/e2e_test.sh
```

### Expected Output

The test script will:
- Display a header showing the test suite name
- Run each test and report pass/fail status with color coding
- Display a summary at the end with total tests passed/failed
- Exit with code 0 if all tests pass, or 1 if any tests fail

Example output:
```
===============================================
Projector End-to-End Test Suite
===============================================
Test directory: /tmp/tmp.xyz123

[TEST] Database Initialization
✓ Initialize local database
✓ Database file created locally

[TEST] Project Management
✓ Add project 'test-app'
✓ Add project 'backend-api'
✓ List projects contains 'test-app'
...

===============================================
Test Summary
===============================================
Passed: 45
Failed: 0
Total:  45

✓ All tests passed!
```

## Test Organization

Each test section covers a logical grouping of functionality:
- Tests are isolated within sections
- A temporary directory is created for all test data
- The database is local to the test environment (`.projector.db`)
- All test artifacts are cleaned up after the suite completes

## Assertion Functions

The test script provides helper functions for common assertions:

- `assert_success "command" "description"` — Asserts a command succeeds
- `assert_failure "command" "description"` — Asserts a command fails
- `assert_output_contains "command" "text" "description"` — Asserts output contains specific text

## Color Coding

Test output uses color codes for clarity:
- 🔵 `[TEST]` — Blue, marks start of test section
- ✓ Green — Test passed
- ✗ Red — Test failed
- ⚠ Yellow — Warning

## Notes

### Isolation

The test suite creates an isolated environment with:
- Temporary directory for test data
- Custom `XDG_CONFIG_HOME` and `XDG_DATA_HOME`
- Local database file (`.projector.db`)

This prevents tests from interfering with your actual Projector data.

### Git SHA Values

Since the E2E tests don't operate within actual git repositories (to maintain isolation), dummy Git SHA values are used for testing the logging functionality. In production, these would be actual commit SHAs.

### Dry-Run Mode

The `proj run` command is tested in dry-run mode to prevent actual command execution in the test environment.

## Troubleshooting

### Tests fail: "projector CLI not found in PATH"

Ensure Projector is installed:
```bash
uv pip install -e .
which proj
```

### Tests fail: "command failed"

Run individual commands manually to debug:
```bash
proj init --local
proj project add test-app
```

### Database already exists

The test suite creates a fresh isolated environment. If tests are failing due to database issues, ensure no stale processes are holding locks on the test database.

## Extending the Tests

To add new tests:

1. Create a new `log_test_start` section
2. Use helper functions: `assert_success`, `assert_failure`, `assert_output_contains`
3. Update the test count in the summary
4. Run the full suite to ensure your tests work

Example:
```bash
# ==============================================================================
# TEST 11: New Feature
# ==============================================================================
log_test_start "New Feature"

assert_success "run_proj new-command arg" \
    "New command description"

echo ""
```

## CI/CD Integration

To run in CI/CD pipelines:

```bash
# In your GitHub Actions, GitLab CI, etc.
bash tests/e2e_test.sh
```

The script will exit with:
- `0` if all tests pass
- `1` if any tests fail
