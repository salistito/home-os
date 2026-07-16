from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.reminders.types import Reminder, ReminderOperationStatus

_STATUS_HTTP = {
    ReminderOperationStatus.INVALID: HTTPStatus.BAD_REQUEST,
    ReminderOperationStatus.PAST_TIME: HTTPStatus.BAD_REQUEST,
    ReminderOperationStatus.DUPLICATE_MESSAGE: HTTPStatus.BAD_REQUEST,
    ReminderOperationStatus.NOT_FOUND: HTTPStatus.NOT_FOUND,
}

_STATUS_MESSAGE = {
    ReminderOperationStatus.INVALID: "Invalid reminder data.",
    ReminderOperationStatus.PAST_TIME: "The specified date or time is in the past.",
    ReminderOperationStatus.DUPLICATE_MESSAGE: "A reminder with that message already exists.",
    ReminderOperationStatus.NOT_FOUND: "Reminder not found.",
}


def serialize_reminder(reminder: Reminder) -> dict:
    return {
        "id": reminder.id,
        "user_id": reminder.user_id,
        "message": reminder.message,
        "trigger_at": reminder.trigger_at,
        "trigger_time": reminder.trigger_time,
        "recurrence": reminder.recurrence.value,
        "created_at": reminder.created_at,
    }


def error_response(status: ReminderOperationStatus) -> JSONResponse:
    return JSONResponse(
        {"error": status.value, "message": _STATUS_MESSAGE[status]},
        status_code=_STATUS_HTTP[status],
    )
