from http import HTTPStatus

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from core.tokens import decode_token

_PUBLIC_PATHS = {"/api/login", "/api/health"}


def _requires_auth(request: Request) -> bool:
    if request.method == "OPTIONS":
        return False
    if not request.url.path.startswith("/api/"):
        return False
    return request.url.path not in _PUBLIC_PATHS


def _unauthorized() -> JSONResponse:
    return JSONResponse(
        {"error": "unauthorized", "message": "Se requiere autenticación."},
        status_code=HTTPStatus.UNAUTHORIZED,
    )


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not _requires_auth(request):
            return await call_next(request)

        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return _unauthorized()

        user_id = decode_token(token)
        if user_id is None:
            return _unauthorized()

        request.state.user_id = user_id
        return await call_next(request)
