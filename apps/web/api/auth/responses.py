from http import HTTPStatus

from starlette.responses import JSONResponse


def authentication_required() -> JSONResponse:
    return JSONResponse(
        {"error": "authentication_required", "message": "Authentication required."},
        status_code=HTTPStatus.UNAUTHORIZED,
    )


def invalid_credentials() -> JSONResponse:
    return JSONResponse(
        {"error": "invalid_credentials", "message": "Invalid username or password."},
        status_code=HTTPStatus.UNAUTHORIZED,
    )
