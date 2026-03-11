"""Configure projects and checks from YAML files."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console

from ..db import Database

console = Console()


def configure_from_file(
    config_file: Optional[str] = typer.Option(None, "--file", "-f", help="Path to config file"),
) -> None:
    """
    Configure projects and checks from a YAML file.

    The YAML file should have this structure:

    projects:
      - name: my-app
        description: My Application
        repo: /path/to/repo
        checks:
          - name: build
            description: Build the project
            mandatory: true
          - name: tests
            description: Run unit tests
            mandatory: true
          - name: lint
            description: Code linting
            mandatory: false

    You can also have projects without repo:
      - name: other-project
        checks:
          - name: style
            mandatory: false
    """
    db = Database()
    db.init_schema()

    # Determine config file path
    if config_file:
        config_path = Path(config_file).expanduser()
    else:
        # Try standard locations
        candidates = [
            Path.cwd() / ".projector" / "config.yaml",
            Path.cwd() / ".projector" / "config.yml",
            Path.cwd() / "projector.yaml",
            Path.cwd() / "projector.yml",
            Path.cwd() / ".projector.yaml",
            Path.cwd() / ".projector.yml",
        ]

        config_path = None
        for candidate in candidates:
            if candidate.exists():
                config_path = candidate
                break

        if not config_path:
            console.print(
                "[red]✗[/red] No configuration file found. Specify with --file or create one at:"
            )
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
    if not isinstance(config, dict) or "projects" not in config:
        console.print(
            "[red]✗[/red] Invalid config format. Expected 'projects:' key with list of projects"
        )
        raise typer.Exit(1)

    projects = config.get("projects", [])
    if not isinstance(projects, list):
        console.print("[red]✗[/red] Invalid config: 'projects' must be a list")
        raise typer.Exit(1)

    # Process projects
    projects_added = 0
    checks_added = 0
    skipped = 0

    for proj_config in projects:
        if not isinstance(proj_config, dict):
            console.print(f"[yellow]⚠[/yellow] Skipping invalid project entry: {proj_config}")
            skipped += 1
            continue

        proj_name = proj_config.get("name")
        if not proj_name:
            console.print("[yellow]⚠[/yellow] Skipping project with no 'name' field")
            skipped += 1
            continue

        proj_description = proj_config.get("description")
        proj_repo = proj_config.get("repo")

        # Check if project exists
        existing_proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (proj_name,))

        if existing_proj:
            proj_id = existing_proj["id"]
            console.print(f"[cyan]ℹ[/cyan] Project '{proj_name}' already exists")
        else:
            try:
                proj_id = db.insert_and_get_id(
                    "projects",
                    name=proj_name,
                    description=proj_description,
                    repo_path=proj_repo,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                console.print(f"[green]✓[/green] Project '{proj_name}' created")
                projects_added += 1
            except Exception as e:
                console.print(f"[red]✗[/red] Error creating project '{proj_name}': {e}")
                skipped += 1
                continue

        # Process checks for this project
        proj_checks = proj_config.get("checks", [])
        if isinstance(proj_checks, list):
            for check_config in proj_checks:
                if not isinstance(check_config, dict):
                    console.print("[yellow]⚠[/yellow] Skipping invalid check entry")
                    skipped += 1
                    continue

                check_name = check_config.get("name")
                if not check_name:
                    console.print("[yellow]⚠[/yellow] Skipping check with no 'name' field")
                    skipped += 1
                    continue

                check_description = check_config.get("description")
                check_mandatory = check_config.get("mandatory", False)

                # Check if already exists
                existing_check = db.fetchone(
                    "SELECT id FROM checks WHERE project_id = ? AND name = ?",
                    (proj_id, check_name),
                )

                if existing_check:
                    console.print(f"  [yellow]⚠[/yellow] Check '{check_name}' already exists")
                    skipped += 1
                    continue

                try:
                    db.insert_and_get_id(
                        "checks",
                        project_id=proj_id,
                        name=check_name,
                        description=check_description,
                        mandatory=check_mandatory,
                        archived=False,
                        created_at=datetime.now(),
                    )
                    console.print(f"  [green]✓[/green] Check '{check_name}' added")
                    checks_added += 1
                except Exception as e:
                    console.print(f"  [red]✗[/red] Error adding check '{check_name}': {e}")
                    skipped += 1

    # Summary
    console.print(
        f"\n[bold]Summary:[/bold] "
        f"{projects_added} projects, {checks_added} checks added, {skipped} skipped"
    )

    if projects_added == 0 and checks_added == 0 and skipped > 0:
        raise typer.Exit(1)
