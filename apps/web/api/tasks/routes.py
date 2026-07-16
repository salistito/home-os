import json
from datetime import date
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.responses import bad_request
from apps.web.api.tasks.responses import error_response, serialize_task
from modules.tasks.repository import EDITABLE_TASK_COLUMNS, get_active_tasks
from modules.tasks.service import (
    create_task,
    soft_delete_active_task,
    update_active_task,
)
from modules.tasks.types import TaskOperationStatus


def _parse_start_date(value: object) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


async def create(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    name = data.get("name")
    points = data.get("points")
    frequency_days = data.get("frequency_days")
    next_due_date_raw = data.get("next_due_date")

    if not isinstance(name, str):
        return bad_request("name is required.")
    if not isinstance(points, int) or isinstance(points, bool):
        return bad_request("points must be an integer.")
    if frequency_days is not None and (
        not isinstance(frequency_days, int) or isinstance(frequency_days, bool)
    ):
        return bad_request("frequency must be an integer.")

    next_due_date = None
    if next_due_date_raw is not None:
        next_due_date = _parse_start_date(next_due_date_raw)
        if next_due_date is None:
            return bad_request("start date must be in YYYY-MM-DD format.")

    result = create_task(name, points, frequency_days, next_due_date)
    if result.status is not TaskOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_task(result.task), status_code=HTTPStatus.CREATED)


async def list_tasks(request: Request) -> Response:
    tasks = get_active_tasks()
    return JSONResponse([serialize_task(t) for t in tasks])


async def update(request: Request) -> Response:
    task_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    fields = {k: v for k, v in data.items() if k in EDITABLE_TASK_COLUMNS}
    if not fields:
        return bad_request("no valid fields to update.")

    if "name" in fields and not isinstance(fields["name"], str):
        return bad_request("name must be a string.")
    if "points" in fields and (
        not isinstance(fields["points"], int) or isinstance(fields["points"], bool)
    ):
        return bad_request("points must be an integer.")
    if (
        "frequency_days" in fields
        and fields["frequency_days"] is not None
        and (
            not isinstance(fields["frequency_days"], int)
            or isinstance(fields["frequency_days"], bool)
        )
    ):
        return bad_request("frequency must be an integer.")
    if "next_due_date" in fields and fields["next_due_date"] is not None:
        if _parse_start_date(fields["next_due_date"]) is None:
            return bad_request("start date must be in YYYY-MM-DD format.")

    result = update_active_task(task_id, **fields)
    if result.status is not TaskOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_task(result.task))


async def delete(request: Request) -> Response:
    task_id = request.path_params["id"]
    result = soft_delete_active_task(task_id)
    if result.status is not TaskOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_task(result.task))
