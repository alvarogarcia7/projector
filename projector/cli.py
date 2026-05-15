"""Projector CLI entry point using Typer."""

import logging
from typing import List, Optional

import typer

from .commands import (
    check,
    configure,
    init,
    init_checks,
    log,
    project,
    report,
    run,
    runner,
    status,
    sync,
    worktree,
)
from .config import (
    apply_path_config,
    clear_path_config,
    get_checks_bin_path,
    get_path_config,
    get_project_from_config,
    get_resolved_log_level,
    get_worktree_from_config,
    save_path_config,
    save_project_config,
    save_worktree_config,
)
from .db import Database
from .git import get_git_branch


def resolve_project(project_arg: Optional[str]) -> str:
    """Resolve project name from argument or config."""
    if project_arg:
        return project_arg

    config_project = get_project_from_config()
    if config_project:
        return config_project

    typer.echo("Error: Project name required. Either:")
    typer.echo("  1. Provide project name as argument: proj status my-app")
    typer.echo("  2. Save project config: proj config set my-app")
    raise typer.Exit(1)


def resolve_worktree(worktree_arg: Optional[str]) -> Optional[str]:
    """Resolve worktree name from argument or config."""
    if worktree_arg:
        return worktree_arg

    return get_worktree_from_config()


app = typer.Typer(
    help="Projector — Track software project health across machines", no_args_is_help=True
)


@app.callback()
def main(
    ctx: typer.Context,
    log_level: Optional[str] = typer.Option(
        None,
        "--log-level",
        help="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
        envvar="PROJECTOR_LOG_LEVEL",
    ),
):
    """Projector — Track software project health across machines."""
    level = get_resolved_log_level(log_level)
    logging.basicConfig(
        level=getattr(logging, level, logging.WARNING),
        format="%(levelname)s: %(message)s",
    )


# Top-level commands
@app.command(name="init")
def init_db(local: bool = typer.Option(False, "--local", help="Create local .projector.db")):
    """Initialize Projector database."""
    init.init_command(local=local)


@app.command(name="configure")
def configure_cmd(config_file: Optional[str] = typer.Option(None, "--file", "-f")):
    """Configure projects and checks from YAML file."""
    configure.configure_from_file(config_file=config_file)


@app.command(name="init-checks")
def init_checks_cmd(
    project: Optional[str] = typer.Argument(None),
    config_file: Optional[str] = typer.Option(None, "--file", "-f"),
):
    """Initialize checks for a project from YAML file."""
    project = resolve_project(project)
    init_checks.init_checks_from_yaml(project, config_file=config_file)


# Project commands
project_app = typer.Typer(help="Manage projects", no_args_is_help=True)
app.add_typer(project_app, name="project")


@project_app.command("add")
def project_add(
    name: str,
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r"),
):
    """Add a new project."""
    project.add_project(name, description=description, repo=repo)


@project_app.command("list")
def project_list():
    """List all projects."""
    project.list_projects()


@project_app.command("show")
def project_show(name: str):
    """Show project details."""
    project.show_project(name)


@project_app.command("remove")
def project_remove(name: str, yes: bool = typer.Option(False, "--yes", "-y")):
    """Remove a project."""
    project.remove_project(name, confirm=yes)


# Worktree commands
worktree_app = typer.Typer(help="Manage worktrees", no_args_is_help=True)
app.add_typer(worktree_app, name="worktree")


@worktree_app.command("add")
def worktree_add(
    project: str,
    name: str,
    path: Optional[str] = typer.Option(None, "--path", "-p"),
):
    """Add a worktree to a project."""
    worktree.add_worktree(project, name, path=path)


@worktree_app.command("list")
def worktree_list(project: str):
    """List worktrees for a project."""
    worktree.list_worktrees(project)


@worktree_app.command("remove")
def worktree_remove(project: str, name: str, yes: bool = typer.Option(False, "--yes", "-y")):
    """Remove a worktree from a project."""
    worktree.remove_worktree(project, name, confirm=yes)


# Check commands
check_app = typer.Typer(help="Manage checks", no_args_is_help=True)
app.add_typer(check_app, name="check")


@check_app.command("add")
def check_add(
    project: str,
    name: str,
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    mandatory: bool = typer.Option(False, "--mandatory", "-m"),
):
    """Add a check to a project."""
    check.add_check(project, name, description=description, mandatory=mandatory)


@check_app.command("list")
def check_list(
    project: str,
    show_archived: bool = typer.Option(False, "--show-archived"),
):
    """List checks for a project."""
    check.list_checks(project, show_archived=show_archived)


@check_app.command("archive")
def check_archive(project: str, name: str):
    """Archive a check (soft delete)."""
    check.archive_check(project, name)


@check_app.command("restore")
def check_restore(project: str, name: str):
    """Restore an archived check."""
    check.restore_check(project, name)


# Run command
@app.command(name="run")
def run_cmd(
    project: Optional[str] = typer.Argument(None),
    worktree: Optional[str] = typer.Argument(None),
    check: Optional[str] = typer.Option(None, "--check", "-c"),
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    """Run checks and record results."""
    project = resolve_project(project)
    worktree = resolve_worktree(worktree)
    run.run_checks(project, worktree=worktree, check=check, dry_run=dry_run)


# Runner command
@app.command(name="runner", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def runner_cmd(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p"),
    worktree: Optional[str] = typer.Option(None, "--worktree", "-w"),
    bypass_cache: bool = typer.Option(False, "-B", help="Bypass cache and force re-execution"),
):
    """Run arbitrary command with caching."""
    runner.runner_command(
        command_args=ctx.args,
        project=project,
        worktree=worktree,
        bypass_cache=bypass_cache,
    )


# Log command
@app.command(name="log")
def log_commit(
    project: str,
    worktree: str,
    sha: Optional[str] = typer.Option(None, "--sha"),
    message: Optional[str] = typer.Option(None, "--message"),
    author: Optional[str] = typer.Option(None, "--author"),
    ci: Optional[List[str]] = typer.Option(None, "--ci", help="CI mode results"),
):
    """Log check results for a commit."""
    log.log_command(project, worktree, sha=sha, message=message, author=author, ci=ci)


# Status command
@app.command(name="status")
def status_cmd(
    project: Optional[str] = typer.Argument(None),
    worktree: Optional[str] = typer.Argument(None),
    sha: Optional[str] = typer.Argument(None),
    show_archived: bool = typer.Option(False, "--show-archived"),
):
    """Show project status."""
    project = resolve_project(project)
    worktree = resolve_worktree(worktree)
    status.status_command(project, worktree=worktree, sha=sha, show_archived=show_archived)


# Report command
@app.command(name="report")
def report_cmd(
    project: Optional[str] = typer.Argument(None),
    format: str = typer.Option("table", "--format", "-f"),
    worktree: Optional[str] = typer.Option(None, "--worktree", "-w"),
    since: Optional[str] = typer.Option(None, "--since", "-s"),
):
    """Generate a report of check results."""
    project = resolve_project(project)
    worktree = resolve_worktree(worktree)
    report.report_command(project, format=format, worktree=worktree, since=since)


# Sync commands
sync_app = typer.Typer(help="Sync databases", no_args_is_help=True)
app.add_typer(sync_app, name="sync")


@sync_app.command("import")
def sync_import(db_path: str):
    """Import a foreign database."""
    sync.import_command(db_path)


@sync_app.command("export")
def sync_export(output: Optional[str] = typer.Option(None, "--output", "-o")):
    """Export the local database."""
    sync.export_command(output=output)


# Config commands
config_app = typer.Typer(help="Manage local configuration", no_args_is_help=True)
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(project: str):
    """Set the default project for this directory."""
    from datetime import datetime
    from pathlib import Path

    save_project_config(project)
    typer.echo(f"✓ Default project set to '{project}'")

    # Also save the current git branch as the worktree
    branch = get_git_branch()
    if branch:
        db = Database()
        db.init_schema()

        # Get project from database
        proj = db.fetchone("SELECT id FROM projects WHERE name = ?", (project,))
        if proj:
            # Check if worktree already exists
            wt = db.fetchone(
                "SELECT id FROM worktrees WHERE project_id = ? AND name = ?",
                (proj["id"], branch),
            )
            if not wt:
                # Create the worktree
                try:
                    db.insert_and_get_id(
                        "worktrees",
                        project_id=proj["id"],
                        name=branch,
                        path=None,
                        created_at=datetime.now(),
                    )
                    typer.echo(f"✓ Worktree '{branch}' created in project '{project}'")
                except Exception as e:
                    typer.echo(f"[yellow]⚠[/yellow] Could not create worktree: {e}")
            else:
                typer.echo(f"✓ Worktree '{branch}' already exists")
        else:
            typer.echo(f"[yellow]⚠[/yellow] Project '{project}' not found in database")

        save_worktree_config(branch)
        typer.echo(f"✓ Default worktree set to '{branch}' (from current branch)")
    else:
        typer.echo("[yellow]⚠[/yellow] Not in a git repository; worktree not set")

    # Set up PATH to include bin/ directory
    bin_dir = Path.cwd() / "bin"
    if bin_dir.exists():
        save_path_config(str(bin_dir))
        apply_path_config()
        typer.echo(f"✓ Added {bin_dir} to PATH")
    else:
        typer.echo(f"[dim]Note: bin/ directory not found at {bin_dir}[/dim]")


@config_app.command("get")
def config_get():
    """Show the default project for this directory."""
    project = get_project_from_config()
    if project:
        typer.echo(f"Default project: {project}")
    else:
        typer.echo("No default project set")


@config_app.command("clear")
def config_clear():
    """Clear the default project for this directory."""
    from pathlib import Path

    # Read current config
    env_path = Path.cwd() / ".projector" / ".env"
    if env_path.exists():
        # Remove PROJECT key from .env
        env_data = {}
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    if key.strip() != "PROJECT":
                        env_data[key.strip()] = value.strip()

        # Rewrite without PROJECT key
        if env_data:
            env_path.parent.mkdir(parents=True, exist_ok=True)
            with open(env_path, "w") as f:
                for key, value in env_data.items():
                    f.write(f"{key}={value}\n")
        else:
            # Remove empty .env file
            env_path.unlink()
        typer.echo("✓ Default project cleared")
    else:
        typer.echo("No default project configured")


@config_app.command("path-set")
def config_path_set(bin_path: Optional[str] = typer.Argument(None)):
    """Configure checks bin directory for this project."""
    if not bin_path:
        # Auto-detect bin/ directory
        detected = get_checks_bin_path()
        if detected:
            bin_path = str(detected)
            typer.echo(f"Auto-detected bin directory: {bin_path}")
        else:
            typer.echo("Error: bin/ directory not found and no path provided")
            typer.echo("Usage: proj config path-set /path/to/bin")
            raise typer.Exit(1)

    # Verify the path exists
    from pathlib import Path

    if not Path(bin_path).exists():
        typer.echo(f"Error: Path does not exist: {bin_path}")
        raise typer.Exit(1)

    save_path_config(bin_path)
    typer.echo(f"✓ Checks bin path set to '{bin_path}'")
    typer.echo("Hint: Run 'proj config path-apply' to update your environment")


@config_app.command("path-get")
def config_path_get():
    """Show the configured checks bin directory."""
    path = get_path_config()
    if path:
        typer.echo(f"Checks bin path: {path}")
    else:
        typer.echo("No checks bin path configured")
        typer.echo("Use 'proj config path-set' to configure")


@config_app.command("path-apply")
def config_path_apply():
    """Apply the configured checks bin directory to PATH."""
    apply_path_config()
    path = get_path_config()
    if path:
        typer.echo(f"✓ Added to PATH: {path}")
        typer.echo("Tip: Add to your shell profile to make it permanent:")
        typer.echo(f'  export PATH="{path}:$PATH"')
    else:
        typer.echo("No checks bin path configured")
        typer.echo("Use 'proj config path-set' first")


@config_app.command("path-clear")
def config_path_clear():
    """Clear the checks bin directory configuration."""
    clear_path_config()
    typer.echo("✓ Checks bin path cleared")


if __name__ == "__main__":
    app()
