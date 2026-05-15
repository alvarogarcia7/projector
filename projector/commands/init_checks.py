"""Initialize checks from YAML configuration file."""

from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console

from ..db import Database

console = Console()


def init_checks_from_yaml(
    project: str,
    config_file: Optional[str] = typer.Option(None, "--file", "-f", help="Path to checks config file"),
) -> None:
    """
    Initialize checks for a project from a YAML configuration file.

    The YAML file should have this structure:

    checks:
      - name: build
        description: Build the project
        mandatory: true
      - name: tests
        description: Run unit tests
        mandatory: true
      - name: lint
        description: Run linter
        mandatory: false
    """
    db = Database()
    db.init_schema()

    # Get project
    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    # Determine config file path
    if config_file:
        config_path = Path(config_file).expanduser()
    else:
        # Try standard locations
        candidates = [
            Path.cwd() / ".projector" / "checks.yaml",
            Path.cwd() / ".projector" / "checks.yml",
            Path.cwd() / "checks.yaml",
            Path.cwd() / "checks.yml",
            Path.cwd() / ".projector-checks.yaml",
            Path.cwd() / ".projector-checks.yml",
        ]

        config_path = None
        for candidate in candidates:
            if candidate.exists():
                config_path = candidate
                break

        if not config_path:
            console.print("[red]✗[/red] No checks configuration file found. Specify with --file or create one at:")
            for candidate in candidates:
                console.print(f"  {candidate}")
            raise typer.Exit(1)

    # Load YAML
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"[red]✗[/red] File not found: {config_path}")
        raise typer.Exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]✗[/red] Invalid YAML: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Error reading file: {e}")
        raise typer.Exit(1)

    # Validate structure
    if not isinstance(config, dict) or "checks" not in config:
        console.print("[red]✗[/red] Invalid config format. Expected 'checks:' key with list of checks")
        raise typer.Exit(1)

    checks = config.get("checks", [])
    if not isinstance(checks, list):
        console.print("[red]✗[/red] Invalid config: 'checks' must be a list")
        raise typer.Exit(1)

    # Add checks
    from datetime import datetime

    added = 0
    skipped = 0

    for check in checks:
        if not isinstance(check, dict):
            console.print(f"[yellow]⚠[/yellow] Skipping invalid check entry: {check}")
            skipped += 1
            continue

        name = check.get("name")
        if not name:
            console.print("[yellow]⚠[/yellow] Skipping check with no 'name' field")
            skipped += 1
            continue

        description = check.get("description")
        mandatory = check.get("mandatory", False)

        # Check if already exists
        existing = db.fetchone(
            "SELECT id FROM checks WHERE project_id = ? AND name = ?",
            (proj["id"], name),
        )

        if existing:
            console.print(f"[yellow]⚠[/yellow] Check '{name}' already exists, skipping")
            skipped += 1
            continue

        try:
            db.insert_and_get_id(
                "checks",
                project_id=proj["id"],
                name=name,
                description=description,
                mandatory=mandatory,
                archived=False,
                created_at=datetime.now(),
            )
            console.print(f"[green]✓[/green] Check '{name}' added")
            added += 1
        except Exception as e:
            console.print(f"[red]✗[/red] Error adding check '{name}': {e}")
            skipped += 1

    # Summary
    console.print(f"\n[bold]Summary:[/bold] {added} added, {skipped} skipped")
    if added == 0 and skipped > 0:
        raise typer.Exit(1)
