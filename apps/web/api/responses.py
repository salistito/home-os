from http import HTTPStatus

from starlette.responses import JSONResponse


def bad_request(message: str) -> JSONResponse:
    return JSONResponse(
        {"error": "invalid_request", "message": message},
        status_code=HTTPStatus.BAD_REQUEST,
    )
