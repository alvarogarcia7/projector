"""Projector CLI entry point using Typer."""

import typer
from .commands import init, project, worktree, check, log, status, report, sync

app = typer.Typer(help="Projector — Track software project health across machines")

# Top-level commands
@app.command()
def init_db(local: bool = typer.Option(False, "--local", help="Create local .projector.db")):
    """Initialize Projector database."""
    init.init_command(local=local)


# Project commands
project_app = typer.Typer(help="Manage projects")
app.add_typer(project_app, name="project")

@project_app.command("add")
def project_add(
    name: str,
    description: str = typer.Option(None, "--description", "-d"),
    repo: str = typer.Option(None, "--repo", "-r"),
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
    path: str = typer.Option(None, "--path", "-p"),
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
    description: str = typer.Option(None, "--description", "-d"),
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


# Log command
@app.command()
def log(
    project: str,
    worktree: str,
    sha: str = typer.Option(None, "--sha"),
    message: str = typer.Option(None, "--message"),
    author: str = typer.Option(None, "--author"),
    ci: list = typer.Option(None, "--ci"),
):
    """Log check results for a commit."""
    log.log_command(project, worktree, sha=sha, message=message, author=author, ci=ci)


# Status command
@app.command()
def status(
    project: str,
    worktree: str = typer.Argument(None),
    sha: str = typer.Argument(None),
    show_archived: bool = typer.Option(False, "--show-archived"),
):
    """Show project status."""
    status.status_command(project, worktree=worktree, sha=sha, show_archived=show_archived)


# Report command
@app.command()
def report(
    project: str,
    format: str = typer.Option("table", "--format", "-f"),
    worktree: str = typer.Option(None, "--worktree", "-w"),
    since: str = typer.Option(None, "--since", "-s"),
):
    """Generate a report of check results."""
    report.report_command(project, format=format, worktree=worktree, since=since)


# Sync commands
sync_app = typer.Typer(help="Sync databases")
app.add_typer(sync_app, name="sync")

@sync_app.command("import")
def sync_import(db_path: str):
    """Import a foreign database."""
    sync.import_command(db_path)


@sync_app.command("export")
def sync_export(output: str = typer.Option(None, "--output", "-o")):
    """Export the local database."""
    sync.export_command(output=output)


if __name__ == "__main__":
    app()
