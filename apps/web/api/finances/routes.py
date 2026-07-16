import json
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.finances.responses import (
    bad_request,
    error_response,
    serialize_entry,
    serialize_period,
    serialize_period_detail,
)
from modules.finances.service import (
    add_entry,
    confirm_entry,
    delete_entry,
    get_period_detail,
    get_periods,
    list_entries,
    open_period,
    reject_entry,
    update_entry,
)
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


async def get_period_detail_endpoint(request: Request) -> Response:
    period_id = request.path_params["id"]
    result = get_period_detail(period_id)
    if result.status is not FinanceOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_period_detail(result.detail))


async def list_entries_endpoint(request: Request) -> Response:
    period_id_raw = request.query_params.get("period_id")
    if period_id_raw is None:
        return bad_request("period_id is required.")
    try:
        period_id = int(period_id_raw)
    except ValueError:
        return bad_request("period_id must be an integer.")

    entries = list_entries(period_id)
    return JSONResponse([serialize_entry(e) for e in entries])


async def create_entry(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    period_id = data.get("period_id")
    kind = data.get("kind")
    scope = data.get("scope")
    owner_id = data.get("owner_id")
    label = data.get("label")
    amount = data.get("amount")

    if not isinstance(period_id, int) or isinstance(period_id, bool):
        return bad_request("period_id must be an integer.")
    if not isinstance(kind, str):
        return bad_request("kind is required.")
    if not isinstance(scope, str):
        return bad_request("scope is required.")
    if not isinstance(owner_id, str):
        return bad_request("owner_id is required.")
    if not isinstance(label, str):
        return bad_request("label is required.")
    if not isinstance(amount, int) or isinstance(amount, bool):
        return bad_request("amount must be an integer.")

    result = add_entry(period_id, kind, scope, owner_id, label, amount)
    if result.status is not FinanceOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_entry(result.entry), status_code=HTTPStatus.CREATED)


def _parse_details(raw) -> list[tuple[str, int]] | None:
    if not isinstance(raw, list):
        return None
    details: list[tuple[str, int]] = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        label = item.get("label")
        amount = item.get("amount")
        if not isinstance(label, str):
            return None
        if not isinstance(amount, int) or isinstance(amount, bool):
            return None
        details.append((label, amount))
    return details


async def update_entry_endpoint(request: Request) -> Response:
    entry_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    fields: dict = {}

    if "label" in data:
        if not isinstance(data["label"], str):
            return bad_request("label must be a string.")
        fields["label"] = data["label"]

    if "owner_id" in data:
        if not isinstance(data["owner_id"], str):
            return bad_request("owner_id must be a string.")
        fields["owner_id"] = data["owner_id"]

    if "amount" in data:
        if not isinstance(data["amount"], int) or isinstance(data["amount"], bool):
            return bad_request("amount must be an integer.")
        fields["amount"] = data["amount"]

    if "detail_mode" in data:
        if not isinstance(data["detail_mode"], str):
            return bad_request("detail_mode must be a string.")
        fields["detail_mode"] = data["detail_mode"]

    if "details" in data:
        details = _parse_details(data["details"])
        if details is None:
            return bad_request("details must be a list of {label, amount}.")
        fields["details"] = details

    result = update_entry(entry_id, **fields)
    if result.status is not FinanceOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_entry(result.entry))


async def delete_entry_endpoint(request: Request) -> Response:
    entry_id = request.path_params["id"]
    result = delete_entry(entry_id)
    if result.status is not FinanceOperationStatus.OK:
        return error_response(result.status)

    return Response(status_code=HTTPStatus.NO_CONTENT)


async def confirm_entry_endpoint(request: Request) -> Response:
    entry_id = request.path_params["id"]
    result = confirm_entry(entry_id)
    if result.status is not FinanceOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_entry(result.entry))


async def reject_entry_endpoint(request: Request) -> Response:
    entry_id = request.path_params["id"]
    result = reject_entry(entry_id)
    if result.status is not FinanceOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_entry(result.entry))
