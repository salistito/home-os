import json

from core.db import get_connection
from modules.fitness.types import ExerciseEntry, ExerciseIntensity, WeightEntry

_WEIGHT_ENTRY_COLUMNS = "id, user_id, weight_kg, measured_at, notes, created_at"
_EXERCISE_ENTRY_COLUMNS = (
    "id, user_id, exercise_type, duration_min, intensity, calories_burned, "
    "performed_at, notes, created_at, metrics"
)

EDITABLE_EXERCISE_COLUMNS = {
    "exercise_type",
    "duration_min",
    "intensity",
    "calories_burned",
    "performed_at",
    "notes",
    "metrics",
}


def _row_to_weight_entry(row) -> WeightEntry:
    return WeightEntry(
        row["id"],
        row["user_id"],
        row["weight_kg"],
        row["measured_at"],
        row["notes"],
        row["created_at"],
    )


def _row_to_exercise_entry(row) -> ExerciseEntry:
    return ExerciseEntry(
        row["id"],
        row["user_id"],
        row["exercise_type"],
        row["duration_min"],
        ExerciseIntensity(row["intensity"]) if row["intensity"] else None,
        row["calories_burned"],
        row["performed_at"],
        row["notes"],
        row["created_at"],
        json.loads(row["metrics"]) if row["metrics"] else {},
    )


# Weight Entries
def upsert_weight_entry(
    user_id: int,
    weight_kg: float,
    measured_at: str,
    notes: str | None,
    created_at: str,
) -> WeightEntry:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO fitness_weight_entries
                (user_id, weight_kg, measured_at, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, measured_at) DO UPDATE SET
                weight_kg = excluded.weight_kg,
                notes = excluded.notes
            """,
            (user_id, weight_kg, measured_at, notes, created_at),
        )
    return get_weight_entry_by_date_and_user(measured_at, user_id)


def get_weight_entry_by_date_and_user(measured_at: str, user_id: int) -> WeightEntry | None:
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {_WEIGHT_ENTRY_COLUMNS}
            FROM fitness_weight_entries
            WHERE measured_at = ?
              AND user_id = ?
            """,
            (measured_at, user_id),
        ).fetchone()
    return _row_to_weight_entry(row) if row else None


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


# Exercise Entries
def create_exercise_entry(
    user_id: int,
    exercise_type: str,
    duration_min: int,
    intensity: str | None,
    calories_burned: float | None,
    performed_at: str,
    notes: str | None,
    created_at: str,
    metrics: dict | None = None,
) -> ExerciseEntry:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO fitness_exercise_entries
                (user_id, exercise_type, duration_min, intensity, calories_burned,
                 performed_at, notes, created_at, metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                exercise_type,
                duration_min,
                intensity,
                calories_burned,
                performed_at,
                notes,
                created_at,
                json.dumps(metrics or {}, ensure_ascii=False),
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
    exercise_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int | None = None,
) -> list[ExerciseEntry]:
    clauses = ["user_id = ?"]
    params: list = [user_id]
    if exercise_type is not None:
        clauses.append("exercise_type = ?")
        params.append(exercise_type)
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

    invalid = set(fields) - EDITABLE_EXERCISE_COLUMNS
    if invalid:
        raise ValueError(f"Invalid editable exercise columns: {', '.join(sorted(invalid))}")

    normalized_fields = fields.copy()
    if "metrics" in normalized_fields:
        normalized_fields["metrics"] = json.dumps(
            normalized_fields["metrics"] or {}, ensure_ascii=False
        )

    set_clauses: list[str] = []
    params: list = []
    for column, value in fields.items():
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
