import sqlite3

from core.db import get_connection
from core.utils.date import get_today, to_db_date
from core.utils.string import normalize_string
from modules.users.errors import UserAlreadyExistsError
from modules.users.types import User, UserRole

_USER_COLUMNS = "id, name, role, password_hash, telegram_chat_id, deleted_at"

EDITABLE_USER_COLUMNS = {"name", "password_hash", "telegram_chat_id"}


def _row_to_user(row) -> User:
    return User(
        row["id"],
        row["name"],
        row["role"],
        row["password_hash"],
        row["telegram_chat_id"],
        row["deleted_at"],
    )


def create_user(user_name: str, role: str = UserRole.MEMBER) -> User:
    normalized_user_name = normalize_string(user_name)
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO users (name, role)
                VALUES (?, ?)
                """,
                (normalized_user_name, role),
            )
        return get_active_user_by_id(cur.lastrowid)

    except sqlite3.IntegrityError as e:
        user = get_user_by_name(normalized_user_name)
        raise UserAlreadyExistsError(user) from e


def get_users() -> list[User]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_USER_COLUMNS}
            FROM users
            ORDER BY id
            """
        ).fetchall()
    return [_row_to_user(r) for r in rows]


def get_active_users() -> list[User]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_USER_COLUMNS}
            FROM users
            WHERE deleted_at IS NULL
            ORDER BY id
            """
        ).fetchall()
    return [_row_to_user(r) for r in rows]


def get_user_by_name(user_name: str) -> User | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_USER_COLUMNS}
            FROM users
            WHERE name = ?
            """,
            (user_name,),
        ).fetchone()
    return _row_to_user(row) if row else None


def get_active_user_by_id(user_id: int) -> User | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_USER_COLUMNS}
            FROM users
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (user_id,),
        ).fetchone()
    return _row_to_user(row) if row else None


def get_active_user_by_name(user_name: str) -> User | None:
    normalized_user_name = normalize_string(user_name)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_USER_COLUMNS}
            FROM users
            WHERE name = ?
              AND deleted_at IS NULL
            """,
            (normalized_user_name,),
        ).fetchone()
    return _row_to_user(row) if row else None


def get_active_user_by_telegram_chat_id(telegram_chat_id: str) -> User | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_USER_COLUMNS}
            FROM users
            WHERE telegram_chat_id = ?
              AND deleted_at IS NULL
            """,
            (telegram_chat_id,),
        ).fetchone()
    return _row_to_user(row) if row else None


def update_user(user_id: int, **fields: str | int | None) -> bool:
    if not fields:
        return True

    invalid = set(fields) - EDITABLE_USER_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable user columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()
    if "name" in normalized_fields and normalized_fields["name"] is not None:
        normalized_fields["name"] = normalize_string(normalized_fields["name"])

    set_clauses: list[str] = []
    params: list[str | int | None] = []
    for column, value in normalized_fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)
    params.append(user_id)

    try:
        with get_connection() as conn:
            cur = conn.execute(
                f"""
                UPDATE users
                SET {", ".join(set_clauses)}
                WHERE id = ?
                """,
                params,
            )
        return cur.rowcount > 0

    except sqlite3.IntegrityError as e:
        user = get_user_by_name(normalized_fields["name"])
        assert user is not None
        raise UserAlreadyExistsError(user) from e


def delete_user(user_id: int) -> bool:
    deleted_at = to_db_date(get_today())
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE users
            SET deleted_at = ?
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (deleted_at, user_id),
        )
    return cur.rowcount > 0
