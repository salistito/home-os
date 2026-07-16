from http import HTTPStatus

from starlette.responses import JSONResponse


def unauthorized() -> JSONResponse:
    return JSONResponse(
        {"error": "invalid_credentials", "message": "Invalid username or password."},
        status_code=HTTPStatus.UNAUTHORIZED,
    )
