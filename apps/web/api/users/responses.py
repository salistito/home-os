from http import HTTPStatus

from starlette.responses import JSONResponse

from modules.users.types import User


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "deleted_at": user.deleted_at,
    }


def authentication_required() -> JSONResponse:
    return JSONResponse(
        {"error": "authentication_required", "message": "Authentication required."},
        status_code=HTTPStatus.UNAUTHORIZED,
    )


def invalid_credentials() -> JSONResponse:
    return JSONResponse(
        {"error": "invalid_credentials", "message": "Invalid name or password."},
        status_code=HTTPStatus.UNAUTHORIZED,
    )


def error_forbidden() -> JSONResponse:
    return JSONResponse(
        {"error": "forbidden", "message": "Admin access required."},
        status_code=HTTPStatus.FORBIDDEN,
    )


def error_registration_closed() -> JSONResponse:
    return JSONResponse(
        {
            "error": "registration_closed",
            "message": "Registration is closed. Ask the admin to create your account.",
        },
        status_code=HTTPStatus.FORBIDDEN,
    )


def error_not_found() -> JSONResponse:
    return JSONResponse(
        {"error": "not_found", "message": "User not found."},
        status_code=HTTPStatus.NOT_FOUND,
    )


def error_conflict(message: str) -> JSONResponse:
    return JSONResponse(
        {"error": "conflict", "message": message},
        status_code=HTTPStatus.CONFLICT,
    )
