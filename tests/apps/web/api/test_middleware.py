import pytest

import json

from unittest.mock import AsyncMock, MagicMock, patch
from starlette.requests import Request
from starlette.responses import JSONResponse

from apps.web.api.middleware import AuthMiddleware, endpoint_requires_authentication


def _make_req(method="GET", path="/api/users", headers=None):
    req = MagicMock(spec=Request)
    req.method = method
    req.url = MagicMock()
    req.url.path = path
    req.headers = headers or {}
    req.state = MagicMock()
    return req


class TestEndpointRequiresAuthentication:
    @pytest.mark.unit
    def test_options_request_returns_false(self):
        req = _make_req(method="OPTIONS", path="/api/users")
        assert endpoint_requires_authentication(req) is False

    @pytest.mark.unit
    def test_non_api_path_returns_false(self):
        req = _make_req(path="/not-api/page")
        assert endpoint_requires_authentication(req) is False

    @pytest.mark.unit
    def test_health_path_returns_false(self):
        req = _make_req(path="/api/health")
        assert endpoint_requires_authentication(req) is False

    @pytest.mark.unit
    def test_register_path_returns_false(self):
        req = _make_req(path="/api/register")
        assert endpoint_requires_authentication(req) is False

    @pytest.mark.unit
    def test_login_path_returns_false(self):
        req = _make_req(path="/api/login")
        assert endpoint_requires_authentication(req) is False

    @pytest.mark.unit
    def test_protected_path_returns_true(self):
        req = _make_req(path="/api/users")
        assert endpoint_requires_authentication(req) is True


@pytest.fixture
def middleware():
    return AuthMiddleware(app=MagicMock())


@pytest.fixture
def call_next():
    return AsyncMock(return_value=JSONResponse({"ok": True}))


class TestAuthMiddlewareDispatch:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_public_path_bypasses_auth(self, middleware, call_next):
        req = _make_req(path="/api/health")

        resp = await middleware.dispatch(req, call_next)

        assert resp.status_code == 200
        call_next.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_authorization_returns_401(self, middleware, call_next):
        req = _make_req()

        resp = await middleware.dispatch(req, call_next)

        assert resp.status_code == 401
        body = json.loads(resp.body)
        assert body["error"] == "authentication_required"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_scheme_returns_401(self, middleware, call_next):
        req = _make_req(headers={"Authorization": "Basic abc"})

        resp = await middleware.dispatch(req, call_next)

        assert resp.status_code == 401
        body = json.loads(resp.body)
        assert body["error"] == "authentication_required"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_token_returns_401(self, middleware, call_next):
        req = _make_req(headers={"Authorization": "Bearer "})

        resp = await middleware.dispatch(req, call_next)

        assert resp.status_code == 401
        body = json.loads(resp.body)
        assert body["error"] == "authentication_required"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, middleware, call_next):
        req = _make_req(headers={"Authorization": "Bearer invalid.token.here"})

        with patch("apps.web.api.middleware.decode_token", return_value=None):
            resp = await middleware.dispatch(req, call_next)

        assert resp.status_code == 401
        body = json.loads(resp.body)
        assert body["error"] == "authentication_required"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_token_sets_user_id(self, middleware, call_next):
        req = _make_req(headers={"Authorization": "Bearer valid.token"})

        with patch("apps.web.api.middleware.decode_token", return_value=42):
            resp = await middleware.dispatch(req, call_next)

        assert req.state.user_id == 42
        call_next.assert_called_once()
        body = json.loads(resp.body)
        assert body["ok"] is True
