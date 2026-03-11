"""Database connection, schema initialization, and migrations."""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple, Any
from .config import get_db_path


class Database:
    """SQLite database connection and schema management."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        self.db_path = db_path or get_db_path()
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Establish database connection."""
        if self.conn is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def init_schema(self):
        """Initialize database schema."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            repo_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS worktrees (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            UNIQUE(project_id, name)
        );

        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            mandatory BOOLEAN DEFAULT 0,
            archived BOOLEAN DEFAULT 0,
            archived_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            UNIQUE(project_id, name)
        );

        CREATE TABLE IF NOT EXISTS commits (
            id INTEGER PRIMARY KEY,
            worktree_id INTEGER NOT NULL,
            sha TEXT NOT NULL,
            message TEXT,
            author TEXT,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            machine_id TEXT,
            FOREIGN KEY (worktree_id) REFERENCES worktrees(id),
            UNIQUE(worktree_id, sha)
        );

        CREATE TABLE IF NOT EXISTS check_results (
            id INTEGER PRIMARY KEY,
            commit_id INTEGER NOT NULL,
            check_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            comment TEXT,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            machine_id TEXT,
            FOREIGN KEY (commit_id) REFERENCES commits(id),
            FOREIGN KEY (check_id) REFERENCES checks(id),
            UNIQUE(commit_id, check_id)
        );

        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            remote TEXT,
            direction TEXT NOT NULL,
            rows_sent INTEGER DEFAULT 0,
            rows_received INTEGER DEFAULT 0,
            conflicts INTEGER DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS conflict_log (
            id INTEGER PRIMARY KEY,
            table_name TEXT NOT NULL,
            row_id INTEGER,
            conflict_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolution TEXT
        );
        """)

        conn.commit()

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return cursor."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

    def executemany(self, query: str, params: List[Tuple]):
        """Execute many queries."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(query, params)
        conn.commit()

    def commit(self):
        """Commit changes."""
        if self.conn:
            self.conn.commit()

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row."""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows."""
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def insert_and_get_id(self, table: str, **kwargs) -> int:
        """Insert a row and return its ID."""
        conn = self.connect()
        cursor = conn.cursor()

        columns = list(kwargs.keys())
        values = list(kwargs.values())
        placeholders = ", ".join("?" * len(columns))

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(query, values)
        conn.commit()

        return cursor.lastrowid
