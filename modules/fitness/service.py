from datetime import timedelta

from core.utils.date import get_today, is_isoformat_date, to_db_date
from modules.fitness import repository
from modules.fitness.types import (
    ExerciseEntry,
    ExerciseIntensity,
    FitnessOperationResult,
    FitnessOperationStatus,
    FitnessStats,
    WeightEntry,
)

_MAX_WEIGHT_KG = 500.0
_MAX_DURATION_MIN = 1440

_SETS_BREAKDOWN_KEY = "sets_breakdown"
_VOLUME_METRIC_KEY = "volume_kg"
_MAX_METRICS_KEYS = 15
_MAX_METRIC_KEY_LEN = 40
_MAX_METRIC_STR_LEN = 50
_MAX_SET_ROWS = 50
_MAX_SET_NAME_LEN = 60
_MAX_REPS = 1000
_MAX_SETS_PER_ROW = 100


def _is_positive_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _validate_sets_breakdown(value) -> list[dict] | None:
    if not isinstance(value, list) or not value or len(value) > _MAX_SET_ROWS:
        return None
    rows: list[dict] = []
    for raw in value:
        if not isinstance(raw, dict):
            return None
        weight_kg = raw.get("weight_kg")
        reps = raw.get("reps")
        sets_count = raw.get("sets", 1)
        if not _is_positive_number(weight_kg) or weight_kg > _MAX_WEIGHT_KG:
            return None
        if (
            not isinstance(reps, int)
            or isinstance(reps, bool)
            or reps <= 0
            or reps > _MAX_REPS
        ):
            return None
        if (
            not isinstance(sets_count, int)
            or isinstance(sets_count, bool)
            or sets_count <= 0
            or sets_count > _MAX_SETS_PER_ROW
        ):
            return None
        name = _clean_optional_text(raw.get("name"))
        if name is not None and len(name) > _MAX_SET_NAME_LEN:
            return None
        rows.append(
            {
                "name": name,
                "weight_kg": round(float(weight_kg), 2),
                "reps": reps,
                "sets": sets_count,
            }
        )
    return rows


def _validate_metrics(value) -> tuple[dict | None, bool]:
    if value is None:
        return {}, True
    if not isinstance(value, dict) or len(value) > _MAX_METRICS_KEYS:
        return None, False
    result: dict = {}
    for key, val in value.items():
        if (
            not isinstance(key, str)
            or not key.strip()
            or len(key.strip()) > _MAX_METRIC_KEY_LEN
        ):
            return None, False
        normalized_key = key.strip()
        if normalized_key == _SETS_BREAKDOWN_KEY:
            rows = _validate_sets_breakdown(val)
            if rows is None:
                return None, False
            result[normalized_key] = rows
            continue
        if isinstance(val, bool):
            return None, False
        if isinstance(val, (int, float)):
            result[normalized_key] = round(float(val), 2)
        elif isinstance(val, str):
            text = val.strip()
            if not text or len(text) > _MAX_METRIC_STR_LEN:
                return None, False
            result[normalized_key] = text
        else:
            return None, False
    rows = result.get(_SETS_BREAKDOWN_KEY)
    if rows is not None:
        volume = round(sum(r["weight_kg"] * r["reps"] * r["sets"] for r in rows), 1)
        result[_VOLUME_METRIC_KEY] = volume
    return result, True


def _resolve_date(
    value, status: FitnessOperationStatus
) -> tuple[str | None, FitnessOperationStatus]:
    if value is None:
        return to_db_date(get_today()), FitnessOperationStatus.OK
    if isinstance(value, str) and is_isoformat_date(value):
        return value, FitnessOperationStatus.OK
    return None, status


def _clean_optional_text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


_VALID_INTENSITIES = {i.value for i in ExerciseIntensity}


def _is_valid_intensity(value) -> bool:
    return value is None or (isinstance(value, str) and value in _VALID_INTENSITIES)


# Weight Entries
def log_weight(
    user_id: int,
    weight_kg,
    measured_at=None,
    notes=None,
) -> FitnessOperationResult:
    if not _is_positive_number(weight_kg) or weight_kg > _MAX_WEIGHT_KG:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_WEIGHT)

    resolved_date, status = _resolve_date(measured_at, FitnessOperationStatus.INVALID_MEASURED_AT)
    if resolved_date is None:
        return FitnessOperationResult(status=status)

    entry = repository.upsert_weight_entry(
        user_id=user_id,
        weight_kg=round(float(weight_kg), 2),
        measured_at=resolved_date,
        notes=_clean_optional_text(notes),
        created_at=to_db_date(get_today()),
    )
    return FitnessOperationResult(weight_entry=entry, status=FitnessOperationStatus.OK)


def list_weight_entries(
    user_id: int, from_date: str | None = None, to_date: str | None = None
) -> list[WeightEntry]:
    return repository.get_weight_entries(user_id, from_date, to_date)


def delete_weight_entry(entry_id, user_id: int) -> FitnessOperationResult:
    if not isinstance(entry_id, int) or entry_id <= 0:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)
    entry = repository.get_weight_entry_by_id_and_user(entry_id, user_id)
    if entry is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    repository.delete_weight_entry(entry_id, user_id)
    return FitnessOperationResult(weight_entry=entry, status=FitnessOperationStatus.OK)


# Exercise Entries
def create_exercise(
    user_id: int,
    exercise_type,
    duration_min,
    intensity=None,
    calories_burned=None,
    performed_at=None,
    notes=None,
    metrics=None,
) -> FitnessOperationResult:
    if not isinstance(exercise_type, str) or not exercise_type.strip():
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_EXERCISE_TYPE)
    if not isinstance(duration_min, int) or isinstance(duration_min, bool):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION)
    if duration_min <= 0 or duration_min > _MAX_DURATION_MIN:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION)

    if not _is_valid_intensity(intensity):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_INTENSITY)
    parsed_intensity = ExerciseIntensity(intensity) if intensity is not None else None

    if calories_burned is not None:
        if (
            not isinstance(calories_burned, (int, float))
            or isinstance(calories_burned, bool)
            or calories_burned < 0
        ):
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_CALORIES)
        calories_burned = round(float(calories_burned), 1)

    resolved_date, status = _resolve_date(performed_at, FitnessOperationStatus.INVALID_PERFORMED_AT)
    if resolved_date is None:
        return FitnessOperationResult(status=status)

    parsed_metrics, ok = _validate_metrics(metrics)
    if not ok:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_METRICS)

    entry = repository.create_exercise_entry(
        user_id=user_id,
        exercise_type=exercise_type.strip(),
        duration_min=duration_min,
        intensity=parsed_intensity.value if parsed_intensity else None,
        calories_burned=calories_burned,
        performed_at=resolved_date,
        notes=_clean_optional_text(notes),
        created_at=to_db_date(get_today()),
        metrics=parsed_metrics,
    )
    return FitnessOperationResult(exercise_entry=entry, status=FitnessOperationStatus.OK)


def list_exercises(
    user_id: int,
    exercise_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int | None = None,
) -> list[ExerciseEntry]:
    return repository.get_exercise_entries(user_id, exercise_type, from_date, to_date, limit)


def update_exercise(entry_id, user_id: int, **fields) -> FitnessOperationResult:
    if not isinstance(entry_id, int) or entry_id <= 0:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)
    entry = repository.get_exercise_entry_by_id_and_user(entry_id, user_id)
    if entry is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    updates: dict = {}
    if "exercise_type" in fields:
        value = fields["exercise_type"]
        if not isinstance(value, str) or not value.strip():
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_EXERCISE_TYPE)
        updates["exercise_type"] = value.strip()
    if "duration_min" in fields:
        value = fields["duration_min"]
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
            or value > _MAX_DURATION_MIN
        ):
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION)
        updates["duration_min"] = value
    if "intensity" in fields:
        value = fields["intensity"]
        if not _is_valid_intensity(value):
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_INTENSITY)
        updates["intensity"] = ExerciseIntensity(value).value if value is not None else None
    if "calories_burned" in fields:
        value = fields["calories_burned"]
        if value is not None:
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or value < 0
            ):
                return FitnessOperationResult(status=FitnessOperationStatus.INVALID_CALORIES)
            value = round(float(value), 1)
        updates["calories_burned"] = value
    if "performed_at" in fields:
        resolved, status = _resolve_date(
            fields["performed_at"], FitnessOperationStatus.INVALID_PERFORMED_AT
        )
        if resolved is None:
            return FitnessOperationResult(status=status)
        updates["performed_at"] = resolved
    if "notes" in fields:
        updates["notes"] = _clean_optional_text(fields["notes"])
    if "metrics" in fields:
        parsed_metrics, ok = _validate_metrics(fields["metrics"])
        if not ok:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_METRICS)
        updates["metrics"] = parsed_metrics

    if updates and not repository.update_exercise_entry(entry_id, user_id, **updates):
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    updated = repository.get_exercise_entry_by_id_and_user(entry_id, user_id)
    return FitnessOperationResult(exercise_entry=updated, status=FitnessOperationStatus.OK)


def delete_exercise(entry_id, user_id: int) -> FitnessOperationResult:
    if not isinstance(entry_id, int) or entry_id <= 0:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)
    entry = repository.get_exercise_entry_by_id_and_user(entry_id, user_id)
    if entry is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    repository.delete_exercise_entry(entry_id, user_id)
    return FitnessOperationResult(exercise_entry=entry, status=FitnessOperationStatus.OK)


# Stats
def get_stats(user_id: int) -> FitnessStats:
    today = get_today()
    stats = FitnessStats()

    latest = _latest_weight_on_or_before(user_id, to_db_date(today))
    if latest is not None:
        stats.latest_weight_kg = latest.weight_kg
        stats.latest_measured_at = latest.measured_at

    for days, attr in ((7, "weight_delta_7d"), (30, "weight_delta_30d")):
        cutoff = to_db_date(today - timedelta(days=days))
        baseline = repository.get_latest_weight_before(user_id, cutoff)
        if latest is not None and baseline is not None:
            setattr(stats, attr, round(latest.weight_kg - baseline.weight_kg, 2))

    exercises_7d = repository.get_exercise_entries(
        user_id, from_date=to_db_date(today - timedelta(days=6)), to_date=to_db_date(today)
    )
    stats.minutes_last_7d = sum(e.duration_min or 0 for e in exercises_7d)
    stats.sessions_last_7d = len(exercises_7d)

    exercises_30d = repository.get_exercise_entries(
        user_id, from_date=to_db_date(today - timedelta(days=29)), to_date=to_db_date(today)
    )
    stats.minutes_last_30d = sum(e.duration_min or 0 for e in exercises_30d)
    stats.sessions_last_30d = len(exercises_30d)
    by_type: dict[str, int] = {}
    for entry in exercises_30d:
        by_type[entry.exercise_type] = by_type.get(entry.exercise_type, 0) + (
            entry.duration_min or 0
        )
    stats.by_type_last_30d = dict(sorted(by_type.items(), key=lambda kv: -kv[1]))
    return stats


def _latest_weight_on_or_before(user_id: int, date_str: str) -> WeightEntry | None:
    entries = repository.get_weight_entries(user_id, to_date=date_str)
    return entries[0] if entries else None
