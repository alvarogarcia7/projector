# Implementing Check Commands

This guide explains how to create the `check_*` shell commands that Projector expects.

## Command Naming Convention

Projector looks for commands named `check_<check-name>`:

| Check Name | Command | Example |
|-----------|---------|---------|
| `build` | `check_build` | Build the project |
| `tests` | `check_tests` | Run test suite |
| `lint` | `check_lint` | Run linter |
| `type-check` | `check_type-check` | Type checking |
| `security` | `check_security` | Security scan |
| `docker-build` | `check_docker-build` | Build Docker image |

## Exit Codes

- **0** = Pass
- **Non-zero** = Fail
- The exit code is recorded in the database as `exit_code`

For mandatory checks, exit code 0 is required or `proj run` fails.

## Implementation Options

### Option 1: Shell Script

Create `check_build` as a shell script:

```bash
#!/bin/bash
set -e

echo "Running build..."
npm install
npm run build
echo "Build successful"
exit 0
```

Make it executable:
```bash
chmod +x check_build
```

### Option 2: Makefile Target

If you use Make:

```makefile
.PHONY: check_build
check_build:
	npm install
	npm run build
```

Then run with:
```bash
make check_build
```

### Option 3: Package Manager Script

Define in `package.json`:

```json
{
  "scripts": {
    "check_build": "npm run build",
    "check_tests": "jest --coverage",
    "check_lint": "eslint ."
  }
}
```

Then use npm to run:
```bash
npm run check_build
```

### Option 4: Language-Specific

#### Node.js/npm
```bash
#!/bin/bash
npm run check_tests
```

#### Python
```bash
#!/bin/bash
python -m pytest
```

#### Go
```bash
#!/bin/bash
go build ./cmd/app
go test ./...
```

#### Rust
```bash
#!/bin/bash
cargo build
cargo test
```

## Putting Commands in PATH

### Method 1: Project Root

Store scripts in project root, add to PATH in CI:

```bash
export PATH="$PWD:$PATH"
proj run my-project main
```

### Method 2: Bin Directory

Create `bin/` directory in project:

```bash
mkdir -p bin
# Create check scripts here
chmod +x bin/check_*
export PATH="$PWD/bin:$PATH"
proj run my-project main
```

### Method 3: Global Installation

Install to `/usr/local/bin` (for development):

```bash
cp check_* /usr/local/bin/
proj run my-project main
```

### Method 4: Docker Container

In `Dockerfile`:

```dockerfile
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# Make check scripts executable
COPY bin/check_* /usr/local/bin/
RUN chmod +x /usr/local/bin/check_*

CMD ["proj", "run", "my-project", "main"]
```

### Method 5: Via symlinks in /usr/local/bin

```bash
ln -s /path/to/check_build /usr/local/bin/check_build
ln -s /path/to/check_tests /usr/local/bin/check_tests
```

## Real-World Examples

### Node.js/TypeScript Project

Create `scripts/check.sh`:

```bash
#!/bin/bash
set -e

# Create check command scripts
mkdir -p bin

# check_build: Install and build
cat > bin/check_build << 'EOF'
#!/bin/bash
set -e
npm install
npm run build
EOF

# check_tests: Run tests
cat > bin/check_tests << 'EOF'
#!/bin/bash
set -e
npm test -- --coverage
EOF

# check_lint: Linting
cat > bin/check_lint << 'EOF'
#!/bin/bash
set -e
npm run lint
npm run format:check
EOF

# check_type-check: TypeScript checking
cat > bin/check_type-check << 'EOF'
#!/bin/bash
set -e
npx tsc --noEmit
EOF

# check_security: Security scan
cat > bin/check_security << 'EOF'
#!/bin/bash
set -e
npx snyk test
EOF

chmod +x bin/check_*
export PATH="$PWD/bin:$PATH"
```

### Python Project

Create `scripts/install_checks.py`:

```python
#!/usr/bin/env python3
import os
import stat

checks_dir = "bin"
os.makedirs(checks_dir, exist_ok=True)

checks = {
    "build": """#!/bin/bash
set -e
python -m pip install -e .
""",
    "tests": """#!/bin/bash
set -e
python -m pytest --cov
""",
    "lint": """#!/bin/bash
set -e
pylint src/
black --check src/
isort --check-only src/
""",
    "type-check": """#!/bin/bash
set -e
mypy src/
""",
    "security": """#!/bin/bash
set -e
bandit -r src/
safety check
""",
}

for name, content in checks.items():
    path = f"{checks_dir}/check_{name}"
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    print(f"Created {path}")
```

### Go Project

Create `Makefile`:

```makefile
.PHONY: check_%
check_%:
	@echo "Running check: $*"

check_build:
	go build -o bin/myapp ./cmd/app

check_tests:
	go test -v -race ./...

check_lint:
	golangci-lint run ./...

check_type-check:
	go vet ./...

check_security:
	gosec ./...

check_docker-build:
	docker build -t myapp:latest .
```

### Makefile for All Languages

```makefile
.PHONY: install-checks

install-checks:
	mkdir -p bin
	chmod +x scripts/check_*.sh
	cp scripts/check_*.sh bin/
	ln -sf $(PWD)/bin/check_* /usr/local/bin/ || true
```

## Timing Considerations

Projector records execution time. Keep these in mind:

- **Fast checks:** build, lint, type-check (< 1 minute)
- **Medium checks:** unit tests (1-5 minutes)
- **Slow checks:** integration tests, performance tests (5-30+ minutes)

For slow checks, consider:
- Running in parallel if possible
- Splitting into multiple smaller checks
- Making them optional vs mandatory
- Running only on specific branches in CI

## Environment Variables

Your check commands can access:

```bash
#!/bin/bash
# Inside a check_* command, you can reference:
git_status="${GIT_STATUS}"  # clean or modified
project_name="${PROJECT}"    # project name
worktree_name="${WORKTREE}"  # branch/worktree name
sha="${SHA}"                 # git commit SHA
```

To pass these to checks, modify your invocation:

```bash
GIT_STATUS="clean" PROJECT="my-app" WORKTREE="main" \
  SHA="abc123" proj run my-app main
```

## Error Handling

### Mandatory Check Failures

```bash
#!/bin/bash
set -e  # Exit on first error

if ! npm test; then
    echo "Tests failed - check_tests exits with non-zero"
    exit 1
fi
```

### Optional Check Failures

```bash
#!/bin/bash
# Allow non-zero exit, but still fail if critical parts fail

npm run lint || {
    echo "Linting issues found (but not blocking)"
    exit 0  # Return success anyway
}
```

## Caching

For expensive checks, consider caching:

```bash
#!/bin/bash
# Npm example - cache node_modules between runs
if [ ! -d node_modules ]; then
    npm install
else
    npm ci  # faster when node_modules exists
fi
npm test
```

## Logging and Output

Projector captures output from your check commands:

```bash
#!/bin/bash
echo "Starting tests..."
npm test
echo "Tests completed successfully"
```

This output appears in console when running `proj run` interactively.

## Testing Your Check Commands

Before adding to Projector:

```bash
# Test that check_build exists and runs
which check_build
check_build
echo "Exit code: $?"

# Test exit codes
check_optional_check
test_result=$?
echo "Optional check returned: $test_result"

# Add to PATH and test with proj
export PATH="$PWD/bin:$PATH"
proj run my-project main
```

## CI/CD Integration

### GitHub Actions

```yaml
jobs:
  projector-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          npm install
          mkdir -p bin
          cp scripts/check_* bin/
          chmod +x bin/check_*
      - name: Run Projector checks
        run: |
          export PATH="$PWD/bin:$PATH"
          uv run proj run my-project main
```

### GitLab CI

```yaml
projector_checks:
  script:
    - npm install
    - mkdir -p bin
    - cp scripts/check_* bin/
    - chmod +x bin/check_*
    - export PATH="$PWD/bin:$PATH"
    - uv run proj run my-project main
```

## Summary

1. Create `check_<name>` scripts/commands for each check
2. Exit with 0 for pass, non-zero for fail
3. Add to PATH so `proj run` can find them
4. Use `proj run` to execute and record results
5. Check database for execution metrics
6. Integrate into CI/CD pipelines
