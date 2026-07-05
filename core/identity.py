from dataclasses import dataclass

from core.db import get_connection


@dataclass
class User:
    id: str
    name: str
    telegram_chat_id: str


def get_users() -> list[User]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, telegram_chat_id FROM users"
        ).fetchall()
    return [User(r["id"], r["name"], r["telegram_chat_id"]) for r in rows]


def get_user_by_chat_id(chat_id: str) -> User | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, telegram_chat_id FROM users WHERE telegram_chat_id = ?",
            (chat_id,),
        ).fetchone()
    if row is None:
        return None
    return User(row["id"], row["name"], row["telegram_chat_id"])
