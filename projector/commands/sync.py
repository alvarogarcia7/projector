"""Database sync commands (import and export)."""

from pathlib import Path
import shutil
from typing import Optional
import typer
from rich.console import Console
from ..db import Database
from ..merge import MergeManager

console = Console()


def import_command(db_path: str) -> None:
    """Import a foreign database into the local database."""
    foreign_path = Path(db_path).expanduser()

    if not foreign_path.exists():
        console.print(f"[red]✗[/red] File not found: {foreign_path}")
        raise typer.Exit(1)

    db = Database()
    db.init_schema()

    console.print(f"[cyan]Importing from: {foreign_path}[/cyan]")

    merger = MergeManager(db, str(foreign_path))

    try:
        stats = merger.import_db()

        console.print("\n[green]✓[/green] Import complete")
        console.print(f"  Rows received: {stats['rows_received']}")
        console.print(f"  Rows sent: {stats['rows_sent']}")
        console.print(f"  Conflicts resolved: {stats['conflicts']}")

    except Exception as e:
        console.print(f"[red]✗[/red] Error during import: {e}")
        raise typer.Exit(1)


def export_command(output: Optional[str] = typer.Option(None, "--output", "-o")) -> None:
    """Export the local database for sharing."""
    db = Database()

    if not db.db_path.exists():
        console.print("[red]✗[/red] Local database not found. Run 'proj init' first.")
        raise typer.Exit(1)

    if output is None:
        output = str(Path.home() / "Dropbox" / "projector.db")

    output_path = Path(output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copy2(str(db.db_path), str(output_path))
        console.print(f"[green]✓[/green] Database exported to: {output_path}")

        # Log the export
        db_inst = Database()
        db_inst.init_schema()
        cursor = db_inst.connect().cursor()
        cursor.execute(
            """INSERT INTO sync_log (synced_at, remote, direction, rows_sent, rows_received, conflicts)
               VALUES (datetime('now'), ?, 'export', 0, 0, 0)""",
            (str(output_path),),
        )
        db_inst.commit()

    except Exception as e:
        console.print(f"[red]✗[/red] Error during export: {e}")
        raise typer.Exit(1)
