# Installation

## Requirements

- Python 3.9+
- [UV](https://astral.sh/blog/uv) (fast Python package manager)

## Quick Install

### Option 1: Using UV (Recommended)

```bash
git clone https://github.com/you/projector
cd projector

# Install UV if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e .
```

Then you can use `proj` command directly:

```bash
proj --help
proj init
```

### Option 2: Using pip

```bash
git clone https://github.com/you/projector
cd projector
pip install -e .
```

### Option 3: Using Python directly

If package managers are not available, you can run Projector directly with Python:

```bash
cd projector
python3 -m projector.cli --help
```

Or create a shell alias:

```bash
alias proj='python3 -m projector.cli'
```

### Option 3: Docker (Optional)

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENTRYPOINT ["proj"]
```

Build and run:

```bash
docker build -t projector .
docker run --rm projector --help
```

## Dependencies

### Core Dependencies

- **typer**: Modern Python CLI framework with automatic help generation
- **rich**: Beautiful table rendering and terminal formatting
- **click**: Dependency of typer
- **shellingham**: Shell detection for typer

### Built-in Dependencies (No additional install needed)

- **sqlite3**: Database (stdlib)
- **subprocess**: Git integration (stdlib)
- **socket**: Machine ID detection (stdlib)

All dependencies are specified in `pyproject.toml` and locked in `uv.lock` for reproducible builds.

## Verification

After installation, verify everything works:

```bash
proj init
proj project list
```

You should see:

```
[green]✓[/green] Global database initialized at /home/user/.projector/projector.db
[yellow]No projects found[/yellow]
```

## Troubleshooting

### "proj: command not found"

If using `uv pip install -e .` or `pip install -e .`, ensure your Python scripts directory is in your PATH:

```bash
# Find where it was installed
which proj

# Or run directly
python3 -m projector.cli --help
```

### "ModuleNotFoundError: No module named 'typer'"

Install dependencies with UV:

```bash
uv pip install -e .
```

Or with pip:

```bash
pip install -e .
```

The lock file ensures consistent versions across all installations.

### SQLite3 not found

SQLite3 is built into Python. If you're getting errors, you may need to reinstall Python-dev:

```bash
# Ubuntu/Debian
apt-get install python3-dev

# macOS
brew install python3
```

## Development Setup

For development with testing:

```bash
uv pip install -e '.[dev]'
uv run pytest
```

Or with pip:

```bash
pip install -e '.[dev]'
pytest
```

## Creating Entry Point Script

If you want a standalone executable without pip:

```bash
cat > proj << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add projector directory to path
sys.path.insert(0, str(Path(__file__).parent / "projector"))

from projector.cli import app

if __name__ == "__main__":
    app()
EOF

chmod +x proj
./proj --help
```
