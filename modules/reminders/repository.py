import sqlite3

from core.db import get_connection
from core.utils.date import get_today, to_db_date
from core.utils.string import normalize_string
from modules.reminders.errors import ReminderAlreadyExistsError
from modules.reminders.types import Reminder, ReminderRecurrence

_REMINDER_COLUMNS = (
    "id, user_id, message, trigger_at, trigger_time, recurrence, cron_job_id, created_at"
)

EDITABLE_REMINDER_COLUMNS = {"message", "trigger_at", "trigger_time", "recurrence", "cron_job_id"}

VALID_RECURRENCES = {"none", "daily", "weekly", "monthly", "yearly"}


def _row_to_reminder(row) -> Reminder:
    return Reminder(
        row["id"],
        row["user_id"],
        row["message"],
        row["trigger_at"],
        row["trigger_time"],
        ReminderRecurrence(row["recurrence"]),
        row["cron_job_id"],
        row["created_at"],
    )


def create_reminder(
    user_id: int,
    message: str,
    trigger_at: str,
    trigger_time: str | None,
    recurrence: ReminderRecurrence,
    cron_job_id: str | None,
) -> Reminder:
    normalized_message = normalize_string(message)
    created_at = to_db_date(get_today())
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO reminders (user_id, message, trigger_at, trigger_time, recurrence, cron_job_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    normalized_message,
                    trigger_at,
                    trigger_time,
                    recurrence.value,
                    cron_job_id,
                    created_at,
                ),
            )
        reminder_id = cur.lastrowid
        return get_reminder_by_id(reminder_id)

    except sqlite3.IntegrityError as e:
        reminder = get_reminder_by_message(normalized_message)
        raise ReminderAlreadyExistsError(reminder) from e


def get_reminder_by_id(reminder_id: int) -> Reminder | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_REMINDER_COLUMNS}
            FROM reminders
            WHERE id = ?
            """,
            (reminder_id,),
        ).fetchone()
    return _row_to_reminder(row) if row else None


def get_reminder_by_message(user_id: int, message: str) -> Reminder | None:
    normalized_message = normalize_string(message)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_REMINDER_COLUMNS}
            FROM reminders
            WHERE user_id = ?
              AND message = ?
            """,
            (user_id, normalized_message),
        ).fetchone()
    return _row_to_reminder(row) if row else None


def get_reminders() -> list[Reminder]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_REMINDER_COLUMNS}
            FROM reminders
            ORDER BY trigger_at, trigger_time
            """,
        ).fetchall()
    return [_row_to_reminder(r) for r in rows]


def get_user_reminders(user_id: int) -> list[Reminder]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_REMINDER_COLUMNS}
            FROM reminders
            WHERE user_id = ?
            ORDER BY trigger_at, trigger_time
            """,
            (user_id,),
        ).fetchall()
    return [_row_to_reminder(r) for r in rows]


def get_user_pending_reminders(user_id: int, today: str) -> list[Reminder]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_REMINDER_COLUMNS}
            FROM reminders
            WHERE user_id = ?
              AND (trigger_at > ? OR (trigger_at = ? AND trigger_time IS NOT NULL AND trigger_time > ?))
            ORDER BY trigger_at, trigger_time
            """,
            (user_id, today, today, "00:00"),
        ).fetchall()
    return [_row_to_reminder(r) for r in rows]


def get_due_day_reminders(date: str) -> list[Reminder]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_REMINDER_COLUMNS}
            FROM reminders
            WHERE trigger_at <= ? AND trigger_time IS NULL
            ORDER BY trigger_at
            """,
            (date,),
        ).fetchall()
    return [_row_to_reminder(r) for r in rows]


def get_due_timed_reminders(date: str, time: str) -> list[Reminder]:
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_REMINDER_COLUMNS}
            FROM reminders
            WHERE trigger_time IS NOT NULL
              AND (
                trigger_at < ?
                OR (trigger_at = ? AND trigger_time <= ?)
              )
            ORDER BY trigger_at, trigger_time
            """,
            (date, date, time),
        ).fetchall()
    return [_row_to_reminder(r) for r in rows]


def update_reminder(reminder_id: int, user_id: int, **fields: str | None) -> bool:
    if not fields:
        return True

    invalid = set(fields) - EDITABLE_REMINDER_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable reminder columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()

    if "message" in normalized_fields and normalized_fields["message"] is not None:
        normalized_fields["message"] = normalize_string(normalized_fields["message"])

    set_clauses: list[str] = []
    params: list[str | None] = []

    for column, value in normalized_fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)

    params.extend([reminder_id, user_id])

    try:
        with get_connection() as conn:
            cur = conn.execute(
                f"""
                UPDATE reminders
                SET {", ".join(set_clauses)}
                WHERE id = ? AND user_id = ?
                """,
                params,
            )
        return cur.rowcount > 0

    except sqlite3.IntegrityError as e:
        reminder = get_reminder_by_message(user_id, normalized_fields["message"])
        assert reminder is not None
        raise ReminderAlreadyExistsError(reminder) from e


def delete_reminder(reminder_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM reminders
            WHERE id = ?
              AND user_id = ?
            """,
            (reminder_id, user_id),
        )
    return cur.rowcount > 0


def update_reminder_cron_job_id(reminder_id: int, cron_job_id: str | None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE reminders
            SET cron_job_id = ?
            WHERE id = ?
            """,
            (cron_job_id, reminder_id),
        )
