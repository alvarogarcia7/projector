# Projector YAML Configuration Samples

This directory contains example YAML configurations demonstrating how to set up Projector for various project types and architectures.

## Quick Start

### Load a sample configuration
```bash
proj configure --file samples/full-stack-app.yaml
```

### Load checks into an existing project
```bash
proj init-checks my-project --file samples/checks-library.yaml
```

## Sample Files

### 1. **full-stack-app.yaml**
Complete full-stack web application with frontend, backend, and infrastructure.

**Projects:**
- `webapp-backend`: Node.js/Express REST API with 8 checks
- `webapp-frontend`: React/TypeScript SPA with 7 checks
- `webapp-infra`: Terraform infrastructure with 4 checks

**Use case:** Modern web applications with separate teams for backend, frontend, and infrastructure.

**Key checks:** Build, tests, lint, type-check, security, bundle-size, visual regression

### 2. **python-projects.yaml**
Python-based projects including data science, ETL, and libraries.

**Projects:**
- `ml-pipeline`: Machine learning training pipeline
- `etl-service`: Batch ETL processing
- `analytics-lib`: Reusable Python library

**Use case:** Data science teams, analytics platforms, and library development.

**Key checks:** Pytest, mypy type-checking, schema validation, model quality, performance benchmarks

### 3. **microservices.yaml**
Microservices architecture with multiple containerized services.

**Projects:**
- `user-service`: User management (Go)
- `order-service`: Order processing (Go)
- `notification-service`: Event-driven notifications (Go)
- `api-gateway`: Service mesh entry point (Go)

**Use case:** Distributed systems, service-oriented architectures, Kubernetes deployments.

**Key checks:** Go build/test/lint, Docker build, security scanning, Helm validation, load testing

### 4. **checks-library.yaml**
Comprehensive reusable checks for common workflows.

**Categories:**
- Build and compilation
- Testing (unit, integration, E2E)
- Code quality (lint, format, type-check)
- Security (scanning, dependency audit, secrets)
- Documentation and API docs
- Performance and monitoring
- Infrastructure (Docker, Helm, Terraform)
- Database and data validation
- Accessibility and compliance

**Use case:** Use as a reference when adding checks to projects. Import subsets into specific projects.

### 5. **minimal-examples.yaml**
Simplest possible project configurations.

**Projects:**
- No checks (project only)
- Single mandatory check
- Three basic checks (build, tests, lint)

**Use case:** Quick reference for minimal setup, template for new projects.

## Configuration Structure

### Project Definition
```yaml
projects:
  - name: project-name              # Required
    description: "Project summary"   # Optional
    repo: "https://github.com/..."   # Optional
    checks:                          # Optional list of checks
      - name: check-name             # Required
        description: "What it does"   # Optional
        mandatory: true              # Optional (default: false)
```

### Checks Definition
```yaml
checks:
  - name: check-name               # Required
    description: "What it does"    # Optional
    mandatory: true                # Optional (default: false)
```

## Check Naming Convention

Check names become shell commands with the pattern `check_<name>`:
- Check `build` → runs `check_build` command
- Check `unit-tests` → runs `check_unit-tests` command
- Check `type-check` → runs `check_type-check` command

Implement these commands as shell scripts, binaries, or aliases in your PATH.

## Mandatory vs Optional

**Mandatory checks:**
- Command must exit with code 0 to pass
- If any mandatory check fails, `proj run` exits with code 1
- Failure blocks deployment/integration
- Examples: build, tests, security, lint

**Optional checks:**
- Exit code is recorded but doesn't block
- All results are still logged to database
- For informational/monitoring purposes
- Examples: coverage, performance, documentation

## How to Use These Samples

### 1. Load all projects from a sample
```bash
proj configure --file samples/full-stack-app.yaml
```

### 2. Load only specific checks
```bash
proj init-checks my-project --file samples/checks-library.yaml
```

### 3. Use as templates
Copy a sample file and customize:
```bash
cp samples/full-stack-app.yaml my-project-config.yaml
# Edit my-project-config.yaml
proj configure --file my-project-config.yaml
```

### 4. Mix and match
Create your own YAML combining multiple samples:
```yaml
projects:
  - name: my-api
    description: Custom API
    checks:
      - name: build
        mandatory: true
      - name: tests
        mandatory: true
      - name: lint
        mandatory: true
      - name: security
        mandatory: true
```

## Real-World Scenarios

### Scenario 1: New Team Setup
1. Start with `minimal-examples.yaml` for basic structure
2. Add checks from `checks-library.yaml` as needed
3. Customize for your tech stack

### Scenario 2: Full-Stack Application
1. Use `full-stack-app.yaml` as template
2. Adjust check names to match your actual commands
3. Modify mandatory/optional flags based on policy
4. Load separately into frontend, backend, infra projects

### Scenario 3: Microservices Platform
1. Start with `microservices.yaml`
2. Replicate service template for each microservice
3. Add language/framework-specific checks
4. Configure deployment and monitoring checks

### Scenario 4: Data Science Team
1. Use `python-projects.yaml` as template
2. Add data validation and model quality checks
3. Include performance benchmarks
4. Configure ML-specific tooling

## Implementation Notes

- All sample files use the YAML 1.2 specification
- Configuration is idempotent: loading twice won't duplicate projects
- Unknown checks/projects are skipped (no errors)
- Empty values and missing optional fields are handled gracefully
- Comments in YAML are preserved for documentation

## Tips

1. **Keep check names consistent** across projects (e.g., always use `build` not `compile`)
2. **Document mandatory checks** - only critical path should be mandatory
3. **Version your configs** - track in git alongside your projects
4. **Start minimal** - add checks incrementally as needed
5. **Use descriptions** - helps team members understand what each check does

## Next Steps

- [View the main README](../README.md) for complete Projector documentation
- [Check the quick reference](../QUICKREF.md) for command syntax
- Implement the `check_*` shell commands in your projects
- Set up `proj run` in your CI/CD pipelines
