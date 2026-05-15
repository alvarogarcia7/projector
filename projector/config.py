"""Configuration and path resolution for Projector."""

import os
from pathlib import Path


def _get_projector_dir() -> Path:
    """Get the local .projector directory path."""
    return Path.cwd() / ".projector"


def _get_env_path() -> Path:
    """Get the path to the .projector/.env file."""
    return _get_projector_dir() / ".env"


def _read_env() -> dict:
    """Read .projector/.env file as key-value pairs."""
    env_path = _get_env_path()
    if not env_path.exists():
        return {}
    result = {}
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    result[key.strip()] = value.strip()
    except Exception:
        pass
    return result


def _write_env(data: dict) -> None:
    """Write key-value pairs to .projector/.env file."""
    env_path = _get_env_path()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    with open(env_path, "w") as f:
        for key, value in data.items():
            f.write(f"{key}={value}\n")


def get_db_path() -> Path:
    """
    Resolve the database path.
    Local .projector/projector.db takes precedence over global ~/.projector/projector.db
    """
    local_db = _get_projector_dir() / "projector.db"
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
    return db_path.name == "projector.db" and db_path.parent == _get_projector_dir()


def has_local_projector_db() -> bool:
    """Check if current directory has a local projector database."""
    return (_get_projector_dir() / "projector.db").exists()


def get_project_from_config() -> str:
    """
    Try to detect the project name from .projector/.env in current directory.
    Returns the project name or None if not found.
    """
    env_data = _read_env()
    return env_data.get("PROJECT")


def get_worktree_from_config() -> str:
    """
    Try to detect the worktree name from .projector-worktree in current directory.
    Returns the worktree name or None if not found.
    """
    config_file = Path.cwd() / ".projector-worktree"
    if config_file.exists():
        try:
            with open(config_file) as f:
                return f.read().strip()
        except Exception:
            pass
    return None


def save_project_config(project_name: str) -> None:
    """Save the current project name to .projector/.env in current directory."""
    env_data = _read_env()
    env_data["PROJECT"] = project_name
    _write_env(env_data)


def save_worktree_config(worktree_name: str) -> None:
    """Save the current worktree name to .projector-worktree in current directory."""
    config_file = Path.cwd() / ".projector-worktree"
    with open(config_file, "w") as f:
        f.write(worktree_name)


def get_checks_bin_path() -> Path:
    """
    Get the path to the checks bin directory.
    Looks for bin/ directory in current working directory or parent directories.
    """
    current = Path.cwd()
    for _ in range(5):  # Search up to 5 directories up
        bin_dir = current / "bin"
        if bin_dir.exists() and bin_dir.is_dir():
            return bin_dir
        current = current.parent
    return None


def get_path_config() -> str:
    """
    Get the configured checks bin path from .projector/.env file.
    Returns the path or None if not configured.
    """
    env_data = _read_env()
    return env_data.get("CHECKS_BIN_PATH")


def save_path_config(bin_path: str) -> None:
    """Save the checks bin path to .projector/.env in current directory."""
    env_data = _read_env()
    env_data["CHECKS_BIN_PATH"] = bin_path
    _write_env(env_data)


def clear_path_config() -> None:
    """Clear the checks bin path configuration."""
    env_data = _read_env()
    if "CHECKS_BIN_PATH" in env_data:
        del env_data["CHECKS_BIN_PATH"]
        _write_env(env_data)


def apply_path_config() -> None:
    """
    Apply the configured checks bin path to the current environment.
    This adds the checks bin directory to the PATH.
    """
    bin_path = get_path_config()
    if bin_path:
        path = os.environ.get("PATH", "")
        if bin_path not in path.split(":"):
            os.environ["PATH"] = f"{bin_path}:{path}"
