# Configuring PATH for Check Commands

Projector can now automatically manage your PATH to include the checks bin directory, eliminating the need for manual `export PATH="$PWD/bin:$PATH"` before running checks.

## Quick Start

### Step 1: Configure PATH (One Time)
```bash
proj config path-set
```

This auto-detects your `bin/` directory and saves the configuration.

### Step 2: Run Checks (No Manual PATH Needed)
```bash
proj run my-project main
```

That's it! The checks will now be found and executed.

## Commands

### `proj config path-set [path]`
Configure the checks bin directory for the current project.

**With auto-detection:**
```bash
proj config path-set
```
Searches for `bin/` directory in current or parent directories and auto-configures.

**With explicit path:**
```bash
proj config path-set /path/to/bin
```
Configures a specific directory.

**Output:**
```
✓ Checks bin path set to '/home/user/project/bin'
Hint: Run 'proj config path-apply' to update your environment
```

### `proj config path-get`
Show the currently configured checks bin path.

```bash
$ proj config path-get
Checks bin path: /home/user/project/bin
```

### `proj config path-apply`
Manually apply the configured PATH to your current shell session.

```bash
$ proj config path-apply
✓ Added to PATH: /home/user/project/bin
Tip: Add to your shell profile to make it permanent:
  export PATH="/home/user/project/bin:$PATH"
```

### `proj config path-clear`
Remove the PATH configuration.

```bash
$ proj config path-clear
✓ Checks bin path cleared
```

## How It Works

### Configuration File
When you run `proj config path-set`, Projector creates a `.projector-path` file in your project:

```bash
$ cat .projector-path
/home/user/project/bin
```

### Automatic Application
When you run `proj run`, Projector:
1. Reads the `.projector-path` file
2. Adds that directory to the PATH environment variable
3. Executes the checks
4. The PATH change is temporary (only for that command execution)

### Environment Isolation
The PATH modification is local to the `proj run` command and doesn't affect your shell permanently. This prevents pollution of your environment.

## Examples

### Complete Workflow

```bash
# 1. Initialize your project
proj init

# 2. Load configuration
proj configure --file samples/full-stack-app.yaml

# 3. Add worktrees
proj worktree add webapp-backend main

# 4. Configure PATH (one time)
proj config path-set

# 5. Now run checks without any PATH manipulation
proj run webapp-backend main
```

### Per-Project Configuration

If you have multiple projects with different check locations:

```bash
# Project 1
cd /path/to/project1
proj config path-set          # Auto-detects ./bin

# Project 2
cd /path/to/project2
proj config path-set          # Auto-detects ./bin (different location)

# When you run commands, the correct PATH is applied automatically
proj run project1 main
proj run project2 main
```

### Permanent Shell Configuration (Optional)

To make the PATH permanent in your shell, you can apply it manually once:

```bash
# For current session
proj config path-apply
source ~/.bashrc   # If using bash

# Or add to your shell profile permanently
echo 'export PATH="/path/to/project/bin:$PATH"' >> ~/.bashrc
```

## Troubleshooting

### Problem: Checks still not found
```bash
$ proj run my-project main
✗ Running: build... (0.00s)
```

**Solution:** Configure PATH first:
```bash
proj config path-set
proj run my-project main
```

### Problem: Wrong PATH configured
```bash
$ proj config path-get
Checks bin path: /old/path/bin
```

**Solution:** Update the configuration:
```bash
proj config path-clear
proj config path-set /correct/path/bin
```

### Problem: Auto-detection failed
```bash
proj config path-set
Error: bin/ directory not found and no path provided
```

**Solution:** Manually specify the path:
```bash
proj config path-set /home/user/my-project/bin
```

## Configuration Files

### `.projector-path`
Stores the configured checks bin directory path. Created by `proj config path-set`.

**Example:**
```
/home/user/project/bin
```

**Location:** Project root directory (same level as `.projector-config`)

### `.projector-config`
Stores the default project name for your directory.

**Related command:** `proj config set my-project`

## Integration with CI/CD

### GitHub Actions
No PATH configuration needed in CI/CD:

```yaml
- name: Run Projector checks
  run: |
    proj config path-set              # Configure once
    proj run my-project main           # Works automatically
```

### GitLab CI
```yaml
run-checks:
  script:
    - proj config path-set
    - proj run my-project main
```

### Local Development
After first-time setup:
```bash
proj config path-set        # One time
proj run my-project main    # Always works
```

## Advanced Usage

### Checking Current Configuration
```bash
# What's configured?
proj config path-get

# What's in the actual PATH?
echo $PATH

# Where are my checks?
ls -la $(proj config path-get | grep -o '^[^ ]*')/check_*
```

### Manual PATH Override
If you need to override temporarily:
```bash
# Use explicit PATH
export PATH="/custom/path/bin:$PATH"
proj run my-project main

# Or set configuration to different path
proj config path-set /custom/path/bin
proj run my-project main
```

### Debugging Check Execution
```bash
# Verify check exists
which check_build

# If not found, check configuration
proj config path-get

# Apply it
proj config path-apply

# Try again
which check_build
```

## FAQ

**Q: Do I need to configure PATH every time?**
A: No, only once per project. The configuration is saved in `.projector-path`.

**Q: What if I move my project?**
A: You may need to reconfigure if the `bin/` directory path changes:
```bash
proj config path-set    # Auto-detects new location
```

**Q: Can I use a different bin directory name?**
A: Yes, specify it explicitly:
```bash
proj config path-set /path/to/checks-scripts
```

**Q: Does this affect my shell PATH permanently?**
A: No, the PATH modification is temporary and only applies to the `proj run` command.

**Q: What if I want to use system-wide checks?**
A: Configure the system path:
```bash
proj config path-set /usr/local/bin
```

## Summary

| Task | Command |
|------|---------|
| Configure PATH (auto-detect) | `proj config path-set` |
| Configure PATH (explicit) | `proj config path-set /path/to/bin` |
| Show configuration | `proj config path-get` |
| Apply to current shell | `proj config path-apply` |
| Remove configuration | `proj config path-clear` |
| Run checks | `proj run project main` |

After running `proj config path-set` once, you can immediately start using `proj run` without any manual PATH management!
