# Push & Create PR - Step-by-Step Guide

This guide explains how to push the completed E2E test suite and create a pull request.

## Current Status

- **Branch:** `4e8c-create-end-to-en`
- **Local Commits:** 3 (ready to push)
- **Files Ready:**
  - tests/e2e_test.sh (test suite)
  - tests/E2E_TESTS.md (documentation)
  - tests/README.md (quick start)
  - .github/PR_TEMPLATE.md (PR template)
  - Makefile (updated for pipeline)

## Step 1: Push the Branch

When network access is available, execute:

```bash
git push -u origin 4e8c-create-end-to-en
```

Expected output:
```
Enumerating objects: 13, done.
Counting objects: 100% (13/13), done.
Delta compression using up to 8 threads
...
remote: Resolving deltas: 100% (7/7), done.
remote:
remote: Create a pull request for '4e8c-create-end-to-en' on GitHub by visiting:
remote:      https://github.com/alvarogarcia7/projector/pull/new/4e8c-create-end-to-en
```

## Step 2: Create the Pull Request

### Option A: Using GitHub CLI (Recommended)

```bash
gh pr create \
  --title "Create end-to-end test suite and integrate into pipeline" \
  --body "$(cat .github/PR_TEMPLATE.md)"
```

### Option B: Using Manual URL

Visit the URL provided in the push output or navigate to:
```
https://github.com/alvarogarcia7/projector/compare/main...4e8c-create-end-to-en
```

Then click "Create Pull Request" button.

The PR template will be auto-populated from `.github/PR_TEMPLATE.md`.

### Option C: Using gh with Draft PR

If you want to mark it as draft initially:

```bash
gh pr create \
  --title "Create end-to-end test suite and integrate into pipeline" \
  --body "$(cat .github/PR_TEMPLATE.md)" \
  --draft
```

Then remove draft status after verification.

## Step 3: Monitor CI Checks

After the PR is created, GitHub will automatically run:

1. **Linting** (ruff check)
   - Expected: ✓ Pass (tests/ directory is clean)

2. **Type Checking** (mypy)
   - Expected: ✓ Pass (Bash files not checked)

3. **Unit Tests** (pytest)
   - Expected: ✓ Pass (2 tests in tests/test_version.py)

4. **E2E Tests** (bash tests/e2e_test.sh)
   - Expected: ✓ Pass (45+ assertions pass)

## Step 4: Address Any Failures

If CI checks fail, they will be visible in the PR checks section.

### Common Issues

**Network Issues in CI:**
- E2E tests may fail if projector CLI is not in PATH
- Solution: Ensure `uv pip install -e .` runs in CI before tests

**Test Timeouts:**
- E2E tests create temporary directories
- Ensure CI runner has adequate disk space and timeout (default 2 minutes)

**Permission Issues:**
- Ensure test script has execute permission (already set)
- Check CI runner has permission to create temp directories

## Step 5: Request Reviews

Once CI passes, request reviews from team members:

```bash
gh pr view 3  # Replace 3 with actual PR number
gh pr edit 3 --add-reviewer @username
```

## Step 6: Monitor Feedback

Watch for:
- ✓ Approval from reviewers
- ✓ All CI checks pass
- ✓ No merge conflicts

Once approved and CI passes, merge with:

```bash
gh pr merge 3 --squash  # Squash commits for cleaner history
# or
gh pr merge 3 --merge   # Keep all commits
```

## Verify After Merge

After the PR is merged, verify on main branch:

```bash
git checkout main
git pull origin main
git log --oneline -5  # Should show new commits
make test-e2e         # Run tests
```

## Rollback (If Needed)

If the PR needs to be reverted:

```bash
# Close PR without merging
gh pr close 3

# Or revert the commits after merge
git revert <commit-sha>
git push origin main
```

## Summary

| Step | Command | Expected Result |
|------|---------|-----------------|
| 1 | `git push -u origin 4e8c-create-end-to-en` | Branch pushed to GitHub |
| 2 | `gh pr create ...` | PR created, CI starts |
| 3 | Monitor PR checks | All checks pass |
| 4 | Request reviews | Reviewers assigned |
| 5 | Address feedback | PR approved |
| 6 | `gh pr merge 3` | PR merged to main |

## CI/CD Pipeline Summary

The PR will trigger the full pipeline:

```
Push → GitHub Actions
  ├─ Lint (ruff check)
  ├─ Type (mypy)
  ├─ Test (pytest)
  └─ E2E (bash)
       → All Pass ✓
         → Ready for Review
           → Merge
```

## Notes

- E2E tests create isolated test environments (no real data affected)
- Tests clean up after themselves automatically
- All exit codes are properly set (0 = success, 1 = failure)
- PR template includes comprehensive documentation

## Support

If you encounter issues:

1. Check `.github/workflows/` for CI configuration
2. Review test output in PR checks section
3. Run `make pre-commit` locally to debug
4. Check documentation in `tests/README.md` and `tests/E2E_TESTS.md`

---

**Ready to push!** Just run the command in Step 1 when network is available.
