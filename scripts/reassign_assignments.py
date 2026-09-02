import argparse
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.utils.date import get_today

DOCKER_DB = "/app/data/homeos.db"
HOST_DB = "~/apps/home-os/data/homeos.db"


def _default_db() -> str:
    env_db = os.environ.get("HOME_OS_DB_PATH", "").strip()
    if env_db:
        return env_db
    if Path(DOCKER_DB).exists():
        return DOCKER_DB
    return HOST_DB


def _get_today() -> str:
    return get_today().isoformat()


def _connect(db_path: str) -> sqlite3.Connection:
    path = Path(db_path).expanduser()
    if not path.exists():
        print(f"Error: database file not found: {path}", file=sys.stderr)
        raise SystemExit(1)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _users_by_name(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT id, name FROM users WHERE deleted_at IS NULL").fetchall()
    return {row["name"].lower(): row["id"] for row in rows}


def _tasks_by_name(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT id, name FROM tasks WHERE deleted_at IS NULL").fetchall()
    return {row["name"].lower(): row["id"] for row in rows}


def list_daily_assignments(conn: sqlite3.Connection, day: str) -> list[dict]:
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT a.id AS assignment_id, a.task_id, t.name AS task_name,
                   a.user_id, u.name AS user_name, a.points_awarded,
                   COALESCE(a.points_awarded, t.points) AS points,
                   a.status, a.source
            FROM assignments a
            JOIN tasks t ON t.id = a.task_id
            JOIN users u ON u.id = a.user_id
            WHERE a.assigned_at = ?
            ORDER BY a.user_id, a.id
            """,
            (day,),
        ).fetchall()
    ]


def print_board(assignments: list[dict]) -> None:
    if not assignments:
        print("  (no assignments for the day)")
        return
    width = max((len(str(a["assignment_id"])) for a in assignments), default=0)
    for a in assignments:
        done = "DONE" if a["status"] == "completed" else a["status"].upper()
        src = f"[{a['source']}]" if a["source"] != "task" else ""
        print(
            f"  id={a['assignment_id']:<{width}}  "
            f"{a['user_name']:<12}  {a['points']:>3} pts  "
            f"{done:<9} {src} {a['task_name']}"
        )


class Reassignment:
    def __init__(self, conn: sqlite3.Connection, day: str):
        self.conn = conn
        self.day = day
        self.users = _users_by_name(conn)
        self.tasks = _tasks_by_name(conn)
        self.history: list[dict] = []

    def _assignment_user_id(self, assignment_id: int) -> str | None:
        row = self.conn.execute(
            "SELECT user_id FROM assignments WHERE id = ?", (assignment_id,)
        ).fetchone()
        return row["user_id"] if row else None

    def _has_pending(self, task_id: int, exclude: int | None = None) -> bool:
        sql = "SELECT id FROM assignments WHERE task_id = ? AND status = 'pending'"
        params: list = [task_id]
        if exclude is not None:
            sql += " AND id != ?"
            params.append(exclude)
        return self.conn.execute(sql, params).fetchone() is not None

    def do_reassign(self, assignment_id: int, user_name: str) -> str | None:
        user_name_norm = user_name.strip().lower()
        if user_name_norm not in self.users:
            return f"Unknown user '{user_name}'"
        user_id = self.users[user_name_norm]
        previous = self._assignment_user_id(assignment_id)
        if previous is None:
            return f"Unknown assignment id {assignment_id}"
        if previous == user_id:
            return f"Assignment {assignment_id} is already assigned to '{user_name}'"
        try:
            self.conn.execute(
                "UPDATE assignments SET user_id = ? WHERE id = ?",
                (user_id, assignment_id),
            )
        except sqlite3.Error as e:
            return f"Database error: {e}"
        self.history.append(
            {"op": "reassign", "assignment_id": assignment_id, "prev_user": previous}
        )
        return None

    def do_delete(self, assignment_id: int) -> str | None:
        row = self.conn.execute(
            "SELECT task_id, status FROM assignments WHERE id = ?",
            (assignment_id,),
        ).fetchone()
        if row is None:
            return f"Unknown assignment id {assignment_id}"
        if row["status"] != "pending":
            return (
                f"Assignment {assignment_id} has status '{row['status']}'; "
                "only pending assignments can be deleted"
            )
        try:
            self.conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        except sqlite3.Error as e:
            return f"Database error: {e}"
        self.history.append(
            {"op": "delete", "assignment_id": assignment_id, "task_id": row["task_id"]}
        )
        return None

    def do_add(self, task_name: str, user_name: str) -> str | None:
        task_name_norm = task_name.strip().lower()
        if task_name_norm not in self.tasks:
            return f"Unknown task '{task_name}'"
        task_id = self.tasks[task_name_norm]
        user_name_norm = user_name.strip().lower()
        if user_name_norm not in self.users:
            return f"Unknown user '{user_name}'"
        user_id = self.users[user_name_norm]
        if self._has_pending(task_id):
            return f"Task '{task_name}' already has a pending assignment for the day"
        try:
            cur = self.conn.execute(
                """
                INSERT INTO assignments (task_id, user_id, assigned_at, status)
                VALUES (?, ?, ?, 'pending')
                """,
                (task_id, user_id, self.day),
            )
        except sqlite3.Error as e:
            return f"Database error: {e}"
        self.history.append(
            {
                "op": "add",
                "assignment_id": cur.lastrowid,
                "task_id": task_id,
            }
        )
        return None

    def undo(self) -> str | None:
        if not self.history:
            return "Nothing to undo"
        last = self.history.pop()
        if last["op"] in ("reassign",):
            self.conn.execute(
                "UPDATE assignments SET user_id = ? WHERE id = ?",
                (last["prev_user"], last["assignment_id"]),
            )
        elif last["op"] in ("add", "delete"):
            self.conn.execute("DELETE FROM assignments WHERE id = ?", (last["assignment_id"],))
        return f"Reverted: {last['op']} assignment {last['assignment_id']}"


def run_interactive(conn: sqlite3.Connection, day: str, db_path: str) -> int:
    reassignment = Reassignment(conn, day)
    print(f"Database: {Path(db_path).expanduser()}")
    print(f"Date: {day}\n")
    print("Current assignments for the day:")
    print_board(list_daily_assignments(conn, day))
    print()
    print("Commands:")
    print("  reassign <assignment_id> <user_name>  - change the assignee")
    print("  delete <assignment_id>               - delete a pending assignment")
    print("  add <task_name> <user_name>          - add a new pending assignment")
    print("  undo                                 - revert the last change")
    print("  show                                 - show the current table")
    print("  done                                 - apply changes and exit")
    print("  quit                                 - discard changes and exit")
    print()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nDiscarding changes.")
            return 1
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].lower()
        if cmd == "done":
            if reassignment.history:
                print_board(list_daily_assignments(conn, day))
                confirm = (
                    input(f"\nApply {len(reassignment.history)} change(s)? [y/N] ").strip().lower()
                )
                if confirm not in ("y", "yes"):
                    print("Discarding changes.")
                    return 1
            break
        if cmd == "quit":
            print("Discarding changes.")
            return 1
        if cmd == "show":
            print_board(list_daily_assignments(conn, day))
            continue
        if cmd == "undo":
            msg = reassignment.undo()
            print(msg)
            continue
        if cmd == "reassign" and len(parts) == 3:
            try:
                assignment_id = int(parts[1])
            except ValueError:
                print(f"Invalid assignment id: {parts[1]}")
                continue
            err = reassignment.do_reassign(assignment_id, parts[2])
        elif cmd == "delete" and len(parts) == 2:
            try:
                assignment_id = int(parts[1])
            except ValueError:
                print(f"Invalid assignment id: {parts[1]}")
                continue
            err = reassignment.do_delete(assignment_id)
        elif cmd == "add" and len(parts) == 3:
            err = reassignment.do_add(parts[1], parts[2])
        else:
            print("Invalid command. Type 'done' to apply, 'quit' to discard.")
            continue
        if err:
            print(f"Error: {err}")
        else:
            print("OK")

    changes = len(reassignment.history)
    if changes == 0:
        print("No changes made.")
        return 0

    print(f"\nApplying {changes} change(s)...")
    return apply_transaction(conn)


def run_noninteractive(conn: sqlite3.Connection, day: str, actions: list[str], db_path: str) -> int:
    reassignment = Reassignment(conn, day)
    print(f"Database: {Path(db_path).expanduser()}")
    print(f"Date: {day}")
    print("Applying changes...")

    for action in actions:
        parts = [p for p in action.split(":") if p != ""]
        op = parts[0].lower() if parts else ""
        if op == "reassign" and len(parts) == 3:
            try:
                assignment_id = int(parts[1])
            except ValueError:
                print(f"Error: invalid assignment id '{parts[1]}' in '{action}'", file=sys.stderr)
                return 1
            err = reassignment.do_reassign(assignment_id, parts[2])
        elif op == "delete" and len(parts) == 2:
            try:
                assignment_id = int(parts[1])
            except ValueError:
                print(f"Error: invalid assignment id '{parts[1]}' in '{action}'", file=sys.stderr)
                return 1
            err = reassignment.do_delete(assignment_id)
        elif op == "add" and len(parts) == 3:
            err = reassignment.do_add(parts[1], parts[2])
        else:
            print(f"Error: invalid action '{action}'", file=sys.stderr)
            return 1
        if err:
            print(f"Error: {err}", file=sys.stderr)
            return 1
        print(f"  {action} -> OK")

    if not reassignment.history:
        print("No changes made.")
        return 0

    print(f"Applying {len(reassignment.history)} change(s)...")
    return apply_transaction(conn)


def apply_transaction(conn: sqlite3.Connection) -> int:
    try:
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error applying changes: {e}", file=sys.stderr)
        return 1
    print("Changes applied successfully.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reassign daily assignments directly on the HomeOS DB (Raspberry Pi)"
    )
    parser.add_argument(
        "--db",
        default=_default_db(),
        help="Path to the SQLite database (default: auto-detected Docker/host path)",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Assignment date as YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--action",
        action="append",
        metavar="ACTION",
        help="Non-interactive action. Formats: "
        "reassign:<assignment_id>:<user_name>, "
        "delete:<assignment_id>, add:<task_name>:<user_name>. Repeatable.",
    )
    args = parser.parse_args()

    day = args.date if args.date else _get_today()

    conn = _connect(args.db)

    if args.action:
        code = run_noninteractive(conn, day, args.action, args.db)
    else:
        code = run_interactive(conn, day, args.db)

    conn.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
