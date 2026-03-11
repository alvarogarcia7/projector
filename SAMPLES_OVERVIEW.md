# Projector YAML Samples Overview

Quick guide to the sample configurations in the `samples/` directory.

## What's Inside

### Configuration Files (YAML)

```
samples/
├── full-stack-app.yaml           # Web app: frontend, backend, infra
├── python-projects.yaml           # Data science & libraries
├── microservices.yaml             # Go microservices with Docker/K8s
├── checks-library.yaml            # 25+ reusable common checks
└── minimal-examples.yaml          # Simple starter templates
```

### Documentation

```
samples/
├── README.md                       # Complete guide to all samples
└── IMPLEMENTATION_GUIDE.md         # How to create check_* commands
```

## Quick Reference

| File | Projects | Checks | Tech Stack | Use Case |
|------|----------|--------|-----------|----------|
| **full-stack-app.yaml** | 3 | 19 | Node.js, React, Terraform | Modern web applications |
| **python-projects.yaml** | 3 | 17 | Python, pytest, mypy | Data science, ML, libraries |
| **microservices.yaml** | 4 | 19 | Go, Docker, Kubernetes | Distributed systems |
| **checks-library.yaml** | 0 | 25+ | Language-agnostic | Import into any project |
| **minimal-examples.yaml** | 4 | 5 | Generic | Quick reference templates |

## Load Samples

### Load all projects from a sample
```bash
proj configure --file samples/full-stack-app.yaml
```

### Add checks to existing project
```bash
proj init-checks my-project --file samples/checks-library.yaml
```

### Use as template
```bash
cp samples/full-stack-app.yaml my-config.yaml
# Edit my-config.yaml
proj configure --file my-config.yaml
```

## Sample Contents

### full-stack-app.yaml (3 projects)
- **webapp-backend**: REST API with 8 checks
  - build, tests, coverage, lint, type-check, security, database-migrations, api-docs
- **webapp-frontend**: React SPA with 7 checks
  - build, tests, lint, type-check, visual-regression, bundle-size, accessibility
- **webapp-infra**: Terraform with 4 checks
  - validate, format, plan, security-scan

### python-projects.yaml (3 projects)
- **ml-pipeline**: ML training with 7 checks
  - build, tests, lint, type-check, data-validation, model-quality, performance
- **etl-service**: Batch processing with 6 checks
  - build, tests, lint, schema-validation, dry-run, performance
- **analytics-lib**: Python library with 6 checks
  - build, tests, lint, type-check, docs, compatibility

### microservices.yaml (4 projects)
- **user-service**: User management with 6 checks
  - build, tests, lint, docker-build, security-scan, helm-validate
- **order-service**: Order processing with 6 checks
  - build, tests, lint, docker-build, security-scan, integration-tests
- **notification-service**: Event-driven with 5 checks
  - build, tests, lint, docker-build, schema-validation, load-test
- **api-gateway**: Gateway/mesh entry with 6 checks
  - build, tests, lint, docker-build, rate-limit-test, tls-validation

### checks-library.yaml (25+ checks)
- **Build**: build, build-release
- **Testing**: tests, integration-tests, e2e-tests, coverage
- **Quality**: lint, format, type-check, style
- **Security**: security, dependency-audit, sast, secrets-scan
- **Documentation**: docs, api-docs
- **Performance**: performance, bundle-size, load-test
- **Infrastructure**: docker-build, helm-validate, terraform-validate, terraform-plan
- **Data**: database-migrate, schema-validate, data-quality
- **Compliance**: accessibility, compliance

### minimal-examples.yaml (4 projects)
- **simple-project**: No checks
- **basic-project**: Single check (build)
- **documented-project**: No checks (description only)
- **standard-project**: 4 checks (build, tests, lint, deploy)

## Learning Path

### 1. Start Here
```bash
# Look at minimal-examples.yaml
cat samples/minimal-examples.yaml

# Load it
proj configure --file samples/minimal-examples.yaml

# Run a check
proj run simple-project main
```

### 2. Pick Your Tech Stack
- Web apps: Use **full-stack-app.yaml**
- Data science: Use **python-projects.yaml**
- Microservices: Use **microservices.yaml**
- Custom: Use **checks-library.yaml**

### 3. Customize
```bash
# Copy template
cp samples/full-stack-app.yaml my-app-config.yaml

# Edit with your:
# - Project names
# - Check names (must match your check_* commands)
# - Mandatory/optional flags
# - Descriptions

# Load it
proj configure --file my-app-config.yaml
```

### 4. Implement Check Commands
Follow IMPLEMENTATION_GUIDE.md to create your `check_*` scripts

### 5. Run and Monitor
```bash
proj run my-project main
proj report my-project --format json
```

## Common Patterns

### Pattern 1: Minimal Mandatory Checks
```yaml
- name: build
  mandatory: true
- name: tests
  mandatory: true
- name: lint
  mandatory: true
```

### Pattern 2: Tiered Quality Gate
```yaml
- name: build         # Always required
  mandatory: true
- name: tests         # Always required
  mandatory: true
- name: lint          # Code quality gate
  mandatory: true
- name: coverage      # Informational
  mandatory: false
- name: performance   # Monitoring
  mandatory: false
```

### Pattern 3: Environment-Specific
```yaml
# For staging/production checks
- name: security      # Required for security
  mandatory: true
- name: deploy        # Validation only
  mandatory: false
- name: load-test     # Performance check
  mandatory: false
```

### Pattern 4: Component-Specific
```yaml
# Frontend checks
- name: build
  mandatory: true
- name: tests
  mandatory: true
- name: accessibility
  mandatory: false  # Important but not blocking
- name: bundle-size
  mandatory: false  # Monitoring

# Backend checks
- name: build
  mandatory: true
- name: tests
  mandatory: true
- name: database-migrations
  mandatory: true   # Critical for backend
- name: api-docs
  mandatory: false
```

## Tips

1. **Keep it simple**: Start with minimal checks, add incrementally
2. **Use existing samples**: Copy and modify rather than creating from scratch
3. **Name consistently**: Use the same check names across projects
4. **Test locally first**: Implement check_* commands before loading config
5. **Document checks**: Use descriptions to explain purpose
6. **Version your config**: Commit YAML files to git with project code

## Next Steps

1. Read `samples/README.md` for complete documentation
2. Read `samples/IMPLEMENTATION_GUIDE.md` to implement check commands
3. Choose a sample and customize for your project
4. Load configuration: `proj configure --file samples/YOUR_SAMPLE.yaml`
5. Create your check_* commands
6. Run checks: `proj run project-name branch-name`
7. Monitor results: `proj report project-name`

## Files Reference

- **samples/full-stack-app.yaml** (2.5 KB)
  - 3 projects with realistic checks for complete web applications
  - Good template for full-stack teams

- **samples/python-projects.yaml** (2.3 KB)
  - 3 Python projects with data science focus
  - Examples of ML, ETL, and library patterns

- **samples/microservices.yaml** (2.9 KB)
  - 4 microservices with container and K8s checks
  - Real-world distributed system example

- **samples/checks-library.yaml** (2.7 KB)
  - 25+ checks across all categories
  - Use as reference or import selectively

- **samples/minimal-examples.yaml** (656 B)
  - 4 minimal configurations
  - Good quick reference

- **samples/README.md** (6.5 KB)
  - Complete guide to each sample
  - Configuration structure documentation
  - Usage scenarios and tips

- **samples/IMPLEMENTATION_GUIDE.md** (7.8 KB)
  - How to create check_* commands
  - Examples for Node.js, Python, Go, Rust
  - CI/CD integration patterns
  - Caching and optimization tips
