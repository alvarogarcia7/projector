"""Projector CLI entry point using Typer."""

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
    save_path_config,
    save_project_config,
)


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


app = typer.Typer(
    help="Projector — Track software project health across machines", no_args_is_help=True
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
project_app = typer.Typer(help="Manage projects")
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
worktree_app = typer.Typer(help="Manage worktrees")
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
check_app = typer.Typer(help="Manage checks")
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
    report.report_command(project, format=format, worktree=worktree, since=since)


# Sync commands
sync_app = typer.Typer(help="Sync databases")
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
config_app = typer.Typer(help="Manage local configuration")
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(project: str):
    """Set the default project for this directory."""
    save_project_config(project)
    typer.echo(f"✓ Default project set to '{project}'")


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

    config_file = Path.cwd() / ".projector-config"
    if config_file.exists():
        config_file.unlink()
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
