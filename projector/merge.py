"""Database merge and conflict resolution logic."""

import sqlite3
from datetime import datetime
from typing import Any, Dict

from .db import Database


class MergeManager:
    """Handles merging foreign databases into local database."""

    def __init__(self, local_db: Database, foreign_db_path: str):
        """Initialize merge manager."""
        self.local_db = local_db
        self.foreign_db_path = foreign_db_path
        self.stats = {
            "rows_sent": 0,
            "rows_received": 0,
            "conflicts": 0,
        }

    def import_db(self) -> Dict[str, Any]:
        """Import foreign database into local. Returns stats and conflicts."""
        foreign_conn = sqlite3.connect(self.foreign_db_path)
        foreign_conn.row_factory = sqlite3.Row
        foreign_cursor = foreign_conn.cursor()

        local_conn = self.local_db.connect()

        try:
            # Import projects (name-based matching)
            self._merge_projects(foreign_cursor, local_conn)

            # Import worktrees (project.name + worktree.name matching)
            self._merge_worktrees(foreign_cursor, local_conn)

            # Import checks (project.name + check.name matching)
            self._merge_checks(foreign_cursor, local_conn)

            # Import commits (worktree match + sha matching)
            self._merge_commits(foreign_cursor, local_conn)

            # Import check_results (commit + check matching)
            self._merge_check_results(foreign_cursor, local_conn)

            local_conn.commit()

            # Log the sync
            self._log_sync("import", self.foreign_db_path)

        finally:
            foreign_conn.close()

        return {
            "rows_received": self.stats["rows_received"],
            "rows_sent": self.stats["rows_sent"],
            "conflicts": self.stats["conflicts"],
        }

    def _merge_projects(self, foreign_cursor: sqlite3.Cursor, local_conn: sqlite3.Connection):
        """Merge projects table."""
        foreign_cursor.execute("SELECT * FROM projects")
        foreign_projects = foreign_cursor.fetchall()

        local_cursor = local_conn.cursor()

        for proj in foreign_projects:
            existing = local_cursor.execute(
                "SELECT id FROM projects WHERE name = ?",
                (proj["name"],),
            ).fetchone()

            if existing:
                # Project exists: check for conflicts (different timestamps)
                if proj["updated_at"] and existing[0]:
                    local_proj = local_cursor.execute(
                        "SELECT updated_at FROM projects WHERE id = ?", (existing[0],)
                    ).fetchone()
                    if local_proj[0] and proj["updated_at"] != local_proj[0]:
                        self.stats["conflicts"] += 1
                        self._log_conflict(
                            "projects",
                            existing[0],
                            f"Kept local version (updated at {local_proj[0]})",
                        )
            else:
                # Insert new project
                local_cursor.execute(
                    """INSERT INTO projects (name, description, repo_path, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        proj["name"],
                        proj["description"],
                        proj["repo_path"],
                        proj["created_at"],
                        proj["updated_at"],
                    ),
                )
                self.stats["rows_received"] += 1

    def _merge_worktrees(self, foreign_cursor: sqlite3.Cursor, local_conn: sqlite3.Connection):
        """Merge worktrees table."""
        foreign_cursor.execute("""
            SELECT w.*, p.name as project_name FROM worktrees w
            JOIN projects p ON w.project_id = p.id
        """)
        foreign_worktrees = foreign_cursor.fetchall()

        local_cursor = local_conn.cursor()

        for wt in foreign_worktrees:
            project_id = local_cursor.execute(
                "SELECT id FROM projects WHERE name = ?",
                (wt["project_name"],),
            ).fetchone()

            if not project_id:
                continue

            existing = local_cursor.execute(
                "SELECT id FROM worktrees WHERE project_id = ? AND name = ?",
                (project_id[0], wt["name"]),
            ).fetchone()

            if not existing:
                local_cursor.execute(
                    "INSERT INTO worktrees (project_id, name, path, created_at) VALUES (?, ?, ?, ?)",
                    (project_id[0], wt["name"], wt["path"], wt["created_at"]),
                )
                self.stats["rows_received"] += 1

    def _merge_checks(self, foreign_cursor: sqlite3.Cursor, local_conn: sqlite3.Connection):
        """Merge checks table."""
        foreign_cursor.execute("""
            SELECT c.*, p.name as project_name FROM checks c
            JOIN projects p ON c.project_id = p.id
        """)
        foreign_checks = foreign_cursor.fetchall()

        local_cursor = local_conn.cursor()

        for check in foreign_checks:
            project_id = local_cursor.execute(
                "SELECT id FROM projects WHERE name = ?",
                (check["project_name"],),
            ).fetchone()

            if not project_id:
                continue

            existing = local_cursor.execute(
                "SELECT id, archived FROM checks WHERE project_id = ? AND name = ?",
                (project_id[0], check["name"]),
            ).fetchone()

            if existing:
                # Propagate archive status if foreign is archived and local is not
                if check["archived"] and not existing[1]:
                    local_cursor.execute(
                        "UPDATE checks SET archived = 1, archived_at = ? WHERE id = ?",
                        (check["archived_at"], existing[0]),
                    )
                    self.stats["conflicts"] += 1
                    self._log_conflict("checks", existing[0], "Propagated archive status from foreign DB")
            else:
                local_cursor.execute(
                    """INSERT INTO checks (project_id, name, description, mandatory, archived, archived_at, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        project_id[0],
                        check["name"],
                        check["description"],
                        check["mandatory"],
                        check["archived"],
                        check["archived_at"],
                        check["created_at"],
                    ),
                )
                self.stats["rows_received"] += 1

    def _merge_commits(self, foreign_cursor: sqlite3.Cursor, local_conn: sqlite3.Connection):
        """Merge commits table."""
        foreign_cursor.execute("""
            SELECT c.*, w.name as worktree_name, p.name as project_name
            FROM commits c
            JOIN worktrees w ON c.worktree_id = w.id
            JOIN projects p ON w.project_id = p.id
        """)
        foreign_commits = foreign_cursor.fetchall()

        local_cursor = local_conn.cursor()

        for commit in foreign_commits:
            project_id = local_cursor.execute(
                "SELECT id FROM projects WHERE name = ?",
                (commit["project_name"],),
            ).fetchone()

            if not project_id:
                continue

            worktree_id = local_cursor.execute(
                "SELECT id FROM worktrees WHERE project_id = ? AND name = ?",
                (project_id[0], commit["worktree_name"]),
            ).fetchone()

            if not worktree_id:
                continue

            existing = local_cursor.execute(
                "SELECT id, logged_at FROM commits WHERE worktree_id = ? AND sha = ?",
                (worktree_id[0], commit["sha"]),
            ).fetchone()

            if existing:
                # Check for conflict (different logged_at)
                if commit["logged_at"] and existing[1] and commit["logged_at"] != existing[1]:
                    self.stats["conflicts"] += 1
                    self._log_conflict(
                        "commits",
                        existing[0],
                        f"Kept newer entry (local: {existing[1]}, foreign: {commit['logged_at']})",
                    )
            else:
                local_cursor.execute(
                    """INSERT INTO commits (worktree_id, sha, message, author, logged_at, machine_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        worktree_id[0],
                        commit["sha"],
                        commit["message"],
                        commit["author"],
                        commit["logged_at"],
                        commit["machine_id"],
                    ),
                )
                self.stats["rows_received"] += 1

    def _merge_check_results(self, foreign_cursor: sqlite3.Cursor, local_conn: sqlite3.Connection):
        """Merge check_results table."""
        foreign_cursor.execute("""
            SELECT cr.*, c.sha, w.name as worktree_name, p.name as project_name,
                   ch.name as check_name
            FROM check_results cr
            JOIN commits c ON cr.commit_id = c.id
            JOIN worktrees w ON c.worktree_id = w.id
            JOIN projects p ON w.project_id = p.id
            JOIN checks ch ON cr.check_id = ch.id
        """)
        foreign_results = foreign_cursor.fetchall()

        local_cursor = local_conn.cursor()

        for result in foreign_results:
            # Find matching local IDs
            project_id = local_cursor.execute(
                "SELECT id FROM projects WHERE name = ?",
                (result["project_name"],),
            ).fetchone()

            if not project_id:
                continue

            check_id = local_cursor.execute(
                "SELECT id FROM checks WHERE project_id = ? AND name = ?",
                (project_id[0], result["check_name"]),
            ).fetchone()

            if not check_id:
                continue

            worktree_id = local_cursor.execute(
                "SELECT id FROM worktrees WHERE project_id = ? AND name = ?",
                (project_id[0], result["worktree_name"]),
            ).fetchone()

            if not worktree_id:
                continue

            commit_id = local_cursor.execute(
                "SELECT id FROM commits WHERE worktree_id = ? AND sha = ?",
                (worktree_id[0], result["sha"]),
            ).fetchone()

            if not commit_id:
                continue

            existing = local_cursor.execute(
                "SELECT id FROM check_results WHERE commit_id = ? AND check_id = ?",
                (commit_id[0], check_id[0]),
            ).fetchone()

            if not existing:
                local_cursor.execute(
                    """INSERT INTO check_results (commit_id, check_id, status, comment, logged_at, machine_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        commit_id[0],
                        check_id[0],
                        result["status"],
                        result["comment"],
                        result["logged_at"],
                        result["machine_id"],
                    ),
                )
                self.stats["rows_received"] += 1

    def _log_sync(self, direction: str, remote: str):
        """Log the sync operation."""
        local_cursor = self.local_db.connect().cursor()
        local_cursor.execute(
            """INSERT INTO sync_log (synced_at, remote, direction, rows_sent, rows_received, conflicts)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(),
                remote,
                direction,
                self.stats["rows_sent"],
                self.stats["rows_received"],
                self.stats["conflicts"],
            ),
        )
        self.local_db.commit()

    def _log_conflict(self, table_name: str, row_id: int, resolution: str):
        """Log a conflict resolution."""
        local_cursor = self.local_db.connect().cursor()
        local_cursor.execute(
            "INSERT INTO conflict_log (table_name, row_id, conflict_at, resolution) VALUES (?, ?, ?, ?)",
            (table_name, row_id, datetime.now(), resolution),
        )
