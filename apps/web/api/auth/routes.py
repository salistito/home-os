import json

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.responses import bad_request
from apps.web.api.auth.responses import invalid_credentials
from core.utils.passwords import verify_password
from core.utils.tokens import create_token
from modules.users.repository import get_password_hash


async def login(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return bad_request("username and password are required.")

    password_hash = get_password_hash(username)
    if password_hash is None or not verify_password(password, password_hash):
        return invalid_credentials()

    return JSONResponse({"token": create_token(username), "user_id": username})
