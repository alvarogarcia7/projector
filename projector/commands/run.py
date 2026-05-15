"""Run checks and record execution results."""

import json
import logging
import os
import shutil
import socket
import subprocess
import time
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console

from ..cache import clear_cache_entry, get_cache_entry, get_git_changed_files_hash, save_cache_entry
from ..config import apply_path_config
from ..db import Database
from ..git import get_git_info

console = Console()


def run_checks(
    project: str,
    worktree: Optional[str] = typer.Argument(None),
    check: Optional[str] = typer.Option(None, "--check", "-c", help="Run specific check only"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would run without executing"),
    bypass_cache: bool = False,
) -> None:
    """
    Run checks and record results.

    Runs all checks (or a specific one with --check) for the current project/worktree.
    Records execution status, exit code, and execution time.
    """
    logger = logging.getLogger(__name__)
    logger.debug(
        f"run_checks() called with project={project}, worktree={worktree}, "
        f"check={check}, dry_run={dry_run}, bypass_cache={bypass_cache}"
    )

    # Apply configured PATH for checks bin directory
    logger.debug("Applying PATH configuration")
    apply_path_config()
    logger.debug(f"PATH after apply_path_config: {os.environ.get('PATH', '(not set)')}")

    # Compute git hash for caching
    files_hash = get_git_changed_files_hash()
    if not files_hash:
        logger.warning("Could not compute git hash, running checks without cache")
        bypass_cache = True
    else:
        logger.debug(f"Git state hash for cache: {files_hash[:7]}")

    db = Database()
    logger.debug(f"Database initialized at {db.db_path}")
    db.init_schema()

    # Get project
    logger.debug(f"Looking up project '{project}'")
    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        logger.error(f"Project '{project}' not found in database")
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)
    logger.debug(f"Project found: id={proj['id']}")

    # Get worktree (auto-detect if not provided)
    if not worktree:
        logger.debug("Worktree not provided, attempting auto-detect from git")
        # Try to detect from git current branch
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            worktree = result.stdout.strip()
            logger.debug(f"Auto-detected worktree from git: {worktree}")
            console.print(f"[dim]Auto-detected worktree: {worktree}[/dim]")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Failed to auto-detect worktree from git: {e}")
            console.print("[red]✗[/red] Worktree required (could not auto-detect from git)")
            raise typer.Exit(1)

    logger.debug(f"Looking up worktree '{worktree}' in project {proj['id']}")
    wt = db.fetchone(
        "SELECT id FROM worktrees WHERE project_id = ? AND name = ?",
        (proj["id"], worktree),
    )
    if not wt:
        logger.error(f"Worktree '{worktree}' not found in project '{project}'")
        # List available worktrees for debugging
        available = db.fetchall("SELECT name FROM worktrees WHERE project_id = ? ORDER BY name", (proj["id"],))
        if available:
            logger.debug(f"Available worktrees: {[w['name'] for w in available]}")
        console.print(f"[red]✗[/red] Worktree '{worktree}' not found in project '{project}'")
        raise typer.Exit(1)
    logger.debug(f"Worktree found: id={wt['id']}")

    # Get git info
    logger.debug("Retrieving git information")
    git_info = get_git_info()
    if not git_info:
        logger.error("Failed to retrieve git information. Not in a git repository?")
        console.print("[red]✗[/red] Not in a git repository")
        raise typer.Exit(1)

    sha, message, author = git_info
    logger.debug(f"Git info: sha={sha[:7]}, author={author}, message={message[:50] if message else '(none)'}")

    # Check git status (clean or modified)
    logger.debug("Checking git status")
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        is_clean = len(result.stdout.strip()) == 0
        status = "clean" if is_clean else "modified"
        logger.debug(f"Git status: {status}")
        if not is_clean:
            logger.debug(f"Modified files:\n{result.stdout}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Git command failed: {e}. Is git installed and in your PATH?", exc_info=True)
        status = "unknown"

    console.print("\n[bold cyan]Running checks[/bold cyan]")
    console.print(f"  Project:  {project}")
    console.print(f"  Worktree: {worktree}")
    console.print(f"  SHA:      {sha[:7]}")
    console.print(f"  Status:   {status}")
    console.print(f"  Message:  {message or '(none)'}\n")

    # Get checks to run
    logger.debug(f"Fetching checks for project {proj['id']}" + (f", filter by check={check}" if check else ""))
    query = "SELECT id, name, mandatory FROM checks WHERE project_id = ? AND archived = 0 ORDER BY name"
    params = [proj["id"]]
    if check:
        query += " AND name = ?"
        params.append(check)

    checks = db.fetchall(query, tuple(params))
    logger.debug(f"Found {len(checks)} checks to run" + (f": {[c['name'] for c in checks]}" if checks else ""))

    if not checks:
        logger.warning("No checks found")
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
        check_id = check_item["id"]

        logger.debug(f"Processing check '{check_name}' (id={check_id}, mandatory={mandatory})")
        console.print(f"[cyan]Running:[/cyan] {check_name}...", end=" ")

        if dry_run:
            logger.debug(f"Skipping check '{check_name}' (dry-run mode)")
            console.print("[yellow]skipped (dry-run)[/yellow]")
            continue

        # Get check command from database (if it exists)
        # For now, we'll use a convention: check_<name> as a shell command
        check_command = f"check_{check_name}"
        cache_key = check_command

        # Check cache before running
        cache_entry = None
        if bypass_cache:
            if files_hash:
                clear_cache_entry(db, proj["id"], wt["id"], cache_key)
        elif files_hash:
            cache_entry = get_cache_entry(db, proj["id"], wt["id"], cache_key, files_hash)

        if cache_entry:
            logger.info(f"Cache HIT for check '{check_name}' (cached at {cache_entry['cached_at']})")
            exit_code = cache_entry["exit_code"]
            elapsed = cache_entry["execution_time"]
            check_status = "pass" if exit_code == 0 else "fail"
            icon = "[green]✓[/green]" if exit_code == 0 else "[red]✗[/red]"
            console.print(f"{icon} ({elapsed:.2f}s, cached)")

            # Upsert check_result using cached status
            details = {
                "status": check_status,
                "exit_code": exit_code,
                "time": round(elapsed, 2),
                "git_status": status,
                "machine": socket.gethostname(),
                "cached": True,
            }
            comment = json.dumps(details)
            existing_result = db.fetchone(
                "SELECT id FROM check_results WHERE commit_id = ? AND check_id = ?",
                (commit_id, check_id),
            )
            if existing_result:
                db.execute(
                    "UPDATE check_results SET status = ?, comment = ?, logged_at = ?, machine_id = ? WHERE id = ?",
                    (check_status, comment, datetime.now(), socket.gethostname(), existing_result["id"]),
                )
            else:
                db.insert_and_get_id(
                    "check_results",
                    commit_id=commit_id,
                    check_id=check_id,
                    status=check_status,
                    comment=comment,
                    logged_at=datetime.now(),
                    machine_id=socket.gethostname(),
                )
            db.commit()

            results.append(
                {
                    "name": check_name,
                    "status": check_status,
                    "exit_code": exit_code,
                    "time": elapsed,
                    "mandatory": mandatory,
                }
            )
            if mandatory and exit_code != 0:
                failed_mandatory = True
            continue

        logger.debug(f"Executing check command: {check_command}")
        logger.debug(
            f"Shell environment: SHELL={os.environ.get('SHELL', '(not set)')},"
            "CWD={os.getcwd()},"
            "HOME={os.environ.get('HOME', '(not set)')}"
        )

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

            error_code_description = ""
            if exit_code == 127:
                error_code_description = "command not found"
            elif exit_code == 1:
                error_code_description = "general error"
            elif exit_code == 2:
                error_code_description = "misuse of shell builtins"
            elif exit_code == 126:
                error_code_description = "command invoked cannot execute"
            elif exit_code == 128:
                error_code_description = "invalid argument to exit"
            elif exit_code == 130:
                error_code_description = "terminated by CTRL-C"
            elif exit_code == 255:
                error_code_description = "exit status out of range"

            logging.info(
                f"Check '{check_name}' completed in {elapsed:.2f}s with exit code {exit_code}: {error_code_description}"
            )
            if exit_code != 0:
                # List files in PATH and check if command is found and executable
                path_env = os.environ.get("PATH", "")
                logging.debug(f"PATH directories: {path_env}")

                command_path = shutil.which(check_command)
                cmd_status = command_path if command_path else "not found"
                logging.debug(f"Check {check_name}: Looking for command '{check_command}': {cmd_status}")

                if command_path:
                    is_executable = os.access(command_path, os.X_OK)
                    logging.debug(f"Check {check_name}: Command '{check_command}' executable: {is_executable}")
                else:
                    logging.debug(f"Check {check_name}: Command '{check_command}' not found in PATH")
            logging.debug(
                f"Check {check_name}: command '{check_command}' details: {result.stdout.strip() or '(no output)'}"
            )

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
                    (
                        check_status,
                        comment,
                        datetime.now(),
                        socket.gethostname(),
                        existing_result["id"],
                    ),
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

            # Save to cache after successful execution
            if files_hash and not bypass_cache:
                save_cache_entry(
                    db,
                    proj["id"],
                    wt["id"],
                    cache_key,
                    files_hash,
                    result.stdout.decode(errors="replace") if result.stdout else "",
                    result.stderr.decode(errors="replace") if result.stderr else "",
                    exit_code,
                    elapsed,
                    socket.gethostname(),
                )

            console.print(f"{icon} ({elapsed:.2f}s)")

            results.append(
                {
                    "name": check_name,
                    "status": check_status,
                    "exit_code": exit_code,
                    "time": elapsed,
                    "mandatory": mandatory,
                }
            )

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

        logger.info(f"Check results: {passed} passed, {failed} failed, total time: {total_time:.2f}s")
        console.print(f"[bold]Results:[/bold] {passed} passed, {failed} failed (total: {total_time:.2f}s)")

    # Exit with error if mandatory check failed
    if failed_mandatory:
        logger.error("Mandatory check failed - exiting with error code 1")
        console.print("\n[red]✗ Mandatory check failed[/red]")
        raise typer.Exit(1)

    logger.info("All checks passed successfully")
    console.print("[green]✓ All checks passed[/green]")
