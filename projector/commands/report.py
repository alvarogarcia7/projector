"""Report generation command."""

import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from datetime import datetime
from ..db import Database

console = Console()


def report_command(
    project: str,
    format: str = typer.Option("table", "--format", "-f", help="table, csv, or json"),
    worktree: Optional[str] = typer.Option(None, "--worktree", "-w"),
    since: Optional[str] = typer.Option(None, "--since", "-s", help="Date filter (YYYY-MM-DD)"),
) -> None:
    """
    Generate a report of check results.

    Supports filtering by worktree and date range.
    """
    db = Database()
    db.init_schema()

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    # Build query
    query = """
    SELECT
        p.name as project_name,
        w.name as worktree_name,
        c.sha,
        c.message,
        c.author,
        c.logged_at,
        ch.name as check_name,
        ch.mandatory,
        cr.status,
        cr.comment
    FROM check_results cr
    JOIN commits c ON cr.commit_id = c.id
    JOIN worktrees w ON c.worktree_id = w.id
    JOIN projects p ON w.project_id = p.id
    JOIN checks ch ON cr.check_id = ch.id
    WHERE p.id = ?
    """
    params = [proj["id"]]

    if worktree:
        query += " AND w.name = ?"
        params.append(worktree)

    if since:
        query += " AND c.logged_at >= ?"
        params.append(since)

    query += " ORDER BY c.logged_at DESC, w.name, ch.name"

    rows = db.fetchall(query, tuple(params))

    if not rows:
        console.print("[yellow]No results found[/yellow]")
        return

    if format == "json":
        _output_json(rows)
    elif format == "csv":
        _output_csv(rows)
    else:
        _output_table(rows)


def _output_table(rows):
    """Output as formatted table."""
    table = Table(title="Report")
    table.add_column("Worktree", style="cyan")
    table.add_column("SHA", style="dim")
    table.add_column("Check", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Comment", style="magenta")
    table.add_column("Logged At", style="dim")

    for row in rows:
        sha_short = row["sha"][:7]
        status_icon = _status_icon(row["status"])
        comment = row["comment"] or "—"

        table.add_row(
            row["worktree_name"],
            sha_short,
            row["check_name"],
            status_icon,
            comment,
            row["logged_at"] or "—",
        )

    console.print(table)


def _output_csv(rows):
    """Output as CSV."""
    import csv
    import sys

    writer = csv.DictWriter(sys.stdout, fieldnames=[
        "worktree", "sha", "check", "status", "comment", "logged_at"
    ])
    writer.writeheader()

    for row in rows:
        writer.writerow({
            "worktree": row["worktree_name"],
            "sha": row["sha"],
            "check": row["check_name"],
            "status": row["status"],
            "comment": row["comment"] or "",
            "logged_at": row["logged_at"],
        })


def _output_json(rows):
    """Output as JSON."""
    data = []
    for row in rows:
        # Parse details JSON if present
        details = {}
        if row["comment"]:
            try:
                details = json.loads(row["comment"])
            except json.JSONDecodeError:
                details = {"raw_comment": row["comment"]}

        data.append({
            "worktree": row["worktree_name"],
            "sha": row["sha"],
            "check": row["check_name"],
            "status": row["status"],
            "details": details,
            "logged_at": row["logged_at"],
        })

    console.print(json.dumps(data, indent=2))


def _status_icon(status: str) -> str:
    """Convert status to icon."""
    icons = {
        "pass": "[green]✓ pass[/green]",
        "fail": "[red]✗ fail[/red]",
        "warn": "[yellow]⚠ warn[/yellow]",
        "skip": "[dim]– skip[/dim]",
    }
    return icons.get(status, "—")
