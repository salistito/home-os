import json
import sqlite3

from core.db import get_connection
from core.utils.date import get_today, to_db_date
from core.utils.string import normalize_string
from modules.fitness.errors import ExerciseAlreadyExistsError, WeightEntryDateConflictError
from modules.fitness.types import Exercise, ExerciseEntry, WeightEntry

_EXERCISE_COLUMNS = "id, name, kind, created_at, updated_at, deleted_at"
_EXERCISE_ENTRY_COLUMNS = (
    "id, user_id, exercise_id, duration_min, calories_burned, "
    "sets_breakdown, metrics, notes, performed_at, created_at"
)
_WEIGHT_ENTRY_COLUMNS = "id, user_id, weight_kg, notes, measured_at, created_at"

EDITABLE_EXERCISE_COLUMNS = {"name", "kind", "updated_at"}
EDITABLE_EXERCISE_ENTRY_COLUMNS = {
    "exercise_id",
    "duration_min",
    "calories_burned",
    "sets_breakdown",
    "metrics",
    "notes",
    "performed_at",
}
EDITABLE_WEIGHT_ENTRY_COLUMNS = {"weight_kg", "notes", "measured_at"}


def _row_to_fitness_exercise(row) -> Exercise:
    return Exercise(
        row["id"],
        row["name"],
        row["kind"],
        row["created_at"],
        row["updated_at"],
        row["deleted_at"],
    )


def _row_to_exercise_entry(row) -> ExerciseEntry:
    return ExerciseEntry(
        row["id"],
        row["user_id"],
        row["exercise_id"],
        row["duration_min"],
        row["calories_burned"],
        json.loads(row["sets_breakdown"]) if row["sets_breakdown"] else [],
        json.loads(row["metrics"]) if row["metrics"] else {},
        row["notes"],
        row["performed_at"],
        row["created_at"],
    )


def _row_to_weight_entry(row) -> WeightEntry:
    return WeightEntry(
        row["id"],
        row["user_id"],
        row["weight_kg"],
        row["notes"],
        row["measured_at"],
        row["created_at"],
    )


# Exercises
def create_exercise(
    name: str,
    kind: str | None,
    created_at: str,
    updated_at: str,
) -> Exercise:
    normalized_exercise_name = normalize_string(name)
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO fitness_exercises (name, kind, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (normalized_exercise_name, kind, created_at, updated_at),
            )
        return get_exercise_by_id(cur.lastrowid)

    except sqlite3.IntegrityError as e:
        exercise = get_active_exercise_by_name(normalized_exercise_name)
        raise ExerciseAlreadyExistsError(exercise) from e


def get_exercise_by_id(exercise_id: int) -> Exercise | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_EXERCISE_COLUMNS}
            FROM fitness_exercises
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (exercise_id,),
        ).fetchone()
    return _row_to_fitness_exercise(row) if row else None


def get_active_exercise_by_name(name: str) -> Exercise | None:
    normalized_exercise_name = normalize_string(name)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_EXERCISE_COLUMNS}
            FROM fitness_exercises
            WHERE name = ?
              AND deleted_at IS NULL
            """,
            (normalized_exercise_name,),
        ).fetchone()
    return _row_to_fitness_exercise(row) if row else None


def get_exercises(include_deleted: bool = False) -> list[Exercise]:
    where = "" if include_deleted else "WHERE deleted_at IS NULL"
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_EXERCISE_COLUMNS}
            FROM fitness_exercises
            {where}
            ORDER BY name COLLATE NOCASE
            """,
        ).fetchall()
    return [_row_to_fitness_exercise(r) for r in rows]


def update_exercise(exercise_id: int, **fields) -> bool:
    if not fields:
        return True

    invalid = set(fields) - EDITABLE_EXERCISE_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable exercise columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()
    if "name" in normalized_fields and normalized_fields["name"] is not None:
        normalized_fields["name"] = normalize_string(normalized_fields["name"])

    set_clauses: list[str] = []
    params: list = []
    for column, value in normalized_fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)
    params.append(exercise_id)

    try:
        with get_connection() as conn:
            cur = conn.execute(
                f"""
                UPDATE fitness_exercises
                SET {", ".join(set_clauses)}
                WHERE id = ?
                  AND deleted_at IS NULL
                """,
                params,
            )
        return cur.rowcount > 0
    except sqlite3.IntegrityError as e:
        exercise = get_active_exercise_by_name(normalized_fields["name"])
        assert exercise is not None
        raise ExerciseAlreadyExistsError(exercise) from e


def soft_delete_exercise(exercise_id: int) -> bool:
    deleted_at = to_db_date(get_today())
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE fitness_exercises
            SET deleted_at = ?
            WHERE id = ?
              AND deleted_at IS NULL
            """,
            (deleted_at, exercise_id),
        )
    return cur.rowcount > 0


# Exercise Entries
def create_exercise_entry(
    user_id: int,
    exercise_id: int,
    duration_min: int | None,
    calories_burned: float | None,
    sets_breakdown: list | None,
    metrics: dict | None,
    notes: str | None,
    performed_at: str,
    created_at: str,
) -> ExerciseEntry:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO fitness_exercise_entries
                (user_id, exercise_id, duration_min, calories_burned, sets_breakdown,
                 metrics, notes, performed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                exercise_id,
                duration_min,
                calories_burned,
                json.dumps(sets_breakdown or [], ensure_ascii=False),
                json.dumps(metrics or {}, ensure_ascii=False),
                notes,
                performed_at,
                created_at,
            ),
        )
        entry_id = cur.lastrowid
    return get_exercise_entry_by_id_and_user(entry_id, user_id)


def get_exercise_entry_by_id_and_user(entry_id: int, user_id: int) -> ExerciseEntry | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_EXERCISE_ENTRY_COLUMNS}
            FROM fitness_exercise_entries
            WHERE id = ?
              AND user_id = ?
            """,
            (entry_id, user_id),
        ).fetchone()
    return _row_to_exercise_entry(row) if row else None


def get_exercise_entries(
    user_id: int,
    exercise_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int | None = None,
) -> list[ExerciseEntry]:
    clauses = ["user_id = ?"]
    params: list = [user_id]
    if exercise_id is not None:
        clauses.append("exercise_id = ?")
        params.append(exercise_id)
    if from_date is not None:
        clauses.append("performed_at >= ?")
        params.append(from_date)
    if to_date is not None:
        clauses.append("performed_at <= ?")
        params.append(to_date)
    sql_limit = "LIMIT ?" if limit is not None else ""
    if limit is not None:
        params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_EXERCISE_ENTRY_COLUMNS}
            FROM fitness_exercise_entries
            WHERE {" AND ".join(clauses)}
            ORDER BY performed_at DESC, id DESC
            {sql_limit}
            """,
            params,
        ).fetchall()
    return [_row_to_exercise_entry(r) for r in rows]


def update_exercise_entry(entry_id: int, user_id: int, **fields) -> bool:
    if not fields:
        return True

    invalid = set(fields) - EDITABLE_EXERCISE_ENTRY_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable entry columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()
    if "sets_breakdown" in normalized_fields:
        normalized_fields["sets_breakdown"] = json.dumps(
            normalized_fields["sets_breakdown"] or [], ensure_ascii=False
        )
    if "metrics" in normalized_fields:
        normalized_fields["metrics"] = json.dumps(
            normalized_fields["metrics"] or {}, ensure_ascii=False
        )

    set_clauses: list[str] = []
    params: list = []
    for column, value in normalized_fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)
    params.append(entry_id)
    params.append(user_id)

    with get_connection() as conn:
        cur = conn.execute(
            f"""
            UPDATE fitness_exercise_entries
            SET {", ".join(set_clauses)}
            WHERE id = ?
              AND user_id = ?
            """,
            params,
        )
    return cur.rowcount > 0


def delete_exercise_entry(entry_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM fitness_exercise_entries
            WHERE id = ?
              AND user_id = ?
            """,
            (entry_id, user_id),
        )
    return cur.rowcount > 0


# Weight Entries
def upsert_weight_entry(
    user_id: int,
    weight_kg: float,
    notes: str | None,
    measured_at: str,
    created_at: str,
) -> WeightEntry:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO fitness_weight_entries
                (user_id, weight_kg, notes, measured_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, measured_at) DO UPDATE SET
                weight_kg = excluded.weight_kg,
                notes = excluded.notes
            """,
            (user_id, weight_kg, notes, measured_at, created_at),
        )
    return get_weight_entry_by_user_and_date(user_id, measured_at)


def get_weight_entry_by_id_and_user(entry_id: int, user_id: int) -> WeightEntry | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_WEIGHT_ENTRY_COLUMNS}
            FROM fitness_weight_entries
            WHERE id = ?
              AND user_id = ?
            """,
            (entry_id, user_id),
        ).fetchone()
    return _row_to_weight_entry(row) if row else None


def get_weight_entry_by_user_and_date(user_id: int, measured_at: str) -> WeightEntry | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_WEIGHT_ENTRY_COLUMNS}
            FROM fitness_weight_entries
            WHERE user_id = ?
              AND measured_at = ?
            """,
            (user_id, measured_at),
        ).fetchone()
    return _row_to_weight_entry(row) if row else None


def get_weight_entries(
    user_id: int, from_date: str | None = None, to_date: str | None = None
) -> list[WeightEntry]:
    clauses = ["user_id = ?"]
    params: list = [user_id]
    if from_date is not None:
        clauses.append("measured_at >= ?")
        params.append(from_date)
    if to_date is not None:
        clauses.append("measured_at <= ?")
        params.append(to_date)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_WEIGHT_ENTRY_COLUMNS}
            FROM fitness_weight_entries
            WHERE {" AND ".join(clauses)}
            ORDER BY measured_at DESC, id DESC
            """,
            params,
        ).fetchall()
    return [_row_to_weight_entry(r) for r in rows]


def get_latest_weight_before(user_id: int, cutoff_date: str) -> WeightEntry | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_WEIGHT_ENTRY_COLUMNS}
            FROM fitness_weight_entries
            WHERE user_id = ?
              AND measured_at < ?
            ORDER BY measured_at DESC, id DESC
            LIMIT 1
            """,
            (user_id, cutoff_date),
        ).fetchone()
    return _row_to_weight_entry(row) if row else None


def update_weight_entry(entry_id: int, user_id: int, **fields) -> bool:
    if not fields:
        return True

    invalid = set(fields) - EDITABLE_WEIGHT_ENTRY_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable weight entry columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()

    set_clauses: list[str] = []
    params: list = []
    for column, value in normalized_fields.items():
        if value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = ?")
            params.append(value)
    params.append(entry_id)
    params.append(user_id)

    try:
        with get_connection() as conn:
            cur = conn.execute(
                f"""
                UPDATE fitness_weight_entries
                SET {", ".join(set_clauses)}
                WHERE id = ?
                  AND user_id = ?
                """,
                params,
            )
        return cur.rowcount > 0

    except sqlite3.IntegrityError as e:
        existing = get_weight_entry_by_user_and_date(user_id, normalized_fields["measured_at"])
        assert existing is not None
        raise WeightEntryDateConflictError(existing) from e


def delete_weight_entry(entry_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            DELETE FROM fitness_weight_entries
            WHERE id = ?
              AND user_id = ?
            """,
            (entry_id, user_id),
        )
    return cur.rowcount > 0
