import json
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.finances.responses import (
    bad_request,
    error_response,
    serialize_period,
)
from modules.finances.service import get_period, get_periods, open_period
from modules.finances.types import FinanceOperationStatus


async def create_period(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        data = {}

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    label = data.get("label")
    if label is not None and not isinstance(label, str):
        return bad_request("label must be a string.")

    result = open_period(label)
    if result.status is not FinanceOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_period(result.period), status_code=HTTPStatus.CREATED)


async def list_periods(request: Request) -> Response:
    periods = get_periods()
    return JSONResponse([serialize_period(p) for p in periods])


async def get_period_detail(request: Request) -> Response:
    period_id = request.path_params["id"]
    result = get_period(period_id)
    if result.status is not FinanceOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_period(result.period))
