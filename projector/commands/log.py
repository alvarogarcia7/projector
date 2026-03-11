"""Log commit check results."""

import socket
from datetime import datetime
from typing import List, Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from ..db import Database
from ..git import get_git_info

console = Console()


def log_command(
    project: str,
    worktree: str,
    sha: Optional[str] = typer.Option(None, "--sha"),
    message: Optional[str] = typer.Option(None, "--message"),
    author: Optional[str] = typer.Option(None, "--author"),
    ci: Optional[List[str]] = typer.Option(None, "--ci"),
) -> None:
    """
    Log check results for a commit.

    Interactive mode (default): prompts for each check.
    CI mode (--ci): non-interactive, can specify check results directly.
    """
    db = Database()
    db.init_schema()

    # Validate project and worktree exist
    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    wt = db.fetchone(
        "SELECT id FROM worktrees WHERE project_id = ? AND name = ?",
        (proj["id"], worktree),
    )
    if not wt:
        console.print(f"[red]✗[/red] Worktree '{worktree}' not found in project '{project}'")
        raise typer.Exit(1)

    # Auto-detect git info if not provided
    if sha is None or message is None or author is None:
        git_info = get_git_info()
        if git_info:
            git_sha, git_msg, git_author = git_info
            sha = sha or git_sha
            message = message or git_msg
            author = author or git_author

    # Prompt for missing info
    if sha is None:
        sha = Prompt.ask("Enter commit SHA")
    if message is None:
        message = Prompt.ask("Enter commit message (optional)", default="")
    if author is None:
        author = Prompt.ask("Enter commit author (optional)", default="")

    message = message or None
    author = author or None

    # Get or create commit entry
    existing_commit = db.fetchone(
        "SELECT id FROM commits WHERE worktree_id = ? AND sha = ?",
        (wt["id"], sha),
    )

    machine_id = socket.gethostname()

    if existing_commit:
        commit_id = existing_commit["id"]
    else:
        commit_id = db.insert_and_get_id(
            "commits",
            worktree_id=wt["id"],
            sha=sha,
            message=message,
            author=author,
            logged_at=datetime.now(),
            machine_id=machine_id,
        )

    # Get all active checks for this project
    checks = db.fetchall(
        "SELECT id, name, mandatory FROM checks WHERE project_id = ? AND archived = 0 ORDER BY name",
        (proj["id"],),
    )

    if not checks:
        console.print("[yellow]No active checks defined for this project[/yellow]")
        return

    if ci:
        # CI mode: parse --ci flags
        _log_ci_mode(db, commit_id, checks, ci, machine_id)
    else:
        # Interactive mode
        _log_interactive_mode(db, commit_id, checks, machine_id)

    console.print(f"[green]✓[/green] Commit logged for {project}/{worktree} at {sha[:7]}")


def _log_interactive_mode(db: Database, commit_id: int, checks: list, machine_id: str):
    """Interactive logging mode."""
    for check in checks:
        mandatory_marker = "[bold red]●[/bold red]" if check["mandatory"] else ""
        prompt_text = f"{mandatory_marker} {check['name']} [pass/fail/warn/skip]"

        while True:
            status = Prompt.ask(prompt_text).lower()
            if status in ("pass", "fail", "warn", "skip"):
                break
            console.print("[yellow]Invalid status. Use: pass, fail, warn, or skip[/yellow]")

        # For mandatory checks, confirm skip
        if check["mandatory"] and status == "skip":
            if not Confirm.ask(f"Confirm skip for mandatory check '{check['name']}'"):
                continue

        # Prompt for optional comment
        comment = None
        if status != "pass":
            comment = Prompt.ask("Comment (optional)", default="")
            comment = comment or None

        # Insert or update check result
        existing = db.fetchone(
            "SELECT id FROM check_results WHERE commit_id = ? AND check_id = ?",
            (commit_id, check["id"]),
        )

        if existing:
            db.execute(
                "UPDATE check_results SET status = ?, comment = ?, logged_at = ?, machine_id = ? WHERE id = ?",
                (status, comment, datetime.now(), machine_id, existing["id"]),
            )
        else:
            db.insert_and_get_id(
                "check_results",
                commit_id=commit_id,
                check_id=check["id"],
                status=status,
                comment=comment,
                logged_at=datetime.now(),
                machine_id=machine_id,
            )

        db.commit()


def _log_ci_mode(db: Database, commit_id: int, checks: list, ci_flags: List[str], machine_id: str):
    """CI mode logging: parse --ci flags and log results."""
    # Parse CI flags
    ci_map = {}
    for flag in ci_flags:
        parts = flag.split("=", 1)
        if len(parts) != 2:
            console.print(f"[red]Invalid --ci flag format: {flag}[/red]")
            raise typer.Exit(1)

        check_name = parts[0]
        result_part = parts[1]

        # Parse status and optional comment
        if ":" in result_part:
            status, comment = result_part.split(":", 1)
        else:
            status, comment = result_part, None

        if status not in ("pass", "fail", "warn", "skip"):
            console.print(f"[red]Invalid status '{status}' for check '{check_name}'[/red]")
            raise typer.Exit(1)

        ci_map[check_name] = (status, comment)

    # Log all checks
    has_failed_mandatory = False

    for check in checks:
        if check["name"] in ci_map:
            status, comment = ci_map[check["name"]]
        else:
            # Not specified: default to skip
            status, comment = "skip", None

        # Insert or update check result
        existing = db.fetchone(
            "SELECT id FROM check_results WHERE commit_id = ? AND check_id = ?",
            (commit_id, check["id"]),
        )

        if existing:
            db.execute(
                "UPDATE check_results SET status = ?, comment = ?, logged_at = ?, machine_id = ? WHERE id = ?",
                (status, comment, datetime.now(), machine_id, existing["id"]),
            )
        else:
            db.insert_and_get_id(
                "check_results",
                commit_id=commit_id,
                check_id=check["id"],
                status=status,
                comment=comment,
                logged_at=datetime.now(),
                machine_id=machine_id,
            )

        # Track if mandatory check failed
        if check["mandatory"] and status == "fail":
            has_failed_mandatory = True

    db.commit()

    if has_failed_mandatory:
        raise typer.Exit(1)
