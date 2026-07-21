import json
from http import HTTPStatus

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.web.api.responses import bad_request
from apps.web.api.users.responses import (
    error_forbidden,
    error_registration_closed,
    error_not_found,
    error_conflict,
    invalid_credentials,
    serialize_user,
)
from core.utils.passwords import hash_password, verify_password
from core.utils.tokens import create_token, decode_token
from modules.users.errors import UserAlreadyExistsError
from modules.users.repository import (
    get_users,
    get_active_user_by_id,
    get_active_user_by_name,
    update_user,
    delete_user,
)
from modules.users.service import register_user
from modules.users.types import UserRole


async def register(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    name = data.get("name")
    password = data.get("password")
    telegram_chat_id = data.get("telegram_chat_id")

    if not isinstance(name, str) or not name.strip():
        return bad_request("name is required.")
    if password is not None and not isinstance(password, str):
        return bad_request("password must be a string.")
    if telegram_chat_id is not None and not isinstance(telegram_chat_id, str):
        return bad_request("telegram_chat_id must be a string.")

    users_exist = len(get_users()) > 0

    if users_exist:
        auth_header = request.headers.get("Authorization", "")
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return error_registration_closed()
        user_id = decode_token(token)
        if user_id is None:
            return error_registration_closed()
        requester = get_active_user_by_id(user_id)
        if requester is None or requester.role != UserRole.ADMIN:
            return error_forbidden()
        role = data.get("role", UserRole.MEMBER)
        if role not in (UserRole.ADMIN, UserRole.MEMBER):
            return bad_request("role must be 'admin' or 'member'.")
    else:
        role = UserRole.ADMIN

    try:
        user = register_user(name, role, password, telegram_chat_id)
    except UserAlreadyExistsError as e:
        return error_conflict(str(e))
    return JSONResponse(serialize_user(user), status_code=HTTPStatus.CREATED)


async def login(request: Request) -> Response:
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    name = data.get("name")
    password = data.get("password")
    if not isinstance(name, str) or not isinstance(password, str):
        return bad_request("name and password are required.")

    user = get_active_user_by_name(name)
    if user is None:
        return invalid_credentials()

    password_hash = user.password_hash
    if password_hash is None or not verify_password(password, password_hash):
        return invalid_credentials()

    return JSONResponse(
        {"id": user.id, "name": user.name, "role": user.role, "token": create_token(user.id)}
    )


async def list_users(request: Request) -> Response:
    users = get_users()
    return JSONResponse([serialize_user(u) for u in users])


async def update(request: Request) -> Response:
    user_id = request.path_params["id"]

    requester = get_active_user_by_id(request.state.user_id)
    if requester is None or requester.role != UserRole.ADMIN:
        return error_forbidden()

    try:
        data = await request.json()
    except json.JSONDecodeError:
        return bad_request("body must be valid JSON.")

    if not isinstance(data, dict):
        return bad_request("body must be a JSON object.")

    allowed = {}
    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            return bad_request("name must be a non-empty string.")
        allowed["name"] = data["name"]
    if "role" in data:
        role = data["role"]
        if role not in (UserRole.ADMIN, UserRole.MEMBER):
            return bad_request("role must be 'admin' or 'member'.")
        allowed["role"] = role
    if "password" in data:
        if not isinstance(data["password"], str):
            return bad_request("password must be a string.")
        allowed["password_hash"] = hash_password(data["password"])
    if "telegram_chat_id" in data:
        if not isinstance(data["telegram_chat_id"], str):
            return bad_request("telegram_chat_id must be a string.")
        allowed["telegram_chat_id"] = data["telegram_chat_id"]
    if data.get("restore") is True:
        allowed["deleted_at"] = None

    if not allowed:
        return bad_request("no valid fields to update.")

    users = get_users()
    existing = next((u for u in users if u.id == user_id), None)
    if existing is None:
        return error_not_found()

    if "role" in allowed and existing.role == UserRole.ADMIN and allowed["role"] != UserRole.ADMIN and existing.deleted_at is None:
        active_admins = [u for u in users if u.role == UserRole.ADMIN and u.deleted_at is None]
        if len(active_admins) <= 1:
            return error_conflict("Cannot remove the last admin role.")

    try:
        updated = update_user(user_id, **allowed)
    except UserAlreadyExistsError as e:
        return error_conflict(str(e))
    if not updated:
        return error_not_found()
    user = next((u for u in get_users() if u.id == user_id), None)
    return JSONResponse(serialize_user(user))


async def delete(request: Request) -> Response:
    user_id = request.path_params["id"]

    requester = get_active_user_by_id(request.state.user_id)
    if requester is None or requester.role != UserRole.ADMIN:
        return error_forbidden()

    target = get_active_user_by_id(user_id)
    if target is None:
        return error_not_found()

    if target.role == UserRole.ADMIN:
        active_admins = [
            u for u in get_users() if u.role == UserRole.ADMIN and u.deleted_at is None
        ]
        if len(active_admins) <= 1:
            return error_conflict("Cannot delete the last admin.")

    if not delete_user(user_id):
        return error_not_found()

    user = next((u for u in get_users() if u.id == user_id), None)
    return JSONResponse(serialize_user(user))
