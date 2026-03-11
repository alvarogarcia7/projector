# Projector Test Suite

This directory contains all tests for the Projector CLI application, including unit tests and end-to-end (E2E) tests.

## Test Files

- **`test_version.py`** — Unit tests for basic module functionality
- **`e2e_test.sh`** — Comprehensive end-to-end test suite (bash)
- **`E2E_TESTS.md`** — Detailed documentation for E2E tests

## Quick Start

### Run Unit Tests
```bash
make test
# or
uv run pytest tests -v
```

### Run End-to-End Tests
```bash
make test-e2e
# or
bash tests/e2e_test.sh
```

### Run All Checks (lint, type, unit tests)
```bash
make pre-commit
```

### Run Tests with Coverage
```bash
make coverage
```

## Test Coverage

### Unit Tests (Python)
- Module imports
- Version validation

### End-to-End Tests (Bash)

The E2E test suite (`e2e_test.sh`) covers 10 major feature areas with 45+ test cases:

1. **Database Initialization** — Creating and setting up databases
2. **Project Management** — CRUD operations on projects
3. **Worktree Management** — Adding/removing git worktrees
4. **Check Management** — Creating and managing health checks
5. **Logging Results** — Recording check results with various statuses
6. **Status Viewing** — Querying project and commit status
7. **Report Generation** — Exporting reports in multiple formats
8. **Configuration** — Managing user settings
9. **Database Sync** — Exporting and importing databases
10. **Dry-Run Mode** — Testing without side effects

## Running Tests Locally

1. **Install dependencies:**
   ```bash
   make dev
   ```

2. **Run unit tests:**
   ```bash
   make test
   ```

3. **Run E2E tests:**
   ```bash
   make test-e2e
   ```

4. **Full validation suite:**
   ```bash
   make pre-commit
   ```

## Continuous Integration

Both test suites are designed to work in CI/CD pipelines:

```bash
# GitHub Actions example
- name: Run unit tests
  run: uv run pytest tests -v

- name: Run E2E tests
  run: bash tests/e2e_test.sh
```

## Test Isolation

- **Unit tests** use pytest's isolation mechanisms
- **E2E tests** create temporary directories and clean up automatically
- No test modifies your actual Projector data

## Debugging Tests

### If unit tests fail:
```bash
uv run pytest tests -v -s  # Show output
uv run pytest tests::test_name -v  # Run specific test
```

### If E2E tests fail:
```bash
bash tests/e2e_test.sh  # Full output with details
bash -x tests/e2e_test.sh  # Debug mode (very verbose)
```

### Check projector installation:
```bash
which proj
proj --version
```

## Writing New Tests

### Adding Unit Tests
Create a new Python file in `tests/` directory:
```python
def test_new_feature():
    """Test description."""
    assert True
```

### Adding E2E Tests
Edit `e2e_test.sh` and add a new section:
```bash
log_test_start "Feature Name"

assert_success "run_proj command-name args" \
    "Description of what should succeed"

echo ""
```

See [E2E_TESTS.md](E2E_TESTS.md) for detailed guidelines.

## Test Results

### Successful Run
```
✓ All tests passed!
```

### Failed Tests
```
✗ Some tests failed
```

Exit codes:
- `0` — All tests passed
- `1` — One or more tests failed

## Dependencies

- **Python:** pytest, typer (for running application)
- **Bash:** Standard utilities (grep, echo, etc.)
- **Runtime:** projector CLI installed and in PATH
