# Colors for output
COLOR_RESET = \033[0m
COLOR_BOLD = \033[1m
COLOR_GREEN = \033[32m
COLOR_YELLOW = \033[33m
COLOR_BLUE = \033[34m

.PHONY: help
help: ## Show this help message
	@echo "$(COLOR_BOLD)Available targets:$(COLOR_RESET)"
	@sed -n 's/^\.PHONY: \(.*\)$$/\1/p' $(MAKEFILE_LIST) | while read target; do \
		desc=$$(grep -A 0 "^$$target: ## " $(MAKEFILE_LIST) | sed 's/^[^#]*## //'); \
		printf "  $(COLOR_GREEN)%-12s$(COLOR_RESET) - %s\n" "$$target" "$$desc"; \
	done

.PHONY: install
install: ## Install project dependencies
	@echo "$(COLOR_BLUE)Installing dependencies...$(COLOR_RESET)"
	uv sync

.PHONY: dev
dev: ## Install development dependencies
	@echo "$(COLOR_BLUE)Installing dev dependencies...$(COLOR_RESET)"
	${MAKE} install
	uv sync --group dev

.PHONY: lint
lint: ## Run ruff linter
	@echo "$(COLOR_BLUE)Running ruff linter...$(COLOR_RESET)"
	uv run ruff check projector tests --config pyproject.toml

.PHONY: format
format: ## Format code with ruff
	@echo "$(COLOR_BLUE)Formatting code with ruff...$(COLOR_RESET)"
	uv run ruff format projector tests

.PHONY: type
type: ## Run mypy type checking
	@echo "$(COLOR_BLUE)Running mypy type checking...$(COLOR_RESET)"
	uv run mypy projector --config-file pyproject.toml

.PHONY: test
test: ## Run pytest tests
	@echo "$(COLOR_BLUE)Running pytest tests...$(COLOR_RESET)"
	uv run pytest tests -v

.PHONY: coverage
coverage: ## Run tests with coverage report
	@echo "$(COLOR_BLUE)Running tests with coverage...$(COLOR_RESET)"
	uv run pytest tests -v --cov=projector --cov-report=term-missing --cov-report=html

.PHONY: pre-commit
pre-commit: ## Run all checks (lint, type, test)
	$(MAKE) lint
	$(MAKE) type
	$(MAKE) test
	@echo "$(COLOR_GREEN)✓ All checks passed!$(COLOR_RESET)"

.PHONY: clean
clean: ## Remove build artifacts and cache files
	@echo "$(COLOR_BLUE)Cleaning up...$(COLOR_RESET)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete
	@echo "$(COLOR_GREEN)✓ Cleaned!$(COLOR_RESET)"

.PHONY: init
init: ## Initialize the project (install deps, hooks, run tests)
	${MAKE} install
	${MAKE} dev
	${MAKE} clean
	${MAKE} test
	@echo "$(COLOR_GREEN)✓ Project initialized!$(COLOR_RESET)"
