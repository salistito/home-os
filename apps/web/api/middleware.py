from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from apps.web.api.users.responses import authentication_required
from core.utils.tokens import decode_token

_PUBLIC_PATHS = {"/api/health", "/api/register", "/api/login"}


def _endpoint_requires_authentication(request: Request) -> bool:
    if request.method == "OPTIONS":
        return False
    if not request.url.path.startswith("/api/"):
        return False
    if request.url.path in _PUBLIC_PATHS:
        return False
    return True


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not _endpoint_requires_authentication(request):
            return await call_next(request)

        authorization_header = request.headers.get("Authorization", "")
        scheme, _, token = authorization_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return authentication_required()

        user_id = decode_token(token)
        if user_id is None:
            return authentication_required()

        request.state.user_id = user_id
        return await call_next(request)
