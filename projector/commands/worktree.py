"""Worktree management commands."""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..db import Database

console = Console()


def add_worktree(
    project: str,
    name: str,
    path: Optional[str] = typer.Option(None, "--path", "-p"),
) -> None:
    """Add a worktree to a project."""
    db = Database()
    db.init_schema()

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    try:
        db.insert_and_get_id(
            "worktrees",
            project_id=proj["id"],
            name=name,
            path=path,
            created_at=datetime.now(),
        )
        console.print(f"[green]✓[/green] Worktree '{name}' added to project '{project}'")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


def list_worktrees(project: str) -> None:
    """List all worktrees for a project."""
    db = Database()
    db.init_schema()

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    rows = db.fetchall(
        "SELECT name, path, created_at FROM worktrees WHERE project_id = ? ORDER BY name",
        (proj["id"],),
    )

    if not rows:
        console.print(f"[yellow]No worktrees found for project '{project}'[/yellow]")
        return

    table = Table(title=f"Worktrees for {project}")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Created", style="dim")

    for row in rows:
        table.add_row(
            row["name"],
            row["path"] or "—",
            row["created_at"] or "—",
        )

    console.print(table)


def remove_worktree(
    project: str, name: str, confirm: bool = typer.Option(False, "--yes", "-y")
) -> None:
    """Remove a worktree from a project."""
    db = Database()
    db.init_schema()

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    wt = db.fetchone(
        "SELECT id FROM worktrees WHERE project_id = ? AND name = ?", (proj["id"], name)
    )
    if not wt:
        console.print(f"[red]✗[/red] Worktree '{name}' not found in project '{project}'")
        raise typer.Exit(1)

    if not confirm:
        console.print(
            f"[yellow]This will remove worktree '{name}' and all associated commits and results.[/yellow]"
        )
        if not typer.confirm("Continue?"):
            console.print("Cancelled")
            return

    conn = db.connect()
    cursor = conn.cursor()

    # Delete check_results and commits for this worktree
    commits = cursor.execute("SELECT id FROM commits WHERE worktree_id = ?", (wt["id"],)).fetchall()
    for commit in commits:
        cursor.execute("DELETE FROM check_results WHERE commit_id = ?", (commit["id"],))
    cursor.execute("DELETE FROM commits WHERE worktree_id = ?", (wt["id"],))
    cursor.execute("DELETE FROM worktrees WHERE id = ?", (wt["id"],))

    conn.commit()
    console.print(f"[green]✓[/green] Worktree '{name}' removed")
