"""SQLite connection manager with automatic migration on first connect."""

import sqlite3
from pathlib import Path

_DB_PATH: Path | None = None
_initialized: bool = False

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def configure(db_path: str | Path) -> None:
    """Set the database path before the first connection."""
    global _DB_PATH, _initialized
    _DB_PATH = Path(db_path)
    _initialized = False


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection. Runs migrations on first call."""
    global _initialized
    if _DB_PATH is None:
        raise RuntimeError("Database not configured. Call configure() first.")
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if not _initialized:
        _run_migrations(conn)
        _initialized = True
    return conn


def _run_migrations(conn: sqlite3.Connection) -> None:
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for migration in migration_files:
        conn.executescript(migration.read_text(encoding="utf-8"))
    conn.commit()
