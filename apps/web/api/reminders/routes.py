import json

from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.reminders.responses import bad_request, error_response, serialize_reminder
from modules.reminders.repository import (
    EDITABLE_REMINDER_COLUMNS,
    VALID_RECURRENCES,
    get_reminders,
    get_user_reminders,
)
from modules.reminders.service import create_reminder, delete_reminder, update_reminder
from modules.reminders.types import ReminderOperationStatus


async def create(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    user_id = data.get("user_id")
    message = data.get("message")
    trigger_at = data.get("trigger_at")
    trigger_time = data.get("trigger_time")
    recurrence = data.get("recurrence", "none")

    if not isinstance(user_id, str) or not user_id:
        return bad_request("user_id is required.")
    if not isinstance(message, str) or not message.strip():
        return bad_request("message is required.")
    if not isinstance(trigger_at, str) or not trigger_at:
        return bad_request("trigger_at is required.")
    if trigger_time is not None and not isinstance(trigger_time, str):
        return bad_request("trigger_time must be a string.")
    if not isinstance(recurrence, str) or recurrence not in VALID_RECURRENCES:
        return bad_request(f"recurrence must be one of: {', '.join(sorted(VALID_RECURRENCES))}")

    result = create_reminder(user_id, message, trigger_at, trigger_time, recurrence)
    if result.status is not ReminderOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_reminder(result.reminder), status_code=HTTPStatus.CREATED)


async def list_reminders(request: Request) -> Response:
    user_id = request.query_params.get("user_id")
    if user_id:
        reminders = get_user_reminders(user_id)
    else:
        reminders = get_reminders()
    return JSONResponse([serialize_reminder(r) for r in reminders])


async def update(request: Request) -> Response:
    reminder_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    user_id = data.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        return bad_request("user_id is required.")

    fields = {k: v for k, v in data.items() if k in EDITABLE_REMINDER_COLUMNS}
    if not fields:
        return bad_request("no valid fields to update.")

    if "message" in fields and (
        not isinstance(fields["message"], str) or not fields["message"].strip()
    ):
        return bad_request("message must be a non-empty string.")
    if "trigger_at" in fields and (
        not isinstance(fields["trigger_at"], str) or not fields["trigger_at"]
    ):
        return bad_request("trigger_at must be a non-empty string.")
    if (
        "trigger_time" in fields
        and fields["trigger_time"] is not None
        and not isinstance(fields["trigger_time"], str)
    ):
        return bad_request("trigger_time must be a string.")
    if "recurrence" in fields and (
        not isinstance(fields["recurrence"], str) or fields["recurrence"] not in VALID_RECURRENCES
    ):
        return bad_request(f"recurrence must be one of: {', '.join(sorted(VALID_RECURRENCES))}")

    result = update_reminder(reminder_id, user_id, **fields)
    if result.status is not ReminderOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_reminder(result.reminder))


async def delete(request: Request) -> Response:
    reminder_id = request.path_params["id"]
    try:
        data = await request.json()
    except json.JSONDecodeError:
        data = {}

    user_id = data.get("user_id") if isinstance(data, dict) else None
    if not isinstance(user_id, str) or not user_id:
        return bad_request("user_id is required in request body.")

    result = delete_reminder(reminder_id, user_id)
    if result.status is not ReminderOperationStatus.OK:
        return error_response(result.status)

    return JSONResponse(serialize_reminder(result.reminder))
