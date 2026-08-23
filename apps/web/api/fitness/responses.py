from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.fitness.types import (
    Exercise,
    ExerciseEntry,
    FitnessOperationStatus,
    FitnessStats,
    WeightEntry,
)

_STATUS_HTTP = {
    FitnessOperationStatus.INVALID_ID: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_NAME: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.DUPLICATE_NAME: HTTPStatus.CONFLICT,
    FitnessOperationStatus.INVALID_KIND: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_EXERCISE_ID: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_DURATION_MIN: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_CALORIES_BURNED: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_SETS_BREAKDOWN: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_METRICS: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_PERFORMED_AT: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_WEIGHT: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_MEASURED_AT: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.DUPLICATE_DATE: HTTPStatus.CONFLICT,
    FitnessOperationStatus.NOT_FOUND: HTTPStatus.NOT_FOUND,
}

_STATUS_MESSAGE = {
    FitnessOperationStatus.INVALID_ID: "Invalid ID.",
    FitnessOperationStatus.INVALID_NAME: "name is required (max 80 characters).",
    FitnessOperationStatus.DUPLICATE_NAME: "An active exercise with that name already exists.",
    FitnessOperationStatus.INVALID_KIND: "kind must be a short text (max 40 characters).",
    FitnessOperationStatus.INVALID_EXERCISE_ID: (
        "exercise_id must reference an existing active exercise."
    ),
    FitnessOperationStatus.INVALID_DURATION_MIN: (
        "duration_min must be an integer between 1 and 1440, or sets_breakdown is required."
    ),
    FitnessOperationStatus.INVALID_CALORIES_BURNED: (
        "calories_burned must be a non-negative number."
    ),
    FitnessOperationStatus.INVALID_SETS_BREAKDOWN: (
        "sets_breakdown must be a list of rows {name?, weight_kg?, reps, sets}."
    ),
    FitnessOperationStatus.INVALID_METRICS: (
        "metrics must be a flat object of keys and numeric or short string values."
    ),
    FitnessOperationStatus.INVALID_PERFORMED_AT: "performed_at must be an ISO date (YYYY-MM-DD).",
    FitnessOperationStatus.INVALID_WEIGHT: "Weight must be a number greater than 0.",
    FitnessOperationStatus.INVALID_MEASURED_AT: "measured_at must be an ISO date (YYYY-MM-DD).",
    FitnessOperationStatus.DUPLICATE_DATE: "A weight entry for that date already exists.",
    FitnessOperationStatus.NOT_FOUND: "Not found.",
}


def serialize_exercise(exercise: Exercise) -> dict:
    return {
        "id": exercise.id,
        "name": exercise.name,
        "kind": exercise.kind,
        "created_at": exercise.created_at,
        "updated_at": exercise.updated_at,
        "deleted_at": exercise.deleted_at,
    }


def _derived_volume(entry: ExerciseEntry) -> tuple[float | None, int | None]:
    if not entry.sets_breakdown:
        return None, None
    has_load = False
    volume_kg = 0.0
    total_reps = 0
    for row in entry.sets_breakdown:
        weight = row.get("weight_kg")
        total_reps += row["reps"] * row["sets"]
        if weight is not None:
            has_load = True
            volume_kg += weight * row["reps"] * row["sets"]
    return (round(volume_kg, 1) if has_load else None), total_reps


def serialize_exercise_entry(
    entry: ExerciseEntry, names_by_id: dict[int, str] | None = None
) -> dict:
    names_by_id = names_by_id or {}
    volume_kg, total_reps = _derived_volume(entry)
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "exercise_id": entry.exercise_id,
        "exercise_name": names_by_id.get(entry.exercise_id),
        "duration_min": entry.duration_min,
        "calories_burned": entry.calories_burned,
        "sets_breakdown": entry.sets_breakdown,
        "volume_kg": volume_kg,
        "total_reps": total_reps,
        "metrics": entry.metrics,
        "notes": entry.notes,
        "performed_at": entry.performed_at,
        "created_at": entry.created_at,
    }


def serialize_weight_entry(entry: WeightEntry) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "weight_kg": entry.weight_kg,
        "notes": entry.notes,
        "measured_at": entry.measured_at,
        "created_at": entry.created_at,
    }


def serialize_stats(stats: FitnessStats) -> dict:
    return {
        "sessions_last_7d": stats.sessions_last_7d,
        "minutes_last_7d": stats.minutes_last_7d,
        "volume_kg_last_7d": stats.volume_kg_last_7d,
        "reps_last_7d": stats.reps_last_7d,
        "sessions_last_30d": stats.sessions_last_30d,
        "minutes_last_30d": stats.minutes_last_30d,
        "volume_kg_last_30d": stats.volume_kg_last_30d,
        "reps_last_30d": stats.reps_last_30d,
        "by_exercise_last_30d": stats.by_exercise_last_30d,
        "latest_weight_kg": stats.latest_weight_kg,
        "latest_measured_at": stats.latest_measured_at,
        "weight_delta_7d": stats.weight_delta_7d,
        "weight_delta_30d": stats.weight_delta_30d,
    }


def error_response(status: FitnessOperationStatus) -> JSONResponse:
    return JSONResponse(
        {"error": status.value, "message": _STATUS_MESSAGE.get(status, "Unexpected error.")},
        status_code=_STATUS_HTTP.get(status, HTTPStatus.BAD_REQUEST),
    )
