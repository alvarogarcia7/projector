"""Configuration and path resolution for Projector."""

import os
from pathlib import Path


def get_db_path() -> Path:
    """
    Resolve the database path.
    Local .projector.db takes precedence over global ~/.projector/projector.db
    """
    local_db = Path.cwd() / ".projector.db"
    if local_db.exists():
        return local_db

    global_db = Path.home() / ".projector" / "projector.db"
    return global_db


def get_or_create_global_db_dir() -> Path:
    """Ensure the global projector directory exists."""
    db_dir = Path.home() / ".projector"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir


def is_local_db(db_path: Path) -> bool:
    """Check if a database is a local (in-repo) database."""
    return db_path.name == ".projector.db" and db_path.parent == Path.cwd()
