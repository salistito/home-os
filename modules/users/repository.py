from core.db import get_connection
from modules.users.types import User

_USER_COLUMNS = "id, name, telegram_chat_id, password_hash"

_USER_COLUMNS_NO_PASSWORD = "id, name, telegram_chat_id"

EDITABLE_USER_COLUMNS = {"name", "telegram_chat_id", "password_hash"}


def _row_to_user(row) -> User:
    return User(
        row["id"],
        row["name"],
        row["telegram_chat_id"],
        row["password_hash"],
    )


def get_users() -> list[User]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_USER_COLUMNS_NO_PASSWORD}
            FROM users
            """
        ).fetchall()
    return [_row_to_user(r) for r in rows]


def get_user_by_id(user_id: str) -> User | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_USER_COLUMNS_NO_PASSWORD}
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    return _row_to_user(row) if row else None


def get_user_by_chat_id(chat_id: str) -> User | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_USER_COLUMNS_NO_PASSWORD}
            FROM users
            WHERE telegram_chat_id = ?
            """,
            (chat_id,),
        ).fetchone()
    return _row_to_user(row) if row else None


def get_password_hash(user_id: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT password_hash
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    return row["password_hash"] if row else None
