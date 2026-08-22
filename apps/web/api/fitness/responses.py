from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.fitness.types import (
    ExerciseEntry,
    FitnessOperationStatus,
    FitnessStats,
    WeightEntry,
)

_STATUS_HTTP = {
    FitnessOperationStatus.INVALID_ID: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_WEIGHT: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_MEASURED_AT: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_EXERCISE_TYPE: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_DURATION: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_INTENSITY: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_CALORIES: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_PERFORMED_AT: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.INVALID_METRICS: HTTPStatus.BAD_REQUEST,
    FitnessOperationStatus.NOT_FOUND: HTTPStatus.NOT_FOUND,
}

_STATUS_MESSAGE = {
    FitnessOperationStatus.INVALID_ID: "Invalid entry ID.",
    FitnessOperationStatus.INVALID_WEIGHT: "Weight must be a number greater than 0.",
    FitnessOperationStatus.INVALID_MEASURED_AT: "measured_at must be an ISO date (YYYY-MM-DD).",
    FitnessOperationStatus.INVALID_EXERCISE_TYPE: (
        "exercise_type is required and must be a non-empty string."
    ),
    FitnessOperationStatus.INVALID_DURATION: "duration_min must be an integer between 1 and 1440.",
    FitnessOperationStatus.INVALID_INTENSITY: "intensity must be 'low', 'medium' or 'high'.",
    FitnessOperationStatus.INVALID_CALORIES: "calories_burned must be a non-negative number.",
    FitnessOperationStatus.INVALID_PERFORMED_AT: "performed_at must be an ISO date (YYYY-MM-DD).",
    FitnessOperationStatus.INVALID_METRICS: (
        "metrics must be a flat object of numbers or short strings "
        "(sets_breakdown must be a list of {weight_kg, reps, sets?})."
    ),
    FitnessOperationStatus.NOT_FOUND: "Not found.",
}


def error_response(status: FitnessOperationStatus) -> JSONResponse:
    return JSONResponse(
        {"error": status.value, "message": _STATUS_MESSAGE.get(status, "Unexpected error.")},
        status_code=_STATUS_HTTP.get(status, HTTPStatus.BAD_REQUEST),
    )


def serialize_weight_entry(entry: WeightEntry) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "weight_kg": entry.weight_kg,
        "measured_at": entry.measured_at,
        "notes": entry.notes,
        "created_at": entry.created_at,
    }


def serialize_exercise_entry(entry: ExerciseEntry) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "exercise_type": entry.exercise_type,
        "duration_min": entry.duration_min,
        "intensity": entry.intensity,
        "calories_burned": entry.calories_burned,
        "performed_at": entry.performed_at,
        "notes": entry.notes,
        "created_at": entry.created_at,
        "metrics": entry.metrics,
    }


def serialize_stats(stats: FitnessStats) -> dict:
    return {
        "latest_weight_kg": stats.latest_weight_kg,
        "latest_measured_at": stats.latest_measured_at,
        "weight_delta_7d": stats.weight_delta_7d,
        "weight_delta_30d": stats.weight_delta_30d,
        "minutes_last_7d": stats.minutes_last_7d,
        "sessions_last_7d": stats.sessions_last_7d,
        "minutes_last_30d": stats.minutes_last_30d,
        "sessions_last_30d": stats.sessions_last_30d,
        "by_type_last_30d": stats.by_type_last_30d,
    }
