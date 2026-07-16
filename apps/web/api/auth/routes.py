import json

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.auth.responses import unauthorized
from apps.web.api.responses import bad_request
from core.identity import get_password_hash
from core.passwords import verify_password
from core.tokens import create_token


async def login(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("Body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("Body must be a JSON object.")

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return bad_request("Username and password are required.")

    password_hash = get_password_hash(username)
    if password_hash is None or not verify_password(password, password_hash):
        return unauthorized()

    return JSONResponse({"token": create_token(username), "user_id": username})
