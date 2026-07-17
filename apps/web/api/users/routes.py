from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from modules.users.repository import get_users


async def list_users(request: Request) -> Response:
    users = get_users()
    return JSONResponse([{"id": u.id, "name": u.name} for u in users])
