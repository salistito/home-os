from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.finances.types import FinanceOperationStatus, Period

_STATUS_HTTP = {
    FinanceOperationStatus.INVALID_LABEL: HTTPStatus.BAD_REQUEST,
    FinanceOperationStatus.DUPLICATE_LABEL: HTTPStatus.CONFLICT,
    FinanceOperationStatus.NOT_FOUND: HTTPStatus.NOT_FOUND,
}

_STATUS_MESSAGE = {
    FinanceOperationStatus.INVALID_LABEL: "Period label cannot be empty.",
    FinanceOperationStatus.DUPLICATE_LABEL: "Ya existe un mes con ese nombre.",
    FinanceOperationStatus.NOT_FOUND: "Period not found.",
}


def serialize_period(period: Period) -> dict:
    return {
        "id": period.id,
        "label": period.label,
        "status": period.status,
        "opened_at": period.opened_at,
    }


def error_response(status: FinanceOperationStatus) -> JSONResponse:
    return JSONResponse(
        {"error": status.value, "message": _STATUS_MESSAGE[status]},
        status_code=_STATUS_HTTP[status],
    )


def bad_request(message: str) -> JSONResponse:
    return JSONResponse(
        {"error": "invalid_request", "message": message},
        status_code=HTTPStatus.BAD_REQUEST,
    )
