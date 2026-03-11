"""Data models and row mappers."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    repo_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Worktree:
    id: Optional[int] = None
    project_id: int = 0
    name: str = ""
    path: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Check:
    id: Optional[int] = None
    project_id: int = 0
    name: str = ""
    description: Optional[str] = None
    mandatory: bool = False
    archived: bool = False
    archived_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class Commit:
    id: Optional[int] = None
    worktree_id: int = 0
    sha: str = ""
    message: Optional[str] = None
    author: Optional[str] = None
    logged_at: Optional[datetime] = None
    machine_id: Optional[str] = None


@dataclass
class CheckResult:
    id: Optional[int] = None
    commit_id: int = 0
    check_id: int = 0
    status: str = ""  # pass | fail | warn | skip
    comment: Optional[str] = None
    logged_at: Optional[datetime] = None
    machine_id: Optional[str] = None


@dataclass
class SyncLog:
    id: Optional[int] = None
    synced_at: Optional[datetime] = None
    remote: Optional[str] = None
    direction: str = ""  # import | export
    rows_sent: int = 0
    rows_received: int = 0
    conflicts: int = 0
    notes: Optional[str] = None


@dataclass
class ConflictLog:
    id: Optional[int] = None
    table_name: str = ""
    row_id: int = 0
    conflict_at: Optional[datetime] = None
    resolution: Optional[str] = None
