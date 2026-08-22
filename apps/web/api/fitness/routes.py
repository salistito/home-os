import json
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.fitness.responses import (
    error_response,
    serialize_exercise_entry,
    serialize_stats,
    serialize_weight_entry,
)
from apps.web.api.responses import bad_request
from modules.fitness.service import (
    create_exercise,
    delete_exercise,
    delete_weight_entry,
    get_stats,
    list_exercises,
    list_weight_entries,
    log_weight,
    update_exercise,
)
from modules.fitness.types import FitnessOperationStatus


def _parse_request_body(data: object) -> dict | None:
    if not isinstance(data, dict):
        return None
    return data


def _parse_int_param(value: str | None) -> int | None | bool:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return False


async def log_weight_handler(request: Request) -> Response:
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    result = log_weight(
        user_id,
        body.get("weight_kg"),
        measured_at=body.get("measured_at"),
        notes=body.get("notes"),
    )
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_weight_entry(result.weight_entry), status_code=201)


async def list_weight_handler(request: Request) -> Response:
    user_id = request.state.user_id
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    entries = list_weight_entries(user_id, from_date, to_date)
    return JSONResponse([serialize_weight_entry(e) for e in entries])


async def delete_weight_handler(request: Request) -> Response:
    entry_id = request.path_params["id"]
    user_id = request.state.user_id
    result = delete_weight_entry(entry_id, user_id)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_weight_entry(result.weight_entry))


async def create_exercise_handler(request: Request) -> Response:
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    result = create_exercise(
        user_id,
        body.get("exercise_type"),
        body.get("duration_min"),
        intensity=body.get("intensity"),
        calories_burned=body.get("calories_burned"),
        performed_at=body.get("performed_at"),
        notes=body.get("notes"),
        metrics=body.get("metrics"),
    )
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(
        serialize_exercise_entry(result.exercise_entry), status_code=HTTPStatus.CREATED
    )


async def list_exercises_handler(request: Request) -> Response:
    user_id = request.state.user_id
    exercise_type = request.query_params.get("type")
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    limit = _parse_int_param(request.query_params.get("limit"))
    if limit is False:
        return bad_request("limit must be an integer.")
    entries = list_exercises(user_id, exercise_type, from_date, to_date, limit)
    return JSONResponse([serialize_exercise_entry(e) for e in entries])


async def update_exercise_handler(request: Request) -> Response:
    entry_id = request.path_params["id"]
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = _parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    allowed = ("exercise_type", "duration_min", "intensity", "calories_burned", "performed_at",
               "notes", "metrics")
    fields = {key: body[key] for key in allowed if key in body}
    if not fields:
        return bad_request("At least one editable field must be provided.")

    result = update_exercise(entry_id, user_id, **fields)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_exercise_entry(result.exercise_entry))


async def delete_exercise_handler(request: Request) -> Response:
    entry_id = request.path_params["id"]
    user_id = request.state.user_id
    result = delete_exercise(entry_id, user_id)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_exercise_entry(result.exercise_entry))


async def get_stats_handler(request: Request) -> Response:
    user_id = request.state.user_id
    return JSONResponse(serialize_stats(get_stats(user_id)))
