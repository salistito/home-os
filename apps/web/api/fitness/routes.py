import json
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.fitness.responses import (
    error_response,
    serialize_exercise,
    serialize_exercise_entry,
    serialize_routine,
    serialize_routine_exercise,
    serialize_stats,
    serialize_weight_entry,
)
from apps.web.api.parsing import parse_int_param, parse_request_body
from apps.web.api.responses import bad_request
from modules.fitness.service import (
    create_exercise,
    create_routine,
    delete_exercise,
    delete_exercise_entry,
    delete_routine,
    delete_weight_entry,
    get_exercise_name_map,
    get_fitness_stats,
    get_routine_details,
    get_routine_name_map,
    list_exercise_entries,
    list_exercises,
    list_routines,
    list_weight_entries,
    log_exercise,
    log_weight,
    replace_routine_exercises,
    update_exercise,
    update_exercise_entry,
    update_routine,
    update_weight_entry,
)
from modules.fitness.types import FitnessOperationStatus


# Exercises
async def create_exercise_handler(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    result = create_exercise(body.get("name"), body.get("kind"))
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_exercise(result.exercise), status_code=HTTPStatus.CREATED)


async def list_exercises_handler(request: Request) -> Response:
    exercises = list_exercises()
    return JSONResponse([serialize_exercise(e) for e in exercises])


async def update_exercise_handler(request: Request) -> Response:
    exercise_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    allowed = ("name", "kind")
    fields = {key: body[key] for key in allowed if key in body}
    if not fields:
        return bad_request("At least one editable field must be provided.")

    result = update_exercise(exercise_id, **fields)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_exercise(result.exercise))


async def delete_exercise_handler(request: Request) -> Response:
    exercise_id = request.path_params["id"]
    result = delete_exercise(exercise_id)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_exercise(result.exercise))


# Routines
async def create_routine_handler(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    result = create_routine(
        name=body.get("name"),
        category=body.get("category"),
        description=body.get("description"),
        exercises=body.get("exercises"),
    )
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)

    routine_data = serialize_routine(result.routine)
    routine_data["exercises"] = [serialize_routine_exercise(re) for re in result.routine_exercises]
    return JSONResponse(routine_data, status_code=HTTPStatus.CREATED)


async def get_routine_handler(request: Request) -> Response:
    routine_id = request.path_params["id"]
    result = get_routine_details(routine_id)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)

    exercise_names = get_exercise_name_map()
    routine_data = serialize_routine(result.routine)
    routine_data["exercises"] = [
        {**serialize_routine_exercise(re), "exercise_name": exercise_names.get(re.exercise_id)}
        for re in result.routine_exercises
    ]
    return JSONResponse(routine_data)


async def list_routines_handler(request: Request) -> Response:
    routines = list_routines()
    exercise_names = get_exercise_name_map()

    result = []
    for routine in routines:
        routine_exercises = get_routine_details(routine.id).routine_exercises
        routine_data = serialize_routine(routine)
        routine_data["exercises"] = [
            {**serialize_routine_exercise(re), "exercise_name": exercise_names.get(re.exercise_id)}
            for re in routine_exercises
        ]
        result.append(routine_data)
    return JSONResponse(result)


async def update_routine_handler(request: Request) -> Response:
    routine_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    allowed = ("name", "category", "description")
    fields = {key: body[key] for key in allowed if key in body}
    if not fields:
        return bad_request("At least one editable field must be provided.")

    result = update_routine(routine_id, **fields)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_routine(result.routine))


async def replace_routine_exercises_handler(request: Request) -> Response:
    routine_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    exercises = body.get("exercises")
    if exercises is None:
        return bad_request("exercises field is required.")

    result = replace_routine_exercises(routine_id, exercises)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)

    exercise_names = get_exercise_name_map()
    routine_data = serialize_routine(result.routine)
    routine_data["exercises"] = [
        {**serialize_routine_exercise(re), "exercise_name": exercise_names.get(re.exercise_id)}
        for re in result.routine_exercises
    ]
    return JSONResponse(routine_data)


async def delete_routine_handler(request: Request) -> Response:
    routine_id = request.path_params["id"]
    result = delete_routine(routine_id)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_routine(result.routine))


# Exercise Entries
async def log_exercise_handler(request: Request) -> Response:
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    result = log_exercise(
        user_id=user_id,
        exercise_id=body.get("exercise_id"),
        routine_id=body.get("routine_id"),
        duration_min=body.get("duration_min"),
        calories_burned=body.get("calories_burned"),
        sets_breakdown=body.get("sets_breakdown"),
        metrics=body.get("metrics"),
        notes=body.get("notes"),
        performed_at=body.get("performed_at"),
    )
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)

    exercise_names = get_exercise_name_map()
    routine_names = get_routine_name_map()

    return JSONResponse(
        serialize_exercise_entry(result.exercise_entry, exercise_names, routine_names),
        status_code=HTTPStatus.CREATED,
    )


async def list_exercise_entries_handler(request: Request) -> Response:
    user_id = request.state.user_id
    exercise_id = parse_int_param(request.query_params.get("exercise_id"))
    if exercise_id is False:
        return bad_request("exercise_id must be an integer.")
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    limit = parse_int_param(request.query_params.get("limit"))
    if limit is False:
        return bad_request("limit must be an integer.")
    exercise_entries = list_exercise_entries(user_id, exercise_id, from_date, to_date, limit)
    exercise_names = get_exercise_name_map()
    routine_names = get_routine_name_map()
    return JSONResponse(
        [serialize_exercise_entry(e, exercise_names, routine_names) for e in exercise_entries]
    )


async def update_exercise_entry_handler(request: Request) -> Response:
    entry_id = request.path_params["id"]
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    allowed = (
        "exercise_id",
        "routine_id",
        "duration_min",
        "calories_burned",
        "sets_breakdown",
        "performed_at",
        "notes",
        "metrics",
    )
    fields = {key: body[key] for key in allowed if key in body}
    if not fields:
        return bad_request("At least one editable field must be provided.")

    result = update_exercise_entry(entry_id, user_id, **fields)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    exercise_names = get_exercise_name_map()
    routine_names = get_routine_name_map()
    return JSONResponse(
        serialize_exercise_entry(result.exercise_entry, exercise_names, routine_names)
    )


async def delete_exercise_entry_handler(request: Request) -> Response:
    entry_id = request.path_params["id"]
    user_id = request.state.user_id
    result = delete_exercise_entry(entry_id, user_id)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    exercise_names = get_exercise_name_map()
    routine_names = get_routine_name_map()
    return JSONResponse(
        serialize_exercise_entry(result.exercise_entry, exercise_names, routine_names)
    )


# Weight Entries
async def log_weight_handler(request: Request) -> Response:
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    result = log_weight(
        user_id=user_id,
        weight_kg=body.get("weight_kg"),
        notes=body.get("notes"),
        measured_at=body.get("measured_at"),
    )
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_weight_entry(result.weight_entry), status_code=201)


async def list_weight_handler(request: Request) -> Response:
    user_id = request.state.user_id
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    weight_entries = list_weight_entries(user_id, from_date, to_date)
    return JSONResponse([serialize_weight_entry(e) for e in weight_entries])


async def update_weight_handler(request: Request) -> Response:
    entry_id = request.path_params["id"]
    user_id = request.state.user_id
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    allowed = ("weight_kg", "measured_at", "notes")
    fields = {key: body[key] for key in allowed if key in body}
    if not fields:
        return bad_request("At least one editable field must be provided.")

    result = update_weight_entry(entry_id, user_id, **fields)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_weight_entry(result.weight_entry))


async def delete_weight_handler(request: Request) -> Response:
    entry_id = request.path_params["id"]
    user_id = request.state.user_id
    result = delete_weight_entry(entry_id, user_id)
    if result.status is not FitnessOperationStatus.OK:
        return error_response(result.status)
    return JSONResponse(serialize_weight_entry(result.weight_entry))


# Stats
async def get_stats_handler(request: Request) -> Response:
    user_id = request.state.user_id
    return JSONResponse(serialize_stats(get_fitness_stats(user_id)))
