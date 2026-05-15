"""Check management commands."""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..db import Database

console = Console()


def add_check(
    project: str,
    name: str,
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    mandatory: bool = typer.Option(False, "--mandatory", "-m"),
) -> None:
    """Add a check to a project."""
    db = Database()
    db.init_schema()

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

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
        console.print(f"[green]✓[/green] Check '{name}' added to project '{project}'")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


def list_checks(
    project: str,
    show_archived: bool = typer.Option(False, "--show-archived"),
) -> None:
    """List all checks for a project."""
    db = Database()
    db.init_schema()

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    query = "SELECT id, name, description, mandatory, archived, archived_at FROM checks WHERE project_id = ?"
    params = [proj["id"]]

    if not show_archived:
        query += " AND archived = 0"

    query += " ORDER BY name"

    rows = db.fetchall(query, tuple(params))

    if not rows:
        console.print(f"[yellow]No checks found for project '{project}'[/yellow]")
        return

    table = Table(title=f"Checks for {project}")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="magenta")
    table.add_column("Mandatory", style="red")
    table.add_column("Status", style="green")

    for row in rows:
        mandatory_marker = "[bold red]●[/bold red]" if row["mandatory"] else "○"
        status = "[dim red]archived[/dim red]" if row["archived"] else "active"
        table.add_row(
            row["name"],
            row["description"] or "—",
            mandatory_marker,
            status,
        )

    console.print(table)


def archive_check(project: str, name: str) -> None:
    """Archive a check (soft delete)."""
    db = Database()
    db.init_schema()

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    check = db.fetchone("SELECT id FROM checks WHERE project_id = ? AND name = ?", (proj["id"], name))
    if not check:
        console.print(f"[red]✗[/red] Check '{name}' not found in project '{project}'")
        raise typer.Exit(1)

    db.execute(
        "UPDATE checks SET archived = 1, archived_at = ? WHERE id = ?",
        (datetime.now(), check["id"]),
    )
    db.commit()

    console.print(f"[green]✓[/green] Check '{name}' archived")


def restore_check(project: str, name: str) -> None:
    """Restore an archived check."""
    db = Database()
    db.init_schema()

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    check = db.fetchone("SELECT id FROM checks WHERE project_id = ? AND name = ?", (proj["id"], name))
    if not check:
        console.print(f"[red]✗[/red] Check '{name}' not found in project '{project}'")
        raise typer.Exit(1)

    db.execute(
        "UPDATE checks SET archived = 0, archived_at = NULL WHERE id = ?",
        (check["id"],),
    )
    db.commit()

    console.print(f"[green]✓[/green] Check '{name}' restored")
