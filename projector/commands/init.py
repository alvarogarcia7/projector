"""Initialize database command."""

from pathlib import Path
from rich.console import Console
from ..db import Database
from ..config import get_or_create_global_db_dir

console = Console()


def init_command(local: bool = False) -> None:
    """
    Initialize Projector database.

    By default creates ~/.projector/projector.db (global).
    Use --local to create .projector.db in current directory (per-repo).
    """
    if local:
        db_path = Path.cwd() / ".projector.db"
        db = Database(db_path)
        db.init_schema()
        console.print(f"[green]✓[/green] Local database initialized at {db_path}")
    else:
        db_dir = get_or_create_global_db_dir()
        db_path = db_dir / "projector.db"
        db = Database(db_path)
        db.init_schema()
        console.print(f"[green]✓[/green] Global database initialized at {db_path}")
