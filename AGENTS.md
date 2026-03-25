1→# AGENTS.md - Development Guide
2→
3→## Commands
4→
5→**Setup:** `uv sync` (uses `.venv` convention from gitignore)  
6→**Build:** N/A (Python CLI, no build step)  
7→**Lint:** `make lint` or `uv run ruff check projector tests`  
8→**Test:** `make test` or `uv run pytest tests -v` (includes e2e tests)  
9→**Dev Server:** N/A (CLI tool, use `uv run proj <command>` for testing)
10→
11→## Tech Stack
12→
13→Python 3.9+ CLI using **uv** package manager, **Typer** (CLI framework), **Rich** (terminal UI), **SQLite** (database), **PyYAML** (config). No build required.
14→
15→## Architecture
16→
17→- `projector/`: Core package with CLI entry point (`cli.py`), database layer (`db.py`), models (`models.py`), git integration (`git.py`), merge logic (`merge.py`)
18→- `projector/commands/`: Command modules (init, project, worktree, check, log, status, report, sync, run)
19→- `tests/`: Pytest tests + e2e bash tests
20→
21→## Code Style
22→
23→- **Linter:** Ruff (120 char line length, Python 3.9 target)
24→- **Type hints:** Encouraged but not strictly required (mypy configured with `disallow_untyped_defs = false`)
25→- **Formatting:** Ruff (run `make format`)
26→- **No comments** unless complex logic requires explanation
27→- Follow existing patterns in `projector/commands/` for new commands
28→