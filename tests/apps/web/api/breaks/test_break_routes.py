import json
from datetime import date
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from apps.web.api.breaks.routes import (
    create_break_period_handler,
    delete_break_period_handler,
    get_break_period_status_handler,
    list_break_periods_handler,
    update_break_period_handler,
)
from modules.breaks.types import (
    BreakPeriod,
    BreakPeriodOperationResult,
    BreakPeriodOperationStatus,
)
from modules.users.types import User


@pytest.fixture
def mock_request():
    req = MagicMock(spec=Request)
    req.state = MagicMock()
    req.state.user_id = 1
    req.headers = {"Authorization": "Bearer test-token"}
    req.method = "GET"
    req.path_params = {}
    req.query_params = {}
    req.json = AsyncMock()
    return req


def _make_user(user_id=1, role="admin"):
    return User(id=user_id, name=f"User{user_id}", role=role, password_hash="hash")


def _make_break_period(
    period_id=1, label="Vacaciones", start_date="2026-03-10", end_date=None, user_ids=None
):
    return BreakPeriod(
        id=period_id,
        label=label,
        start_date=start_date,
        end_date=end_date,
        created_at="2026-03-01",
        user_ids=user_ids or [1],
    )


def _make_admin_requester(role="admin"):
    return User(id=1, name="Admin", role=role, password_hash="hash")


class TestBreakPeriodStatus:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_status_not_on_break(self, mock_request):
        with (
            patch(
                "apps.web.api.breaks.routes.get_active_break_period_for_user",
                return_value=None,
            ),
            patch("apps.web.api.breaks.routes.get_today", return_value=date(2026, 3, 15)),
        ):
            resp = await get_break_period_status_handler(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body == {"on_break": False, "break": None}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_status_on_break(self, mock_request):
        with (
            patch(
                "apps.web.api.breaks.routes.get_active_break_period_for_user",
                return_value=_make_break_period(),
            ),
            patch("apps.web.api.breaks.routes.get_today", return_value=date(2026, 3, 15)),
        ):
            resp = await get_break_period_status_handler(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["on_break"] is True
        assert body["break"]["label"] == "Vacaciones"
        assert body["break"]["end_date"] is None


class TestBreakPeriodList:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_forbidden_for_member(self, mock_request):
        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(role="member"),
            ),
        ):
            resp = await list_break_periods_handler(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_admin_enriched(self, mock_request):
        period = _make_break_period()
        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
            patch(
                "apps.web.api.breaks.routes.get_break_periods",
                return_value=[period],
            ),
            patch(
                "apps.web.api.breaks.routes.get_users",
                return_value=[_make_user(1)],
            ),
        ):
            resp = await list_break_periods_handler(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert len(body) == 1
        assert body[0]["id"] == 1
        assert body[0]["label"] == "Vacaciones"
        assert body[0]["users"] == [{"id": 1, "name": "User1"}]


class TestBreakPeriodCreate:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_forbidden_for_member(self, mock_request):
        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(role="member"),
            ),
        ):
            resp = await create_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN

    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload_key", ["start_date", "user_ids"])
    async def test_create_rejects_missing_fields(self, mock_request, payload_key):
        payload = {"label": "Vacaciones", "start_date": "2026-03-10", "user_ids": [1]}
        del payload[payload_key]
        mock_request.json.return_value = payload

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
        ):
            resp = await create_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_rejects_invalid_json(self, mock_request):
        mock_request.json.side_effect = json.JSONDecodeError("bad", "", 0)

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
        ):
            resp = await create_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_service_invalid_date_range(self, mock_request):
        mock_request.json.return_value = {
            "start_date": "2026-03-20",
            "end_date": "2026-03-10",
            "user_ids": [1],
        }

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
            patch(
                "apps.web.api.breaks.routes.create_break_period",
                return_value=BreakPeriodOperationResult(
                    status=BreakPeriodOperationStatus.INVALID_DATE_RANGE
                ),
            ),
        ):
            resp = await create_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["error"] == "invalid_date_range"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_ok(self, mock_request):
        period = _make_break_period()
        mock_request.json.return_value = {
            "label": "Vacaciones",
            "start_date": "2026-03-10",
            "user_ids": [1],
        }

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
            patch(
                "apps.web.api.breaks.routes.create_break_period",
                return_value=BreakPeriodOperationResult(
                    break_period=period,
                    status=BreakPeriodOperationStatus.OK,
                ),
            ),
            patch(
                "apps.web.api.breaks.routes.get_users",
                return_value=[_make_user(1)],
            ),
        ):
            resp = await create_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        body = json.loads(resp.body)
        assert body["id"] == 1
        assert body["user_ids"] == [1]


class TestBreakPeriodUpdate:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_forbidden_for_member(self, mock_request):
        mock_request.path_params["id"] = 1

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(role="member"),
            ),
        ):
            resp = await update_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_empty_body(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {}

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
        ):
            resp = await update_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_request):
        mock_request.path_params["id"] = 9999
        mock_request.json.return_value = {"end_date": "2026-03-20"}

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
            patch(
                "apps.web.api.breaks.routes.update_break_period",
                return_value=BreakPeriodOperationResult(
                    status=BreakPeriodOperationStatus.NOT_FOUND
                ),
            ),
        ):
            resp = await update_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_ok(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"end_date": "2026-03-20"}

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
            patch(
                "apps.web.api.breaks.routes.update_break_period",
                return_value=BreakPeriodOperationResult(
                    break_period=_make_break_period(end_date="2026-03-20"),
                    status=BreakPeriodOperationStatus.OK,
                ),
            ),
            patch(
                "apps.web.api.breaks.routes.get_users",
                return_value=[_make_user(1)],
            ),
        ):
            resp = await update_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["end_date"] == "2026-03-20"


class TestBreakPeriodDelete:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_forbidden_for_member(self, mock_request):
        mock_request.path_params["id"] = 1

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(role="member"),
            ),
        ):
            resp = await delete_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_request):
        mock_request.path_params["id"] = 9999

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
            patch(
                "apps.web.api.breaks.routes.delete_break_period",
                return_value=BreakPeriodOperationResult(
                    status=BreakPeriodOperationStatus.NOT_FOUND
                ),
            ),
        ):
            resp = await delete_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_ok(self, mock_request):
        mock_request.path_params["id"] = 1

        with (
            patch(
                "apps.web.api.breaks.routes.get_active_user_by_id",
                return_value=_make_admin_requester(),
            ),
            patch(
                "apps.web.api.breaks.routes.delete_break_period",
                return_value=BreakPeriodOperationResult(
                    break_period=_make_break_period(),
                    status=BreakPeriodOperationStatus.OK,
                ),
            ),
            patch(
                "apps.web.api.breaks.routes.get_users",
                return_value=[_make_user(1)],
            ),
        ):
            resp = await delete_break_period_handler(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["id"] == 1
