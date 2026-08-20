import sqlite3
import sys
from pathlib import Path

DEFAULT_DB_PATH = "~/apps/home-os/data/homeos.db"


def _print_table(cursor: sqlite3.Cursor, table: str) -> None:
    cursor.execute(f"SELECT count(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"--- {table} ({count} rows) ---")

    cursor.execute(f"SELECT * FROM {table} LIMIT 25")
    columns = [desc[0] for desc in cursor.description]
    print(f"  {columns}")
    for row in cursor.fetchall():
        print(f"  {row}")
    if count > 25:
        print(f"  ... and {count - 25} more rows")
    print()


def inspect_db(db_path: str) -> int:
    path = Path(db_path).expanduser()
    if not path.exists():
        print(f"File not found: {path}")
        return 1

    print(f"Database: {path}\n")
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}\n")

    for table in tables:
        if table == "sqlite_sequence":
            continue
        _print_table(cursor, table)

    conn.close()
    return 0


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH
    return inspect_db(path)


if __name__ == "__main__":
    raise SystemExit(main())
