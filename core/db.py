"""
Database setup and migration runner.

Usage
-----
init_db()  — call once at startup; applies schema.sql + pending migrations.

Migrations
----------
Each file in core/migrations/ is a Python module with a `migrate(conn)` function.
Files are named with a timestamp prefix so they sort naturally:

    YYYYMMDD_HHMMSS_short_description.py

Only files with a name *greater* than the content of core/SCHEMA_VERSION.txt are
applied, in sorted order. After a successful run, SCHEMA_VERSION.txt is updated
to the name of the last applied migration.

To create a new migration:

    python scripts/generate_migration.py <description>

See also
--------
- AGENTS.md — development workflow
"""

import importlib
import importlib.util
import sqlite3

from pathlib import Path

from core.config import HOME_OS_DB_PATH

_SCHEMA = Path(__file__).parent / "schema.sql"
_MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_SCHEMA_VERSION_FILE = Path(__file__).parent / "SCHEMA_VERSION.txt"


def get_connection() -> sqlite3.Connection:
    Path(HOME_OS_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(HOME_OS_DB_PATH)  # fmt: skip
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _current_schema_version() -> str:
    if not _SCHEMA_VERSION_FILE.is_file():
        return ""
    return _SCHEMA_VERSION_FILE.read_text(encoding="utf-8").strip()


def _write_schema_version(version: str) -> None:
    _SCHEMA_VERSION_FILE.write_text(version.strip() + "\n", encoding="utf-8")


def run_migrations() -> None:
    """Apply any migration files that are newer than the stored schema version.

    Migrations are applied inside a single connection. After all pending
    migrations succeed, the SCHEMA_VERSION file is updated. If a migration
    fails, the file is NOT updated and the connection is rolled back.
    """
    if not _MIGRATIONS_DIR.is_dir():
        return
    current = _current_schema_version()
    migrations = sorted(
        p for p in _MIGRATIONS_DIR.iterdir() if p.suffix == ".py" and not p.stem.startswith("_")
    )
    if not migrations:
        return
    last_applied = current
    pending = [p for p in migrations if p.name > current] if current else migrations
    if not pending:
        return
    with get_connection() as conn:
        for path in pending:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.migrate(conn)
            last_applied = path.name
    _write_schema_version(last_applied)


def init_db() -> None:
    """Initialise the database and run any pending migrations.

    1. Ensure the database file and directory exist.
    2. Execute schema.sql (idempotent — uses IF NOT EXISTS everywhere).
    3. Run ``run_migrations()`` to apply outstanding versioned changes.
    """
    with get_connection() as conn:
        conn.executescript(_SCHEMA.read_text(encoding="utf-8"))
    run_migrations()
