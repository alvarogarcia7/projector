#!/bin/bash

# End-to-End Test Suite for Projector
# Tests the main features of the projector CLI application

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Setup test environment
TEST_DIR=$(mktemp -d)
TEST_DB="${TEST_DIR}/test.db"
export XDG_CONFIG_HOME="${TEST_DIR}/.config"
export XDG_DATA_HOME="${TEST_DIR}/.data"

# Ensure projector is installed
if ! command -v proj &> /dev/null; then
    echo -e "${RED}✗ projector CLI not found in PATH${NC}"
    exit 1
fi

# Logging functions
log_test_start() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED+1))
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED+1))
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Cleanup function
cleanup() {
    if [[ -d "${TEST_DIR}" ]]; then
        rm -rf "${TEST_DIR}"
    fi
}

trap cleanup EXIT

# Helper function to run proj commands
run_proj() {
    proj "$@" 2>&1 || return $?
}

# Helper function to assert command succeeds
assert_success() {
    local cmd="$1"
    local description="$2"

    if eval "$cmd" > /dev/null 2>&1; then
        log_success "$description"
    else
        log_error "$description (command failed: $cmd)"
    fi
}

# Helper function to assert command fails
assert_failure() {
    local cmd="$1"
    local description="$2"

    if ! eval "$cmd" > /dev/null 2>&1; then
        log_success "$description"
    else
        log_error "$description (command succeeded unexpectedly)"
    fi
}

# Helper function to assert output contains text
assert_output_contains() {
    local cmd="$1"
    local expected="$2"
    local description="$3"

    if output=$(eval "$cmd" 2>&1) && echo "$output" | grep -q "$expected"; then
        log_success "$description"
    else
        log_error "$description (output missing: '$expected')"
    fi
}

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}Projector End-to-End Test Suite${NC}"
echo -e "${BLUE}===============================================${NC}"
echo "Test directory: ${TEST_DIR}"
echo ""

# ==============================================================================
# TEST 1: Database Initialization
# ==============================================================================
log_test_start "Database Initialization"

# Create a local database for testing
assert_success "run_proj init --local" "Initialize local database"

# Verify database file was created
if [[ -f ".projector.db" ]]; then
    log_success "Database file created locally"
else
    log_error "Database file not created"
fi

echo ""

# ==============================================================================
# TEST 2: Project Management
# ==============================================================================
log_test_start "Project Management"

# Add a project
assert_success "run_proj project add test-app --description 'Test Application' --repo /tmp/test" \
    "Add project 'test-app'"

# Add another project
assert_success "run_proj project add backend-api --description 'Backend API' --repo /tmp/backend" \
    "Add project 'backend-api'"

# List projects
assert_output_contains "run_proj project list" "test-app" \
    "List projects contains 'test-app'"

assert_output_contains "run_proj project list" "backend-api" \
    "List projects contains 'backend-api'"

# Show project details
assert_output_contains "run_proj project show test-app" "test-app" \
    "Show project displays project name"

# Remove a project (without confirmation - testing flag)
assert_success "run_proj project remove backend-api --yes" \
    "Remove project 'backend-api'"

# Verify removed project is gone
assert_failure "run_proj project show backend-api" \
    "Removed project should not exist"

echo ""

# ==============================================================================
# TEST 3: Worktree Management
# ==============================================================================
log_test_start "Worktree Management"

# Add worktrees to the project
assert_success "run_proj worktree add test-app main --path /tmp/test" \
    "Add worktree 'main' to test-app"

assert_success "run_proj worktree add test-app feature/auth --path /tmp/test" \
    "Add worktree 'feature/auth' to test-app"

assert_success "run_proj worktree add test-app develop --path /tmp/test" \
    "Add worktree 'develop' to test-app"

# List worktrees
assert_output_contains "run_proj worktree list test-app" "main" \
    "List worktrees contains 'main'"

assert_output_contains "run_proj worktree list test-app" "feature/auth" \
    "List worktrees contains 'feature/auth'"

assert_output_contains "run_proj worktree list test-app" "develop" \
    "List worktrees contains 'develop'"

# Remove a worktree
assert_success "run_proj worktree remove test-app develop --yes" \
    "Remove worktree 'develop'"

# Verify worktree is removed
assert_failure "run_proj worktree list test-app | grep develop" \
    "Removed worktree should not be listed"

echo ""

# ==============================================================================
# TEST 4: Check Management
# ==============================================================================
log_test_start "Check Management"

# Add checks to the project
assert_success "run_proj check add test-app build --description 'Build Check' --mandatory" \
    "Add mandatory check 'build'"

assert_success "run_proj check add test-app tests --description 'Unit Tests' --mandatory" \
    "Add mandatory check 'tests'"

assert_success "run_proj check add test-app lint --description 'Code Linting'" \
    "Add optional check 'lint'"

assert_success "run_proj check add test-app security --description 'Security Scan'" \
    "Add optional check 'security'"

# List checks
assert_output_contains "run_proj check list test-app" "build" \
    "List checks contains 'build'"

assert_output_contains "run_proj check list test-app" "tests" \
    "List checks contains 'tests'"

assert_output_contains "run_proj check list test-app" "lint" \
    "List checks contains 'lint'"

# Archive a check
assert_success "run_proj check archive test-app security" \
    "Archive check 'security'"

# Verify archived check is not in default list
assert_failure "run_proj check list test-app | grep security" \
    "Archived check should not appear in default list"

# Show archived checks
assert_output_contains "run_proj check list test-app --show-archived" "security" \
    "Archived checks visible with --show-archived flag"

# Restore a check
assert_success "run_proj check restore test-app security" \
    "Restore archived check 'security'"

# Verify check is restored
assert_output_contains "run_proj check list test-app" "security" \
    "Restored check appears in list"

echo ""

# ==============================================================================
# TEST 5: Logging Check Results
# ==============================================================================
log_test_start "Logging Check Results"

# Get current git commit SHA (or use a dummy one)
GIT_SHA="abc123def456ghi789jkl012mno"
GIT_MESSAGE="Test commit for e2e testing"
GIT_AUTHOR="E2E Test Bot"

# Log results with explicit values
assert_success "run_proj log test-app main \
    --sha ${GIT_SHA} \
    --message '${GIT_MESSAGE}' \
    --author '${GIT_AUTHOR}' \
    --ci build=pass \
    --ci tests=pass \
    --ci lint=warn:'style issues' \
    --ci security=pass" \
    "Log check results in CI mode"

echo ""

# ==============================================================================
# TEST 6: Status Checking
# ==============================================================================
log_test_start "Status Checking"

# Check overall project status
assert_success "run_proj status test-app" \
    "Get overall project status"

# Check worktree status
assert_success "run_proj status test-app main" \
    "Get worktree status for 'main'"

# Check specific commit status
assert_output_contains "run_proj status test-app main ${GIT_SHA}" "main" \
    "Get specific commit status"

echo ""

# ==============================================================================
# TEST 7: Report Generation
# ==============================================================================
log_test_start "Report Generation"

# Generate default table report
assert_success "run_proj report test-app" \
    "Generate default table report"

# Generate CSV report
assert_success "run_proj report test-app --format csv" \
    "Generate CSV format report"

# Generate JSON report
assert_success "run_proj report test-app --format json" \
    "Generate JSON format report"

# Report with worktree filter
assert_success "run_proj report test-app --worktree main" \
    "Generate report filtered by worktree"

# Report with date filter
assert_success "run_proj report test-app --since 2024-01-01" \
    "Generate report filtered by date"

echo ""

# ==============================================================================
# TEST 8: Configuration Management
# ==============================================================================
log_test_start "Configuration Management"

# Set default project
assert_success "run_proj config set test-app" \
    "Set default project configuration"

# Get default project
assert_output_contains "run_proj config get" "test-app" \
    "Get default project shows configured project"

# Clear default project
assert_success "run_proj config clear" \
    "Clear project configuration"

# Verify configuration is cleared
assert_output_contains "run_proj config get" "No default" \
    "Configuration cleared, no default project set"

echo ""

# ==============================================================================
# TEST 9: Database Sync (Export/Import)
# ==============================================================================
log_test_start "Database Sync Operations"

# Export database
EXPORT_PATH="${TEST_DIR}/export.db"
assert_success "run_proj sync export --output ${EXPORT_PATH}" \
    "Export database to file"

# Verify export file exists
if [[ -f "${EXPORT_PATH}" ]]; then
    log_success "Exported database file exists"
else
    log_error "Exported database file not found"
fi

echo ""

# ==============================================================================
# TEST 10: Dry-Run Mode
# ==============================================================================
log_test_start "Dry-Run Mode"

# Run checks in dry-run mode (should not record results)
assert_success "run_proj run test-app main --dry-run" \
    "Execute run command in dry-run mode"

echo ""

# ==============================================================================
# Summary
# ==============================================================================
echo ""
echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
echo -e "Total:  $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [[ ${TESTS_FAILED} -eq 0 ]]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
