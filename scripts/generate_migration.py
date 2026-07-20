import sys

from datetime import datetime
from pathlib import Path

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "core" / "migrations"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if not args:
        print("Usage: python scripts/generate_migration.py <description>")
        print("  e.g. python scripts/generate_migration.py add_email_to_users")
        return 1

    description = args[0].strip().lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{description}.py"
    path = _MIGRATIONS_DIR / filename

    if path.exists():
        print(f"Migration already exists: {filename}")
        return 1

    template = """def migrate(conn):
    pass
"""
    path.write_text(template, encoding="utf-8")
    print(f"Created: {path.relative_to(_MIGRATIONS_DIR.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
