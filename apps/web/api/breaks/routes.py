import json
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.breaks.responses import (
    error_forbidden,
    error_response,
    serialize_break_period,
    serialize_break_period_status,
)
from apps.web.api.parsing import parse_request_body
from apps.web.api.responses import bad_request
from core.utils.date import get_today
from modules.breaks.service import (
    create_break_period,
    delete_break_period,
    get_active_break_period_for_user,
    get_break_periods,
    update_break_period,
)
from modules.breaks.types import BreakPeriodOperationStatus
from modules.users.repository import get_active_user_by_id, get_users
from modules.users.types import UserRole


def _is_admin_requester(request: Request) -> bool:
    requester = get_active_user_by_id(request.state.user_id)
    return requester is not None and requester.role == UserRole.ADMIN


async def create_break_period_handler(request: Request) -> Response:
    if not _is_admin_requester(request):
        return error_forbidden()

    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    label = body.get("label")
    start_date = body.get("start_date")
    end_date = body.get("end_date")
    user_ids = body.get("user_ids")

    if label is not None and not isinstance(label, str):
        return bad_request("label must be a string.")
    if not isinstance(start_date, str):
        return bad_request("start_date is required and must be a string.")
    if end_date is not None and not isinstance(end_date, str):
        return bad_request("end_date must be a string.")
    if not isinstance(user_ids, list) or any(
        not isinstance(user_id, int) or isinstance(user_id, bool) for user_id in user_ids
    ):
        return bad_request("user_ids must be a list of integers.")

    result = create_break_period(label, start_date, end_date, user_ids)
    if result.status is not BreakPeriodOperationStatus.OK:
        return error_response(result.status)

    users_by_id = {user.id: user for user in get_users()}
    return JSONResponse(
        serialize_break_period(result.break_period, users_by_id),
        status_code=HTTPStatus.CREATED,
    )


async def list_break_periods_handler(request: Request) -> Response:
    if not _is_admin_requester(request):
        return error_forbidden()

    break_periods = get_break_periods()
    users_by_id = {user.id: user for user in get_users()}
    return JSONResponse(
        [serialize_break_period(break_period, users_by_id) for break_period in break_periods]
    )


async def get_break_period_status_handler(request: Request) -> Response:
    break_period = get_active_break_period_for_user(request.state.user_id, get_today())
    return JSONResponse(serialize_break_period_status(break_period))


async def update_break_period_handler(request: Request) -> Response:
    if not _is_admin_requester(request):
        return error_forbidden()

    break_period_id = request.path_params["id"]

    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    body = parse_request_body(data)
    if body is None:
        return bad_request("body must be a JSON object.")

    fields: dict[str, object] = {}
    for field in ("label", "start_date", "end_date", "user_ids"):
        if field in body:
            fields[field] = body[field]
    if not fields:
        return bad_request("no valid fields to update.")

    result = update_break_period(break_period_id, **fields)
    if result.status is not BreakPeriodOperationStatus.OK:
        return error_response(result.status)

    users_by_id = {user.id: user for user in get_users()}
    return JSONResponse(serialize_break_period(result.break_period, users_by_id))


async def delete_break_period_handler(request: Request) -> Response:
    if not _is_admin_requester(request):
        return error_forbidden()

    break_period_id = request.path_params["id"]
    result = delete_break_period(break_period_id)
    if result.status is not BreakPeriodOperationStatus.OK:
        return error_response(result.status)

    users_by_id = {user.id: user for user in get_users()}
    return JSONResponse(serialize_break_period(result.break_period, users_by_id))
