import pytest
import json

from unittest.mock import MagicMock, patch

from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.testclient import TestClient


class TestApiHealth:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_health_returns_ok(self):
        from apps.web.api.main import api_health

        request = MagicMock()
        resp = await api_health(request)
        assert resp.status_code == 200
        assert json.loads(resp.body) == {"status": "ok"}


class TestRoutes:
    @pytest.mark.unit
    def test_routes_contains_all_endpoints(self):
        from apps.web.api.main import routes

        from collections import defaultdict

        assert all(isinstance(r, Route) for r in routes)
        paths = defaultdict(set)
        for r in routes:
            paths[r.path] |= r.methods
        assert paths["/api/health"] >= {"GET"}
        assert paths["/api/users"] >= {"POST", "GET"}
        assert paths["/api/signup"] >= {"POST"}
        assert paths["/api/login"] >= {"POST"}
        assert paths["/api/users/{id:int}"] >= {"PATCH", "DELETE"}
        assert paths["/api/tasks"] >= {"POST", "GET"}
        assert paths["/api/tasks/{id:int}"] >= {"PATCH", "DELETE"}
        assert paths["/api/tasks/monthly-ranking"] >= {"GET"}
        assert paths["/api/tasks/daily-breakdown"] >= {"GET"}
        assert paths["/api/tasks/today-board"] >= {"GET"}
        assert paths["/api/reminders"] >= {"POST", "GET"}
        assert paths["/api/reminders/{id:int}"] >= {"PATCH", "DELETE"}
        assert paths["/api/finances/periods"] >= {"POST", "GET"}
        assert paths["/api/finances/periods/{id:int}"] >= {"GET"}
        assert paths["/api/finances/tags"] >= {"GET"}
        assert paths["/api/finances/entries"] >= {"POST", "GET"}
        assert paths["/api/finances/entries/{id:int}"] >= {"PATCH", "DELETE"}
        assert paths["/api/finances/entries/{id:int}/confirm"] >= {"POST"}
        assert len(routes) >= 27


class TestMiddleware:
    @pytest.mark.unit
    def test_middleware_contains_cors_and_auth(self):
        from apps.web.api.main import middleware

        assert len(middleware) == 2
        assert all(isinstance(m, Middleware) for m in middleware)


class TestLifespan:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_lifespan_calls_init_db(self):
        from apps.web.api.main import _lifespan

        with patch("apps.web.api.main.init_db") as mock_init:
            async with _lifespan(MagicMock()):
                mock_init.assert_called_once()


class TestApp:
    @pytest.mark.integration
    def test_app_health_endpoint(self, db_path):
        from apps.web.api.main import app

        with TestClient(app) as client:
            resp = client.get("/api/health")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok"}
