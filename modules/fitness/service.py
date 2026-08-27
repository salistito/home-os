from datetime import timedelta

from core.utils.date import get_today, is_isoformat_date, to_db_date
from core.utils.parser import normalize_optional_text
from core.utils.string import normalize_string
from core.utils.validation import is_positive_number, is_valid_id
from modules.fitness import repository
from modules.fitness.errors import WeightEntryDateConflictError
from modules.fitness.types import (
    Exercise,
    ExerciseEntry,
    FitnessOperationResult,
    FitnessOperationStatus,
    FitnessStats,
    Routine,
    WeightEntry,
)

_MAX_EXERCISE_NAME_LEN = 80
_MAX_EXERCISE_KIND_LEN = 40
_MAX_EXERCISE_DURATION_MIN = 1440

_MAX_ROUTINE_NAME_LEN = 80
_MAX_ROUTINE_CATEGORY_LEN = 40
_MAX_ROUTINE_DESCRIPTION_LEN = 500
_MAX_ROUTINE_EXERCISES = 50

_MAX_EXERCISE_SET_ROWS = 50
_MAX_SET_NAME_LEN = 60
_MAX_WEIGHT_KG = 500.0
_MAX_REPS = 1000
_MAX_SETS = 100

_MAX_METRICS_KEYS = 15
_MAX_METRIC_KEY_LEN = 40
_MAX_METRIC_STR_LEN = 50


def _validate_routine_exercises(exercises) -> list[dict] | None:
    if exercises is None:
        return []
    if not isinstance(exercises, list) or len(exercises) > _MAX_ROUTINE_EXERCISES:
        return None

    seen_exercise_ids: set[int] = set()
    parsed_exercises: list[dict] = []
    for i, item in enumerate(exercises):
        if not isinstance(item, dict):
            return None

        exercise_id = item.get("exercise_id")
        if (
            not isinstance(exercise_id, int)
            or isinstance(exercise_id, bool)
            or exercise_id <= 0
            or repository.get_exercise_by_id(exercise_id) is None
        ):
            return None

        if exercise_id in seen_exercise_ids:
            return None
        seen_exercise_ids.add(exercise_id)

        weight_kg = item.get("weight_kg")
        if weight_kg is not None and (
            not is_positive_number(weight_kg) or weight_kg > _MAX_WEIGHT_KG
        ):
            return None

        reps = item.get("reps")
        if not isinstance(reps, int) or isinstance(reps, bool) or reps <= 0 or reps > _MAX_REPS:
            return None

        sets_count = item.get("sets", 1)
        if (
            not isinstance(sets_count, int)
            or isinstance(sets_count, bool)
            or sets_count <= 0
            or sets_count > _MAX_SETS
        ):
            return None

        position = item.get("position")
        if position is not None:
            if not isinstance(position, int) or isinstance(position, bool) or position < 0:
                return None
        else:
            position = i

        parsed_exercises.append(
            {
                "exercise_id": exercise_id,
                "weight_kg": round(float(weight_kg), 2) if weight_kg is not None else None,
                "reps": reps,
                "sets": sets_count,
                "position": position,
            }
        )
    parsed_exercises.sort(key=lambda x: x["position"])

    for i, item in enumerate(parsed_exercises):
        item["position"] = i

    return parsed_exercises


def _validate_sets_breakdown(
    sets_breakdown, require_exercise_id: bool = False
) -> list[dict] | None:
    if not isinstance(sets_breakdown, list) or len(sets_breakdown) > _MAX_EXERCISE_SET_ROWS:
        return None
    parsed_sets: list[dict] = []
    for set in sets_breakdown:
        if not isinstance(set, dict):
            return None
        exercise_id = set.get("exercise_id")
        exercise_name = set.get("exercise_name")
        if not isinstance(exercise_name, str) or not exercise_name.strip():
            return None
        exercise_name = normalize_string(exercise_name)
        weight_kg = set.get("weight_kg")
        reps = set.get("reps")
        sets_count = set.get("sets", 1)
        if require_exercise_id or exercise_id is not None:
            if not is_valid_id(exercise_id):
                return None
        if len(exercise_name) > _MAX_SET_NAME_LEN:
            return None
        if weight_kg is not None and (
            not is_positive_number(weight_kg) or weight_kg > _MAX_WEIGHT_KG
        ):
            return None
        if not isinstance(reps, int) or isinstance(reps, bool) or reps <= 0 or reps > _MAX_REPS:
            return None
        if (
            not isinstance(sets_count, int)
            or isinstance(sets_count, bool)
            or sets_count <= 0
            or sets_count > _MAX_SETS
        ):
            return None

        parsed_sets.append(
            {
                "exercise_id": exercise_id,
                "exercise_name": exercise_name,
                "weight_kg": round(float(weight_kg), 2) if weight_kg is not None else None,
                "reps": reps,
                "sets": sets_count,
            }
        )
    return parsed_sets


def _validate_metrics(metrics) -> tuple[dict | None, bool]:
    if metrics is None:
        return {}, True
    if not isinstance(metrics, dict) or len(metrics) > _MAX_METRICS_KEYS:
        return None, False
    parsed_metrics: dict = {}
    for key, val in metrics.items():
        if not isinstance(key, str) or not key.strip() or len(key.strip()) > _MAX_METRIC_KEY_LEN:
            return None, False
        normalized_key = key.strip()
        if isinstance(val, bool):
            return None, False
        if isinstance(val, (int, float)):
            parsed_metrics[normalized_key] = round(float(val), 2)
        elif isinstance(val, str):
            text = val.strip()
            if not text or len(text) > _MAX_METRIC_STR_LEN:
                return None, False
            parsed_metrics[normalized_key] = text
        else:
            return None, False
    return parsed_metrics, True


def _resolve_date(
    date, status: FitnessOperationStatus
) -> tuple[str | None, FitnessOperationStatus]:
    if date is None:
        return to_db_date(get_today()), FitnessOperationStatus.OK
    if isinstance(date, str) and is_isoformat_date(date):
        return date, FitnessOperationStatus.OK
    return None, status


# Exercises
def create_exercise(name, kind=None) -> FitnessOperationResult:
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > _MAX_EXERCISE_NAME_LEN:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_NAME)
    name = name.strip()
    if repository.get_active_exercise_by_name(name) is not None:
        return FitnessOperationResult(status=FitnessOperationStatus.DUPLICATE_NAME)

    kind = normalize_optional_text(kind)
    if kind is not None and len(kind) > _MAX_EXERCISE_KIND_LEN:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_KIND)

    today = to_db_date(get_today())
    exercise = repository.create_exercise(name=name, kind=kind, created_at=today, updated_at=today)
    return FitnessOperationResult(exercise=exercise, status=FitnessOperationStatus.OK)


def list_exercises(include_deleted: bool = False) -> list[Exercise]:
    return repository.get_exercises(include_deleted=include_deleted)


def get_exercise_name_map() -> dict[int, str]:
    return {e.id: e.name for e in repository.get_exercises(include_deleted=True)}


def update_exercise(exercise_id, **fields) -> FitnessOperationResult:
    if not is_valid_id(exercise_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)

    exercise = repository.get_exercise_by_id(exercise_id)
    if exercise is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    updates: dict = {}
    if "name" in fields:
        value = fields["name"]
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value.strip()) > _MAX_EXERCISE_NAME_LEN
        ):
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_NAME)
        exercise_name = value.strip()
        existing = repository.get_active_exercise_by_name(exercise_name)
        if existing is not None and existing.id != exercise_id:
            return FitnessOperationResult(status=FitnessOperationStatus.DUPLICATE_NAME)
        updates["name"] = exercise_name

    if "kind" in fields:
        kind = normalize_optional_text(fields["kind"])
        if kind is not None and len(kind) > _MAX_EXERCISE_KIND_LEN:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_KIND)
        updates["kind"] = kind

    if updates:
        updates["updated_at"] = to_db_date(get_today())
        repository.update_exercise(exercise_id, **updates)

    updated_exercise = repository.get_exercise_by_id(exercise_id)
    if updated_exercise is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    return FitnessOperationResult(exercise=updated_exercise, status=FitnessOperationStatus.OK)


def delete_exercise(exercise_id) -> FitnessOperationResult:
    if not is_valid_id(exercise_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)
    exercise = repository.get_exercise_by_id(exercise_id)
    if exercise is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    repository.soft_delete_exercise(exercise_id)
    return FitnessOperationResult(exercise=exercise, status=FitnessOperationStatus.OK)


# Routines
def create_routine(name, category=None, description=None, exercises=None) -> FitnessOperationResult:
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > _MAX_ROUTINE_NAME_LEN:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_NAME)
    name = name.strip()
    if repository.get_active_routine_by_name(name) is not None:
        return FitnessOperationResult(status=FitnessOperationStatus.DUPLICATE_NAME)

    category = normalize_optional_text(category)
    if category is not None and len(category) > _MAX_ROUTINE_CATEGORY_LEN:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_CATEGORY)

    description = normalize_optional_text(description)
    if description is not None and len(description) > _MAX_ROUTINE_DESCRIPTION_LEN:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_DESCRIPTION)

    parsed_exercises = _validate_routine_exercises(exercises)
    if parsed_exercises is None:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_EXERCISES)

    today = to_db_date(get_today())
    routine = repository.create_routine(
        name=name, category=category, description=description, created_at=today, updated_at=today
    )

    if parsed_exercises:
        routine_exercises = repository.set_routine_exercises(routine.id, parsed_exercises)
    else:
        routine_exercises = []

    return FitnessOperationResult(
        routine=routine, routine_exercises=routine_exercises, status=FitnessOperationStatus.OK
    )


def list_routines(include_deleted: bool = False) -> list[Routine]:
    return repository.get_routines(include_deleted=include_deleted)


def get_routine_name_map() -> dict[int, str]:
    return {r.id: r.name for r in list_routines(include_deleted=True)}


def get_routine_details(routine_id) -> FitnessOperationResult:
    if not is_valid_id(routine_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_ID)

    routine = repository.get_routine_by_id(routine_id)
    if routine is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    routine_exercises = repository.get_routine_exercises(routine_id)
    return FitnessOperationResult(
        routine=routine, routine_exercises=routine_exercises, status=FitnessOperationStatus.OK
    )


def update_routine(routine_id, **fields) -> FitnessOperationResult:
    if not is_valid_id(routine_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_ID)

    routine = repository.get_routine_by_id(routine_id)
    if routine is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    updates: dict = {}
    if "name" in fields:
        value = fields["name"]
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value.strip()) > _MAX_ROUTINE_NAME_LEN
        ):
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_NAME)
        routine_name = value.strip()
        existing = repository.get_active_routine_by_name(routine_name)
        if existing is not None and existing.id != routine_id:
            return FitnessOperationResult(status=FitnessOperationStatus.DUPLICATE_NAME)
        updates["name"] = routine_name

    if "category" in fields:
        category = normalize_optional_text(fields["category"])
        if category is not None and len(category) > _MAX_ROUTINE_CATEGORY_LEN:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_CATEGORY)
        updates["category"] = category

    if "description" in fields:
        description = normalize_optional_text(fields["description"])
        if description is not None and len(description) > _MAX_ROUTINE_DESCRIPTION_LEN:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_DESCRIPTION)
        updates["description"] = description

    if updates:
        updates["updated_at"] = to_db_date(get_today())
        repository.update_routine(routine_id, **updates)

    updated_routine = repository.get_routine_by_id(routine_id)
    if updated_routine is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    return FitnessOperationResult(routine=updated_routine, status=FitnessOperationStatus.OK)


def replace_routine_exercises(routine_id, exercises) -> FitnessOperationResult:
    if not is_valid_id(routine_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_ID)

    routine = repository.get_routine_by_id(routine_id)
    if routine is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    parsed_exercises = _validate_routine_exercises(exercises)
    if parsed_exercises is None:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_EXERCISES)

    routine_exercises = repository.set_routine_exercises(routine_id, parsed_exercises)
    updated_routine = repository.get_routine_by_id(routine_id)
    return FitnessOperationResult(
        routine=updated_routine,
        routine_exercises=routine_exercises,
        status=FitnessOperationStatus.OK,
    )


def delete_routine(routine_id) -> FitnessOperationResult:
    if not is_valid_id(routine_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_ID)
    routine = repository.get_routine_by_id(routine_id)
    if routine is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    repository.soft_delete_routine(routine_id)
    return FitnessOperationResult(routine=routine, status=FitnessOperationStatus.OK)


# Exercise Entries
def log_exercise(
    user_id: int,
    exercise_id=None,
    routine_id=None,
    duration_min=None,
    calories_burned=None,
    sets_breakdown=None,
    metrics=None,
    notes=None,
    performed_at=None,
) -> FitnessOperationResult:
    has_exercise_id = is_valid_id(exercise_id)
    has_routine_id = is_valid_id(routine_id)

    if (not has_exercise_id and not has_routine_id) or has_exercise_id and has_routine_id:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)

    if has_exercise_id:
        if repository.get_exercise_by_id(exercise_id) is None:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_EXERCISE_ID)

    if has_routine_id:
        if repository.get_routine_by_id(routine_id) is None:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_ID)

    if duration_min is not None:
        if (
            not isinstance(duration_min, int)
            or isinstance(duration_min, bool)
            or duration_min <= 0
            or duration_min > _MAX_EXERCISE_DURATION_MIN
        ):
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION_MIN)

    if calories_burned is not None:
        if (
            not isinstance(calories_burned, (int, float))
            or isinstance(calories_burned, bool)
            or calories_burned < 0
        ):
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_CALORIES_BURNED)
        calories_burned = round(float(calories_burned), 1)

    parsed_sets = (
        _validate_sets_breakdown(sets_breakdown, require_exercise_id=has_routine_id)
        if sets_breakdown is not None
        else []
    )
    if parsed_sets is None:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_SETS_BREAKDOWN)

    parsed_metrics, valid_metrics = _validate_metrics(metrics)
    if not valid_metrics:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_METRICS)

    if duration_min is None and not parsed_sets:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION_MIN)

    resolved_notes = normalize_optional_text(notes)

    resolved_performed_at, status = _resolve_date(
        performed_at, FitnessOperationStatus.INVALID_PERFORMED_AT
    )
    if resolved_performed_at is None:
        return FitnessOperationResult(status=status)

    created_at = to_db_date(get_today())

    if has_exercise_id:
        entry = repository.create_exercise_entry(
            user_id=user_id,
            exercise_id=exercise_id,
            routine_id=None,
            duration_min=duration_min,
            calories_burned=calories_burned,
            sets_breakdown=parsed_sets,
            metrics=parsed_metrics,
            notes=resolved_notes,
            performed_at=resolved_performed_at,
            created_at=created_at,
        )
        return FitnessOperationResult(exercise_entry=entry, status=FitnessOperationStatus.OK)
    else:
        routine_exercises = repository.get_routine_exercises(routine_id)
        if not routine_exercises:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_EXERCISES)

        entry = repository.create_exercise_entry(
            user_id=user_id,
            exercise_id=None,
            routine_id=routine_id,
            duration_min=duration_min,
            calories_burned=calories_burned,
            sets_breakdown=parsed_sets,
            metrics=parsed_metrics,
            notes=resolved_notes,
            performed_at=resolved_performed_at,
            created_at=created_at,
        )
        return FitnessOperationResult(exercise_entry=entry, status=FitnessOperationStatus.OK)


def list_exercise_entries(
    user_id: int,
    exercise_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int | None = None,
) -> list[ExerciseEntry]:
    return repository.get_exercise_entries(user_id, exercise_id, from_date, to_date, limit)


def update_exercise_entry(entry_id, user_id: int, **fields) -> FitnessOperationResult:
    if not is_valid_id(entry_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)

    exercise_entry = repository.get_exercise_entry_by_id_and_user(entry_id, user_id)
    if exercise_entry is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    updates: dict = {}
    if "routine_id" in fields:
        routine_id = fields["routine_id"]
        if routine_id is not None:
            if not is_valid_id(routine_id) or repository.get_routine_by_id(routine_id) is None:
                return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ROUTINE_ID)
        updates["routine_id"] = routine_id

    if "exercise_id" in fields:
        exercise_id = fields["exercise_id"]
        if (
            not isinstance(exercise_id, int)
            or isinstance(exercise_id, bool)
            or exercise_id <= 0
            or repository.get_exercise_by_id(exercise_id) is None
        ):
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_EXERCISE_ID)
        updates["exercise_id"] = exercise_id

    if ("routine_id" in updates) and ("exercise_id" in updates):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)

    if "duration_min" in fields:
        duration_min = fields["duration_min"]
        if duration_min is not None:
            if (
                not isinstance(duration_min, int)
                or isinstance(duration_min, bool)
                or duration_min <= 0
                or duration_min > _MAX_EXERCISE_DURATION_MIN
            ):
                return FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION_MIN)
        updates["duration_min"] = duration_min

    if "calories_burned" in fields:
        calories_burned = fields["calories_burned"]
        if calories_burned is not None:
            if (
                not isinstance(calories_burned, (int, float))
                or isinstance(calories_burned, bool)
                or calories_burned < 0
            ):
                return FitnessOperationResult(status=FitnessOperationStatus.INVALID_CALORIES_BURNED)
            calories_burned = round(float(calories_burned), 1)
        updates["calories_burned"] = calories_burned

    if "sets_breakdown" in fields:
        routine_id = updates.get("routine_id", exercise_entry.routine_id)
        require_exercise_id = routine_id is not None
        parsed_sets = _validate_sets_breakdown(fields["sets_breakdown"] or [], require_exercise_id)
        if parsed_sets is None:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_SETS_BREAKDOWN)
        updates["sets_breakdown"] = parsed_sets

    if "metrics" in fields:
        parsed_metrics, valid_metrics = _validate_metrics(fields["metrics"])
        if not valid_metrics:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_METRICS)
        updates["metrics"] = parsed_metrics

    if "notes" in fields:
        updates["notes"] = normalize_optional_text(fields["notes"])

    if "performed_at" in fields:
        resolved_performed_at, status = _resolve_date(
            fields["performed_at"], FitnessOperationStatus.INVALID_PERFORMED_AT
        )
        if resolved_performed_at is None:
            return FitnessOperationResult(status=status)
        updates["performed_at"] = resolved_performed_at

    if updates:
        if "routine_id" in updates:
            updates["exercise_id"] = None
        elif "exercise_id" in updates:
            updates["routine_id"] = None
        resulting_duration = updates.get("duration_min", exercise_entry.duration_min)
        resulting_sets = updates.get("sets_breakdown", exercise_entry.sets_breakdown)
        if resulting_duration is None and not resulting_sets:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_DURATION_MIN)
        if not repository.update_exercise_entry(entry_id, user_id, **updates):
            return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    updated = repository.get_exercise_entry_by_id_and_user(entry_id, user_id)
    if updated is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    return FitnessOperationResult(exercise_entry=updated, status=FitnessOperationStatus.OK)


def delete_exercise_entry(entry_id, user_id: int) -> FitnessOperationResult:
    if not is_valid_id(entry_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)
    exercise_entry = repository.get_exercise_entry_by_id_and_user(entry_id, user_id)
    if exercise_entry is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    repository.delete_exercise_entry(entry_id, user_id)
    return FitnessOperationResult(exercise_entry=exercise_entry, status=FitnessOperationStatus.OK)


# Weight Entries
def log_weight(user_id: int, weight_kg, notes=None, measured_at=None) -> FitnessOperationResult:
    if not is_positive_number(weight_kg) or weight_kg > _MAX_WEIGHT_KG:
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_WEIGHT)

    resolved_measured_at, status = _resolve_date(
        measured_at, FitnessOperationStatus.INVALID_MEASURED_AT
    )
    if resolved_measured_at is None:
        return FitnessOperationResult(status=status)

    entry = repository.upsert_weight_entry(
        user_id=user_id,
        weight_kg=round(float(weight_kg), 2),
        notes=normalize_optional_text(notes),
        measured_at=resolved_measured_at,
        created_at=to_db_date(get_today()),
    )
    return FitnessOperationResult(weight_entry=entry, status=FitnessOperationStatus.OK)


def list_weight_entries(
    user_id: int, from_date: str | None = None, to_date: str | None = None
) -> list[WeightEntry]:
    return repository.get_weight_entries(user_id, from_date, to_date)


def update_weight_entry(entry_id, user_id: int, **fields) -> FitnessOperationResult:
    if not is_valid_id(entry_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)

    weight_entry = repository.get_weight_entry_by_id_and_user(entry_id, user_id)
    if weight_entry is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)

    updates: dict = {}
    if "weight_kg" in fields:
        weight_kg = fields["weight_kg"]
        if not is_positive_number(weight_kg) or weight_kg > _MAX_WEIGHT_KG:
            return FitnessOperationResult(status=FitnessOperationStatus.INVALID_WEIGHT)
        updates["weight_kg"] = round(float(weight_kg), 2)

    if "notes" in fields:
        updates["notes"] = normalize_optional_text(fields["notes"])

    if "measured_at" in fields:
        resolved_measured_at, status = _resolve_date(
            fields["measured_at"], FitnessOperationStatus.INVALID_MEASURED_AT
        )
        if resolved_measured_at is None:
            return FitnessOperationResult(status=status)
        existing_by_date = repository.get_weight_entry_by_user_and_date(
            user_id, resolved_measured_at
        )
        if existing_by_date is not None and existing_by_date.id != entry_id:
            return FitnessOperationResult(status=FitnessOperationStatus.DUPLICATE_DATE)
        updates["measured_at"] = resolved_measured_at

    if updates:
        try:
            repository.update_weight_entry(entry_id, user_id, **updates)
        except WeightEntryDateConflictError:
            return FitnessOperationResult(status=FitnessOperationStatus.DUPLICATE_DATE)

    updated_weight_entry = repository.get_weight_entry_by_id_and_user(entry_id, user_id)
    if updated_weight_entry is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    return FitnessOperationResult(
        weight_entry=updated_weight_entry, status=FitnessOperationStatus.OK
    )


def delete_weight_entry(entry_id, user_id: int) -> FitnessOperationResult:
    if not is_valid_id(entry_id):
        return FitnessOperationResult(status=FitnessOperationStatus.INVALID_ID)
    weight_entry = repository.get_weight_entry_by_id_and_user(entry_id, user_id)
    if weight_entry is None:
        return FitnessOperationResult(status=FitnessOperationStatus.NOT_FOUND)
    repository.delete_weight_entry(entry_id, user_id)
    return FitnessOperationResult(weight_entry=weight_entry, status=FitnessOperationStatus.OK)


# Stats
def _latest_weight_on_or_before(user_id: int, date_str: str) -> WeightEntry | None:
    weight_entries = repository.get_weight_entries(user_id, to_date=date_str)
    return weight_entries[0] if weight_entries else None


def _volume_totals(entries: list[ExerciseEntry]) -> tuple[float | None, int]:
    has_load = False
    volume_kg = 0.0
    total_reps = 0
    for e in entries:
        for row in e.sets_breakdown:
            weight = row.get("weight_kg")
            total_reps += row["reps"] * row["sets"]
            if weight is not None:
                has_load = True
                volume_kg += weight * row["reps"] * row["sets"]
    return (round(volume_kg, 1) if has_load else None), total_reps


def get_fitness_stats(user_id: int) -> FitnessStats:
    today = get_today()
    fitness_stats = FitnessStats()

    # 7d stats
    exercises_7d = repository.get_exercise_entries(
        user_id, from_date=to_db_date(today - timedelta(days=6)), to_date=to_db_date(today)
    )
    fitness_stats.sessions_last_7d, fitness_stats.minutes_last_7d = (
        len(exercises_7d),
        sum(e.duration_min or 0 for e in exercises_7d),
    )
    fitness_stats.volume_kg_last_7d, fitness_stats.reps_last_7d = _volume_totals(exercises_7d)

    # 30d stats
    exercises_30d = repository.get_exercise_entries(
        user_id, from_date=to_db_date(today - timedelta(days=29)), to_date=to_db_date(today)
    )
    fitness_stats.sessions_last_30d, fitness_stats.minutes_last_30d = (
        len(exercises_30d),
        sum(e.duration_min or 0 for e in exercises_30d),
    )
    fitness_stats.volume_kg_last_30d, fitness_stats.reps_last_30d = _volume_totals(exercises_30d)

    # Top exercise stats (usage count and usage minutes consolidated per exercise)
    exercise_names = get_exercise_name_map()
    by_exercise: dict[str, dict] = {}
    for entry in exercises_30d:
        if entry.exercise_id is not None:
            exercise_name = exercise_names.get(entry.exercise_id, f"#{entry.exercise_id}")
            exercise_stats = by_exercise.setdefault(exercise_name, {"count": 0, "minutes": 0})
            exercise_stats["count"] += 1
            exercise_stats["minutes"] += entry.duration_min or 0
        elif entry.routine_id is not None:
            for row in entry.sets_breakdown:
                exercise_id = row.get("exercise_id")
                if exercise_id is None:
                    continue
                exercise_name = exercise_names.get(exercise_id, f"#{exercise_id}")
                exercise_stats = by_exercise.setdefault(exercise_name, {"count": 0, "minutes": 0})
                exercise_stats["count"] += 1
    fitness_stats.by_exercise_last_30d = dict(
        sorted(by_exercise.items(), key=lambda kv: -kv[1]["count"])
    )

    # weight stats
    latest_weight = _latest_weight_on_or_before(user_id, to_db_date(today))
    if latest_weight is not None:
        fitness_stats.latest_weight_kg = latest_weight.weight_kg
        fitness_stats.latest_measured_at = latest_weight.measured_at
    for days, attr in ((7, "weight_delta_7d"), (30, "weight_delta_30d")):
        cutoff = to_db_date(today - timedelta(days=days))
        baseline_weight = repository.get_latest_weight_before(user_id, cutoff)
        if latest_weight is not None and baseline_weight is not None:
            setattr(
                fitness_stats, attr, round(latest_weight.weight_kg - baseline_weight.weight_kg, 2)
            )

    return fitness_stats
