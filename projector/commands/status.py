"""Status report command."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..db import Database

console = Console()


def status_command(
    project: str,
    worktree: Optional[str] = typer.Argument(None),
    sha: Optional[str] = typer.Argument(None),
    show_archived: bool = typer.Option(False, "--show-archived"),
) -> None:
    """
    Show project status.

    - proj status <project>: latest commit per worktree
    - proj status <project> <worktree>: full history for worktree
    - proj status <project> <worktree> <sha>: specific commit details
    """
    db = Database()
    db.init_schema()

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    if sha:
        # Show specific commit detail
        _show_commit_detail(db, proj["id"], worktree, sha, show_archived)
    elif worktree:
        # Show full history for worktree
        _show_worktree_history(db, proj["id"], worktree, show_archived)
    else:
        # Show latest for all worktrees
        _show_latest_status(db, project, proj["id"], show_archived)


def _show_latest_status(db: Database, project_name: str, project_id: int, show_archived: bool):
    """Show latest commit status for all worktrees."""
    worktrees = db.fetchall(
        "SELECT id, name FROM worktrees WHERE project_id = ? ORDER BY name",
        (project_id,),
    )

    if not worktrees:
        console.print(f"[yellow]No worktrees defined for project '{project_name}'[/yellow]")
        return

    # Get checks
    checks = db.fetchall(
        "SELECT id, name, mandatory FROM checks WHERE project_id = ? AND archived = 0 ORDER BY name",
        (project_id,),
    )

    check_names = [c["name"] for c in checks]

    # Create table
    table = Table(title=f"project: {project_name}")
    table.add_column("worktree", style="cyan")
    table.add_column("sha", style="dim")

    for check in checks:
        style = "bold" if check["mandatory"] else ""
        table.add_column(check["name"], style=style)

    # Add rows
    for wt in worktrees:
        # Get latest commit for this worktree
        latest_commit = db.fetchone(
            "SELECT id, sha FROM commits WHERE worktree_id = ? ORDER BY logged_at DESC LIMIT 1",
            (wt["id"],),
        )

        if not latest_commit:
            row_data = [wt["name"], "—"]
            for _ in check_names:
                row_data.append("—")
            table.add_row(*row_data)
            continue

        sha_short = latest_commit["sha"][:7]
        row_data = [wt["name"], sha_short]

        # Get check results for this commit
        for check in checks:
            result = db.fetchone(
                "SELECT status FROM check_results WHERE commit_id = ? AND check_id = ?",
                (latest_commit["id"], check["id"]),
            )

            if result:
                status = result["status"]
                icon = _status_icon(status)
                row_data.append(icon)
            else:
                row_data.append("—")

        table.add_row(*row_data)

    console.print(table)


def _show_worktree_history(db: Database, project_id: int, worktree_name: str, show_archived: bool):
    """Show full history for a worktree."""
    wt = db.fetchone(
        "SELECT id FROM worktrees WHERE project_id = ? AND name = ?",
        (project_id, worktree_name),
    )

    if not wt:
        console.print(f"[red]✗[/red] Worktree '{worktree_name}' not found")
        raise typer.Exit(1)

    # Get checks
    query = "SELECT id, name, mandatory FROM checks WHERE project_id = ?"
    params = [project_id]
    if not show_archived:
        query += " AND archived = 0"
    query += " ORDER BY name"

    checks = db.fetchall(query, tuple(params))

    # Get commits
    commits = db.fetchall(
        "SELECT id, sha, message, author, logged_at FROM commits WHERE worktree_id = ? ORDER BY logged_at DESC",
        (wt["id"],),
    )

    if not commits:
        console.print(f"[yellow]No commits logged for worktree '{worktree_name}'[/yellow]")
        return

    # Create table
    table = Table(title=f"worktree: {worktree_name}")
    table.add_column("sha", style="dim")
    table.add_column("message", style="cyan")
    table.add_column("author", style="green")
    table.add_column("logged at", style="dim")

    for check in checks:
        style = "bold" if check["mandatory"] else ""
        table.add_column(check["name"], style=style)

    # Add rows
    for commit in commits:
        sha_short = commit["sha"][:7]
        msg = (commit["message"] or "")[:30]
        author = commit["author"] or "—"
        logged = commit["logged_at"] or "—"

        row_data = [sha_short, msg, author, logged]

        # Get check results
        for check in checks:
            result = db.fetchone(
                "SELECT status FROM check_results WHERE commit_id = ? AND check_id = ?",
                (commit["id"], check["id"]),
            )

            if result:
                status = result["status"]
                icon = _status_icon(status)
                row_data.append(icon)
            else:
                row_data.append("—")

        table.add_row(*row_data)

    console.print(table)


def _show_commit_detail(db: Database, project_id: int, worktree_name: str, sha: str, show_archived: bool):
    """Show details for a specific commit."""
    wt = db.fetchone(
        "SELECT id FROM worktrees WHERE project_id = ? AND name = ?",
        (project_id, worktree_name),
    )

    if not wt:
        console.print(f"[red]✗[/red] Worktree '{worktree_name}' not found")
        raise typer.Exit(1)

    commit = db.fetchone(
        "SELECT id, sha, message, author, logged_at, machine_id FROM commits WHERE worktree_id = ? AND sha LIKE ?",
        (wt["id"], f"{sha}%"),
    )

    if not commit:
        console.print(f"[red]✗[/red] Commit '{sha}' not found in worktree '{worktree_name}'")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Commit: {commit['sha'][:7]}[/bold cyan]")
    console.print(f"Message:  {commit['message'] or '—'}")
    console.print(f"Author:   {commit['author'] or '—'}")
    console.print(f"Logged:   {commit['logged_at']}")
    console.print(f"Machine:  {commit['machine_id']}\n")

    # Get check results
    query = "SELECT id, name, mandatory FROM checks WHERE project_id = ?"
    params = [project_id]
    if not show_archived:
        query += " AND archived = 0"
    query += " ORDER BY name"

    checks = db.fetchall(query, tuple(params))

    table = Table(title="Check Results")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Comment", style="magenta")

    for check in checks:
        result = db.fetchone(
            "SELECT status, comment FROM check_results WHERE commit_id = ? AND check_id = ?",
            (commit["id"], check["id"]),
        )

        if result:
            status = result["status"]
            icon = _status_icon(status)
            comment = result["comment"] or "—"
            table.add_row(check["name"], icon, comment)
        else:
            table.add_row(check["name"], "—", "—")

    console.print(table)


def _status_icon(status: str) -> str:
    """Convert status to icon."""
    icons = {
        "pass": "[green]✓ pass[/green]",
        "fail": "[red]✗ fail[/red]",
        "warn": "[yellow]⚠ warn[/yellow]",
        "skip": "[dim]– skip[/dim]",
    }
    return icons.get(status, "—")
