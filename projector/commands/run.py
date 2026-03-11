"""Run checks and record execution results."""

import subprocess
import time
import json
import socket
from datetime import datetime
from typing import Optional
import typer
from rich.console import Console
from ..db import Database
from ..git import get_git_info
from ..config import apply_path_config

console = Console()


def run_checks(
    project: str,
    worktree: Optional[str] = typer.Argument(None),
    check: Optional[str] = typer.Option(None, "--check", "-c", help="Run specific check only"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would run without executing"),
) -> None:
    """
    Run checks and record results.

    Runs all checks (or a specific one with --check) for the current project/worktree.
    Records execution status, exit code, and execution time.
    """
    # Apply configured PATH for checks bin directory
    apply_path_config()

    db = Database()
    db.init_schema()

    # Get project
    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    # Get worktree (auto-detect if not provided)
    if not worktree:
        # Try to detect from git current branch
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            worktree = result.stdout.strip()
            console.print(f"[dim]Auto-detected worktree: {worktree}[/dim]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[red]✗[/red] Worktree required (could not auto-detect from git)")
            raise typer.Exit(1)

    wt = db.fetchone(
        "SELECT id FROM worktrees WHERE project_id = ? AND name = ?",
        (proj["id"], worktree),
    )
    if not wt:
        console.print(f"[red]✗[/red] Worktree '{worktree}' not found in project '{project}'")
        raise typer.Exit(1)

    # Get git info
    git_info = get_git_info()
    if not git_info:
        console.print("[red]✗[/red] Not in a git repository")
        raise typer.Exit(1)

    sha, message, author = git_info

    # Check git status (clean or modified)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        is_clean = len(result.stdout.strip()) == 0
        status = "clean" if is_clean else "modified"
    except (subprocess.CalledProcessError, FileNotFoundError):
        status = "unknown"

    console.print("\n[bold cyan]Running checks[/bold cyan]")
    console.print(f"  Project:  {project}")
    console.print(f"  Worktree: {worktree}")
    console.print(f"  SHA:      {sha[:7]}")
    console.print(f"  Status:   {status}")
    console.print(f"  Message:  {message or '(none)'}\n")

    # Get checks to run
    query = "SELECT id, name, mandatory FROM checks WHERE project_id = ? AND archived = 0 ORDER BY name"
    params = [proj["id"]]
    if check:
        query += " AND name = ?"
        params.append(check)

    checks = db.fetchall(query, tuple(params))

    if not checks:
        console.print("[yellow]No checks found[/yellow]")
        return

    # Create or get commit entry
    existing_commit = db.fetchone(
        "SELECT id FROM commits WHERE worktree_id = ? AND sha = ?",
        (wt["id"], sha),
    )

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
            machine_id=socket.gethostname(),
        )

    # Run checks
    failed_mandatory = False
    results = []

    for check_item in checks:
        check_name = check_item["name"]
        mandatory = check_item["mandatory"]

        console.print(f"[cyan]Running:[/cyan] {check_name}...", end=" ")

        if dry_run:
            console.print("[yellow]skipped (dry-run)[/yellow]")
            continue

        # Get check command from database (if it exists)
        # For now, we'll use a convention: check_<name> as a shell command
        check_command = f"check_{check_name}"

        start_time = time.time()
        try:
            result = subprocess.run(
                check_command,
                shell=True,
                capture_output=True,
                timeout=300,  # 5 minute timeout
            )
            exit_code = result.returncode
            elapsed = time.time() - start_time

            # Determine result status
            if exit_code == 0:
                check_status = "pass"
                icon = "[green]✓[/green]"
            else:
                check_status = "fail"
                icon = "[red]✗[/red]"

            # Record result with full execution details as JSON
            existing_result = db.fetchone(
                "SELECT id FROM check_results WHERE commit_id = ? AND check_id = ?",
                (commit_id, check_item["id"]),
            )

            details = {
                "status": "pass" if exit_code == 0 else "fail",
                "exit_code": exit_code,
                "time": round(elapsed, 2),
                "git_status": status,
                "machine": socket.gethostname(),
            }
            comment = json.dumps(details)

            if existing_result:
                db.execute(
                    "UPDATE check_results SET status = ?, comment = ?, logged_at = ?, machine_id = ? WHERE id = ?",
                    (check_status, comment, datetime.now(), socket.gethostname(), existing_result["id"]),
                )
            else:
                db.insert_and_get_id(
                    "check_results",
                    commit_id=commit_id,
                    check_id=check_item["id"],
                    status=check_status,
                    comment=comment,
                    logged_at=datetime.now(),
                    machine_id=socket.gethostname(),
                )

            db.commit()

            console.print(f"{icon} ({elapsed:.2f}s)")

            results.append({
                "name": check_name,
                "status": check_status,
                "exit_code": exit_code,
                "time": elapsed,
                "mandatory": mandatory,
            })

            if mandatory and exit_code != 0:
                failed_mandatory = True

        except subprocess.TimeoutExpired:
            console.print("[red]✗[/red] timeout")
            details = {
                "status": "fail",
                "error": "timeout",
                "timeout_seconds": 300,
                "git_status": status,
                "machine": socket.gethostname(),
            }
            comment = json.dumps(details)
            existing_result = db.fetchone(
                "SELECT id FROM check_results WHERE commit_id = ? AND check_id = ?",
                (commit_id, check_item["id"]),
            )
            if existing_result:
                db.execute(
                    "UPDATE check_results SET status = ?, comment = ?, logged_at = ?, machine_id = ? WHERE id = ?",
                    ("fail", comment, datetime.now(), socket.gethostname(), existing_result["id"]),
                )
            else:
                db.insert_and_get_id(
                    "check_results",
                    commit_id=commit_id,
                    check_id=check_item["id"],
                    status="fail",
                    comment=comment,
                    logged_at=datetime.now(),
                    machine_id=socket.gethostname(),
                )
            db.commit()
            failed_mandatory = True

        except Exception as e:
            console.print(f"[red]✗[/red] error: {e}")
            details = {
                "status": "fail",
                "error": str(e),
                "git_status": status,
                "machine": socket.gethostname(),
            }
            comment = json.dumps(details)
            existing_result = db.fetchone(
                "SELECT id FROM check_results WHERE commit_id = ? AND check_id = ?",
                (commit_id, check_item["id"]),
            )
            if existing_result:
                db.execute(
                    "UPDATE check_results SET status = ?, comment = ?, logged_at = ?, machine_id = ? WHERE id = ?",
                    ("fail", comment, datetime.now(), socket.gethostname(), existing_result["id"]),
                )
            else:
                db.insert_and_get_id(
                    "check_results",
                    commit_id=commit_id,
                    check_id=check_item["id"],
                    status="fail",
                    comment=comment,
                    logged_at=datetime.now(),
                    machine_id=socket.gethostname(),
                )
            db.commit()
            failed_mandatory = True

    # Print summary
    console.print()
    if results:
        passed = sum(1 for r in results if r["status"] == "pass")
        failed = sum(1 for r in results if r["status"] == "fail")
        total_time = sum(r["time"] for r in results)

        console.print(f"[bold]Results:[/bold] {passed} passed, {failed} failed (total: {total_time:.2f}s)")

    # Exit with error if mandatory check failed
    if failed_mandatory:
        console.print("\n[red]✗ Mandatory check failed[/red]")
        raise typer.Exit(1)

    console.print("[green]✓ All checks passed[/green]")
