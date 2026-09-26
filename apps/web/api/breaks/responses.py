from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.breaks.types import BreakPeriod, BreakPeriodOperationStatus

_STATUS_HTTP = {
    BreakPeriodOperationStatus.INVALID_START_DATE: HTTPStatus.BAD_REQUEST,
    BreakPeriodOperationStatus.INVALID_END_DATE: HTTPStatus.BAD_REQUEST,
    BreakPeriodOperationStatus.INVALID_DATE_RANGE: HTTPStatus.BAD_REQUEST,
    BreakPeriodOperationStatus.INVALID_USER_IDS: HTTPStatus.BAD_REQUEST,
    BreakPeriodOperationStatus.INVALID_MODULES: HTTPStatus.BAD_REQUEST,
    BreakPeriodOperationStatus.NOT_FOUND: HTTPStatus.NOT_FOUND,
}

_STATUS_MESSAGE = {
    BreakPeriodOperationStatus.INVALID_START_DATE: (
        "start_date is required and must be a valid date."
    ),
    BreakPeriodOperationStatus.INVALID_END_DATE: "end_date must be a valid date.",
    BreakPeriodOperationStatus.INVALID_DATE_RANGE: (
        "end_date must be greater than or equal to start_date."
    ),
    BreakPeriodOperationStatus.INVALID_USER_IDS: (
        "user_ids must be a non-empty list of active users."
    ),
    BreakPeriodOperationStatus.INVALID_MODULES: (
        "modules must be a non-empty list of valid modules."
    ),
    BreakPeriodOperationStatus.NOT_FOUND: "break period not found.",
}


def serialize_break_period(
    break_period: BreakPeriod, users_by_id: dict[int, object] | None = None
) -> dict:
    break_period_data = {
        "id": break_period.id,
        "label": break_period.label,
        "start_date": break_period.start_date,
        "end_date": break_period.end_date,
        "created_at": break_period.created_at,
        "user_ids": break_period.user_ids or [],
        "modules": break_period.modules or [],
    }
    if users_by_id is not None:
        break_period_data["users"] = [
            {"id": user_id, "name": users_by_id[user_id].name}
            for user_id in break_period.user_ids or []
            if user_id in users_by_id
        ]
    return break_period_data


def error_forbidden() -> JSONResponse:
    return JSONResponse(
        {"error": "forbidden", "message": "Admin access required."},
        status_code=HTTPStatus.FORBIDDEN,
    )


def error_response(status: BreakPeriodOperationStatus) -> JSONResponse:
    return JSONResponse(
        {"error": status.value, "message": _STATUS_MESSAGE[status]},
        status_code=_STATUS_HTTP[status],
    )
