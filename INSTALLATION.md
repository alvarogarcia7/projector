# Installation

## Requirements

- Python 3.9+
- `typer[all]>=0.9.0` (CLI framework)
- `rich>=13.0.0` (terminal output)

## Quick Install

### Option 1: Using pip (Recommended)

```bash
git clone https://github.com/you/projector
cd projector
pip install -e .
```

Then you can use `proj` command directly:

```bash
proj --help
proj init
```

### Option 2: Using Python directly

If pip is not available, you can run Projector directly with Python:

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

### Built-in Dependencies (No additional install needed)

- **sqlite3**: Database (stdlib)
- **subprocess**: Git integration (stdlib)
- **socket**: Machine ID detection (stdlib)

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

If using `pip install -e .`, ensure your Python scripts directory is in your PATH:

```bash
# Find where pip installed proj
which proj

# Or run directly
python3 -m projector.cli --help
```

### "ModuleNotFoundError: No module named 'typer'"

Install dependencies:

```bash
pip install typer[all] rich
```

Or if pip is not available, dependencies must be installed system-wide or in a virtualenv.

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
