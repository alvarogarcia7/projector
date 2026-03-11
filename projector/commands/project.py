"""Project management commands."""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..db import Database

console = Console()


def add_project(
    name: str,
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r"),
) -> None:
    """Add a new project."""
    db = Database()
    db.init_schema()

    try:
        db.insert_and_get_id(
            "projects",
            name=name,
            description=description,
            repo_path=repo,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        console.print(f"[green]✓[/green] Project '{name}' created")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


def list_projects() -> None:
    """List all projects."""
    db = Database()
    db.init_schema()

    rows = db.fetchall(
        "SELECT id, name, description, repo_path, created_at FROM projects ORDER BY name"
    )

    if not rows:
        console.print("[yellow]No projects found[/yellow]")
        return

    table = Table(title="Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="magenta")
    table.add_column("Repo Path", style="green")
    table.add_column("Created", style="dim")

    for row in rows:
        table.add_row(
            row["name"],
            row["description"] or "—",
            row["repo_path"] or "—",
            row["created_at"] or "—",
        )

    console.print(table)


def show_project(name: str) -> None:
    """Show project details."""
    db = Database()
    db.init_schema()

    project = db.fetchone("SELECT * FROM projects WHERE name = ?", (name,))

    if not project:
        console.print(f"[red]✗[/red] Project '{name}' not found")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Project: {project['name']}[/bold cyan]")
    console.print(f"Description: {project['description'] or '—'}")
    console.print(f"Repo Path:   {project['repo_path'] or '—'}")
    console.print(f"Created:     {project['created_at']}")
    console.print(f"Updated:     {project['updated_at']}\n")


def remove_project(name: str, confirm: bool = typer.Option(False, "--yes", "-y")) -> None:
    """Remove a project (this will also remove associated data)."""
    db = Database()
    db.init_schema()

    project = db.fetchone("SELECT id FROM projects WHERE name = ?", (name,))

    if not project:
        console.print(f"[red]✗[/red] Project '{name}' not found")
        raise typer.Exit(1)

    if not confirm:
        console.print(
            f"[yellow]This will remove project '{name}' and all associated data.[/yellow]"
        )
        if not typer.confirm("Continue?"):
            console.print("Cancelled")
            return

    conn = db.connect()
    cursor = conn.cursor()

    # Get all worktrees for this project
    worktrees = cursor.execute(
        "SELECT id FROM worktrees WHERE project_id = ?", (project["id"],)
    ).fetchall()

    # Delete check_results, commits, checks, worktrees
    for wt in worktrees:
        commits = cursor.execute(
            "SELECT id FROM commits WHERE worktree_id = ?", (wt["id"],)
        ).fetchall()
        for commit in commits:
            cursor.execute("DELETE FROM check_results WHERE commit_id = ?", (commit["id"],))
        cursor.execute("DELETE FROM commits WHERE worktree_id = ?", (wt["id"],))
    cursor.execute("DELETE FROM checks WHERE project_id = ?", (project["id"],))
    cursor.execute("DELETE FROM worktrees WHERE project_id = ?", (project["id"],))
    cursor.execute("DELETE FROM projects WHERE id = ?", (project["id"],))

    conn.commit()
    console.print(f"[green]✓[/green] Project '{name}' removed")
