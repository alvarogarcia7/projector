"""Run arbitrary commands with caching."""

import socket
import subprocess
import sys
import time
from typing import List, Optional

import typer
from rich.console import Console

from ..cache import clear_cache_entry, get_cache_entry, get_git_changed_files_hash, save_cache_entry
from ..db import Database

console = Console()


def runner_command(
    command_args: List[str],
    project: Optional[str] = None,
    worktree: Optional[str] = None,
    bypass_cache: bool = False,
) -> None:
    """
    Run a command with caching.

    Executes the given command and caches the results based on git state.
    On subsequent runs with the same git state, returns cached results instantly.
    Use -B to bypass cache and force re-execution.
    """
    if not command_args:
        console.print("[red]✗[/red] No command specified")
        raise typer.Exit(1)

    command = " ".join(command_args)

    db = Database()
    db.init_schema()

    if not project:
        from ..config import get_project_from_config

        project = get_project_from_config()
        if not project:
            console.print("[red]✗[/red] Project required. Set with: proj config set <project>")
            raise typer.Exit(1)

    proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
    if not proj:
        console.print(f"[red]✗[/red] Project '{project}' not found")
        raise typer.Exit(1)

    if not worktree:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            worktree = result.stdout.strip()
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

    files_hash = get_git_changed_files_hash()
    if not files_hash:
        console.print("[yellow]![/yellow] Could not compute git hash, running without cache")
        bypass_cache = True

    if bypass_cache and files_hash:
        clear_cache_entry(db, proj["id"], wt["id"], command)

    cache_entry = None
    if not bypass_cache and files_hash:
        cache_entry = get_cache_entry(db, proj["id"], wt["id"], command, files_hash)

    if cache_entry:
        console.print(f"[dim]Using cached result from {cache_entry['cached_at']}[/dim]")

        if cache_entry["stdout"]:
            sys.stdout.write(cache_entry["stdout"])
            sys.stdout.flush()

        if cache_entry["stderr"]:
            sys.stderr.write(cache_entry["stderr"])
            sys.stderr.flush()

        exit_code = cache_entry["exit_code"]
        raise typer.Exit(exit_code)

    start_time = time.time()

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
    )

    elapsed = time.time() - start_time

    stdout = result.stdout
    stderr = result.stderr
    exit_code = result.returncode

    if stdout:
        sys.stdout.write(stdout)
        sys.stdout.flush()

    if stderr:
        sys.stderr.write(stderr)
        sys.stderr.flush()

    if files_hash:
        save_cache_entry(
            db,
            proj["id"],
            wt["id"],
            command,
            files_hash,
            stdout or "",
            stderr or "",
            exit_code,
            elapsed,
            socket.gethostname(),
        )

    raise typer.Exit(exit_code)
