import pytest
import json

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

from starlette.requests import Request

from apps.web.api.finances.routes import (
    create_period,
    list_periods,
    get_period_detail_endpoint,
    list_entries_endpoint,
    create_entry,
    update_entry_endpoint,
    delete_entry_endpoint,
    confirm_entry_endpoint,
    list_tags_endpoint,
)
from apps.web.api.reminders.routes import (
    create as reminder_create,
    list_reminders,
    update as reminder_update,
    delete as reminder_delete,
)
from apps.web.api.tasks.routes import (
    create,
    list_tasks,
    update as task_update,
    delete as task_delete,
)
from apps.web.api.tasks.scores import monthly_ranking, daily_breakdown, today_board
from apps.web.api.users.routes import register, login, list_users, update, delete
from modules.finances.types import (
    Entry,
    EntryOperationResult,
    FinanceOperationStatus,
    Period,
    PeriodDetail,
    PeriodDetailResult,
    PeriodOperationResult,
    PeriodSummary,
    Tag,
)
from modules.reminders.types import (
    Reminder,
    ReminderOperationResult,
    ReminderOperationStatus,
    ReminderRecurrence,
)
from modules.tasks.types import (
    Task,
    TaskOperationResult,
    TaskOperationStatus,
)
from modules.users.errors import UserAlreadyExistsError
from modules.users.types import User, UserRole


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


def _make_user(user_id=1, name="Test", role="admin", password_hash="hash", deleted_at=None):
    return User(
        id=user_id, name=name, role=role, password_hash=password_hash, deleted_at=deleted_at
    )


def _make_task(task_id=1, name="Task", points=10, frequency_days=None, next_due_date=None):
    return Task(
        id=task_id,
        name=name,
        points=points,
        frequency_days=frequency_days,
        next_due_date=next_due_date,
    )


def _make_task_result(task=None, status=TaskOperationStatus.OK):
    return TaskOperationResult(task=task, status=status)


def _make_reminder(
    reminder_id=1,
    user_id=1,
    message="test",
    trigger_at="2026-12-01",
    trigger_time=None,
    recurrence=ReminderRecurrence.NONE,
    cron_job_id=None,
    created_at="2026-01-01",
):
    return Reminder(
        id=reminder_id,
        user_id=user_id,
        message=message,
        trigger_at=trigger_at,
        trigger_time=trigger_time,
        recurrence=recurrence,
        cron_job_id=cron_job_id,
        created_at=created_at,
    )


def _make_reminder_result(reminder=None, status=ReminderOperationStatus.OK):
    return ReminderOperationResult(reminder=reminder, status=status)


def _make_period(period_id=1, label="Enero 2026", status="open", opened_at="2026-01-01"):
    return Period(id=period_id, label=label, status=status, opened_at=opened_at)


def _make_period_result(period=None, status=FinanceOperationStatus.OK):
    return PeriodOperationResult(period=period, status=status)


def _make_period_detail_result(detail=None, status=FinanceOperationStatus.OK):
    return PeriodDetailResult(detail=detail, status=status)


def _make_entry(
    entry_id=1,
    period_id=1,
    kind="expense",
    scope="shared",
    owner_id=1,
    label="entry",
    amount=100,
    status="pending",
    paid_at=None,
    detail_mode="none",
    created_at="2026-01-01",
    details=None,
    tags=None,
):
    return Entry(
        id=entry_id,
        period_id=period_id,
        kind=kind,
        scope=scope,
        owner_id=owner_id,
        label=label,
        amount=amount,
        status=status,
        paid_at=paid_at,
        detail_mode=detail_mode,
        created_at=created_at,
        details=details or [],
        tags=tags or [],
    )


def _make_entry_result(entry=None, status=FinanceOperationStatus.OK):
    return EntryOperationResult(entry=entry, status=status)


def _make_tag(tag_id=1, name="tag", color="#fff", created_at="2026-01-01"):
    return Tag(id=tag_id, name=name, color=color, created_at=created_at)


class TestUsersRegister:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_name_no_users_exist_creates_admin(self, mock_request):
        user = _make_user(name="NewUser", role="admin")
        mock_request.json.return_value = {"name": "NewUser"}

        with (
            patch("apps.web.api.users.routes.get_users", return_value=[]),
            patch("apps.web.api.users.routes.register_user", return_value=user) as mock_register,
        ):
            resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        body = json.loads(resp.body)
        assert body["name"] == "NewUser"
        mock_register.assert_called_once_with("NewUser", UserRole.ADMIN, None, None)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_body_returns_400(self, mock_request):
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["error"] == "invalid_request"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        mock_request.json.return_value = ["not a dict"]

        resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_name_returns_400(self, mock_request):
        mock_request.json.return_value = {}

        resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "name is required."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_users_exist_no_token_returns_registration_closed(self, mock_request):
        mock_request.json.return_value = {"name": "NewUser"}
        mock_request.headers = {}

        with patch("apps.web.api.users.routes.get_users", return_value=[_make_user()]):
            resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN
        body = json.loads(resp.body)
        assert body["error"] == "registration_closed"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_users_exist_non_admin_token_returns_forbidden(self, mock_request):
        user = _make_user(role="member")
        mock_request.json.return_value = {"name": "NewUser"}

        with (
            patch("apps.web.api.users.routes.get_users", return_value=[_make_user()]),
            patch("apps.web.api.users.routes.decode_token", return_value=1),
            patch("apps.web.api.users.routes.get_active_user_by_id", return_value=user),
        ):
            resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN
        body = json.loads(resp.body)
        assert body["error"] == "forbidden"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_users_exist_admin_token_creates_member(self, mock_request):
        admin = _make_user(user_id=1, role="admin")
        member = _make_user(user_id=2, name="Member", role="member")
        mock_request.json.return_value = {"name": "Member"}

        with (
            patch("apps.web.api.users.routes.get_users", return_value=[admin]),
            patch("apps.web.api.users.routes.decode_token", return_value=1),
            patch("apps.web.api.users.routes.get_active_user_by_id", return_value=admin),
            patch("apps.web.api.users.routes.register_user", return_value=member) as mock_register,
        ):
            resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        mock_register.assert_called_once_with("Member", UserRole.MEMBER, None, None)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_duplicate_name_returns_409(self, mock_request):
        mock_request.json.return_value = {"name": "Existing"}

        with (
            patch("apps.web.api.users.routes.get_users", return_value=[]),
            patch(
                "apps.web.api.users.routes.register_user",
                side_effect=UserAlreadyExistsError(_make_user()),
            ),
        ):
            resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.CONFLICT
        body = json.loads(resp.body)
        assert body["error"] == "conflict"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_password_type_returns_400(self, mock_request):
        mock_request.json.return_value = {"name": "User", "password": 123}

        with patch("apps.web.api.users.routes.get_users", return_value=[]):
            resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_telegram_chat_id_type_returns_400(self, mock_request):
        mock_request.json.return_value = {"name": "User", "telegram_chat_id": 123}

        with patch("apps.web.api.users.routes.get_users", return_value=[]):
            resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_password_and_telegram_chat_id(self, mock_request):
        user = _make_user(role="admin")
        mock_request.json.return_value = {
            "name": "User",
            "password": "secret",
            "telegram_chat_id": "12345",
        }

        with (
            patch("apps.web.api.users.routes.get_users", return_value=[]),
            patch("apps.web.api.users.routes.register_user", return_value=user) as mock_register,
        ):
            resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        mock_register.assert_called_once_with("User", UserRole.ADMIN, "secret", "12345")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_existing_users_bad_token_returns_closed(self, mock_request):
        mock_request.json.return_value = {"name": "NewUser"}

        with (
            patch("apps.web.api.users.routes.get_users", return_value=[_make_user()]),
            patch("apps.web.api.users.routes.decode_token", return_value=None),
        ):
            resp = await register(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN
        body = json.loads(resp.body)
        assert body["error"] == "registration_closed"


class TestUsersLogin:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_credentials_returns_token(self, mock_request):
        user = _make_user(password_hash="hashed")
        mock_request.json.return_value = {"name": "Test", "password": "secret"}

        with (
            patch("apps.web.api.users.routes.get_active_user_by_name", return_value=user),
            patch("apps.web.api.users.routes.verify_password", return_value=True),
            patch("apps.web.api.users.routes.create_token", return_value="token123"),
        ):
            resp = await login(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["id"] == 1
        assert body["name"] == "Test"
        assert body["role"] == "admin"
        assert body["token"] == "token123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, mock_request):
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        resp = await login(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        mock_request.json.return_value = []

        resp = await login(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_name_or_password_returns_400(self, mock_request):
        mock_request.json.return_value = {"name": 1, "password": 2}

        resp = await login(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_wrong_name_returns_401(self, mock_request):
        mock_request.json.return_value = {"name": "Nobody", "password": "secret"}

        with patch("apps.web.api.users.routes.get_active_user_by_name", return_value=None):
            resp = await login(mock_request)

        assert resp.status_code == HTTPStatus.UNAUTHORIZED
        body = json.loads(resp.body)
        assert body["error"] == "invalid_credentials"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, mock_request):
        user = _make_user(password_hash="hashed")
        mock_request.json.return_value = {"name": "Test", "password": "wrong"}

        with (
            patch("apps.web.api.users.routes.get_active_user_by_name", return_value=user),
            patch("apps.web.api.users.routes.verify_password", return_value=False),
        ):
            resp = await login(mock_request)

        assert resp.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_password_hash_returns_401(self, mock_request):
        user = _make_user(password_hash=None)
        mock_request.json.return_value = {"name": "Test", "password": "secret"}

        with (
            patch("apps.web.api.users.routes.get_active_user_by_name", return_value=user),
            patch("apps.web.api.users.routes.verify_password", return_value=False),
        ):
            resp = await login(mock_request)

        assert resp.status_code == HTTPStatus.UNAUTHORIZED


class TestUsersListUsers:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_user_list(self, mock_request):
        users = [_make_user(user_id=1), _make_user(user_id=2, name="User2", role="member")]

        with patch("apps.web.api.users.routes.get_users", return_value=users):
            resp = await list_users(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert len(body) == 2
        assert body[0]["id"] == 1
        assert body[1]["id"] == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_list(self, mock_request):
        with patch("apps.web.api.users.routes.get_users", return_value=[]):
            resp = await list_users(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body == []


class TestUsersUpdate:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_non_admin_requester_returns_403(self, mock_request):
        member = _make_user(role="member")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=member):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_requester_not_found_returns_403(self, mock_request):
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=None):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_update_by_admin_succeeds(self, mock_request):
        admin = _make_user(role="admin")
        target = _make_user(user_id=2, name="UpdatedUser", role="member")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"name": "UpdatedUser"}

        with (
            patch(
                "apps.web.api.users.routes.get_active_user_by_id",
                side_effect=[admin, target, target],
            ),
            patch("apps.web.api.users.routes.update_user", return_value=True),
        ):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["name"] == "UpdatedUser"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_user_not_found_returns_404(self, mock_request):
        admin = _make_user(role="admin")
        mock_request.path_params["id"] = 99
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"name": "NewName"}

        with (
            patch("apps.web.api.users.routes.get_active_user_by_id", side_effect=[admin, None]),
        ):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, mock_request):
        admin = _make_user(role="admin")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=admin):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_valid_fields_returns_400(self, mock_request):
        admin = _make_user(role="admin")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"unknown_field": "value"}

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=admin):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "no valid fields to update."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_duplicate_name_returns_409(self, mock_request):
        admin = _make_user(role="admin")
        target = _make_user(user_id=2, name="OldName", role="member")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"name": "ExistingName"}

        with (
            patch("apps.web.api.users.routes.get_active_user_by_id", side_effect=[admin, target]),
            patch(
                "apps.web.api.users.routes.update_user",
                side_effect=UserAlreadyExistsError(_make_user(name="ExistingName")),
            ),
        ):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.CONFLICT

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_name_type_returns_400(self, mock_request):
        admin = _make_user(role="admin")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"name": 123}

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=admin):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_name_returns_400(self, mock_request):
        admin = _make_user(role="admin")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"name": "   "}

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=admin):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_password_hashing(self, mock_request):
        admin = _make_user(role="admin")
        target = _make_user(user_id=2)
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"password": "newpass"}

        with (
            patch(
                "apps.web.api.users.routes.get_active_user_by_id",
                side_effect=[admin, target, target],
            ),
            patch("apps.web.api.users.routes.hash_password", return_value="hashed_new"),
            patch("apps.web.api.users.routes.update_user", return_value=True) as mock_update,
        ):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(2, password_hash="hashed_new")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_password_type_returns_400(self, mock_request):
        admin = _make_user(role="admin")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"password": 123}

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=admin):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_telegram_chat_id_type_returns_400(self, mock_request):
        admin = _make_user(role="admin")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"telegram_chat_id": True}

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=admin):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        admin = _make_user(role="admin")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = []

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=admin):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "body must be a JSON object."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_telegram_chat_id_update(self, mock_request):
        admin = _make_user(role="admin")
        target = _make_user(user_id=2, name="UserWithChat", role="member")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"telegram_chat_id": "123456"}

        with (
            patch("apps.web.api.users.routes.get_active_user_by_id", side_effect=[admin, target, target]),
            patch("apps.web.api.users.routes.update_user", return_value=True) as mock_update,
        ):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(2, telegram_chat_id="123456")
        body = json.loads(resp.body)
        assert body["name"] == "UserWithChat"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_user_false_returns_not_found(self, mock_request):
        admin = _make_user(role="admin")
        target = _make_user(user_id=2, name="Target", role="member")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1
        mock_request.json.return_value = {"name": "NewName"}

        with (
            patch("apps.web.api.users.routes.get_active_user_by_id", side_effect=[admin, target]),
            patch("apps.web.api.users.routes.update_user", return_value=False),
        ):
            resp = await update(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND
        body = json.loads(resp.body)
        assert body["error"] == "not_found"


class TestUsersDelete:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_non_admin_returns_403(self, mock_request):
        member = _make_user(role="member")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1

        with patch("apps.web.api.users.routes.get_active_user_by_id", return_value=member):
            resp = await delete(mock_request)

        assert resp.status_code == HTTPStatus.FORBIDDEN

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_target_not_found_returns_404(self, mock_request):
        admin = _make_user(role="admin")
        mock_request.path_params["id"] = 99
        mock_request.state.user_id = 1

        with (
            patch("apps.web.api.users.routes.get_active_user_by_id", side_effect=[admin, None]),
        ):
            resp = await delete(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cannot_delete_last_admin(self, mock_request):
        admin = _make_user(user_id=1, role="admin")
        target_admin = _make_user(user_id=1, role="admin")
        mock_request.path_params["id"] = 1
        mock_request.state.user_id = 1

        with (
            patch(
                "apps.web.api.users.routes.get_active_user_by_id", side_effect=[admin, target_admin]
            ),
            patch("apps.web.api.users.routes.get_users", return_value=[target_admin]),
        ):
            resp = await delete(mock_request)

        assert resp.status_code == HTTPStatus.CONFLICT

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_delete_succeeds(self, mock_request):
        admin = _make_user(user_id=1, role="admin")
        target = _make_user(user_id=2, role="member")
        deleted = _make_user(user_id=2, role="member", deleted_at="2026-01-01")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1

        with (
            patch("apps.web.api.users.routes.get_active_user_by_id", side_effect=[admin, target]),
            patch("apps.web.api.users.routes.get_users", return_value=[admin, deleted]),
            patch("apps.web.api.users.routes.delete_user", return_value=True),
        ):
            resp = await delete(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["deleted_at"] is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_fails_returns_404(self, mock_request):
        admin = _make_user(role="admin")
        target = _make_user(user_id=2, role="member")
        mock_request.path_params["id"] = 2
        mock_request.state.user_id = 1

        with (
            patch("apps.web.api.users.routes.get_active_user_by_id", side_effect=[admin, target]),
            patch("apps.web.api.users.routes.get_users", return_value=[admin, target]),
            patch("apps.web.api.users.routes.delete_user", return_value=False),
        ):
            resp = await delete(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND


class TestTasksCreate:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_data_creates_task(self, mock_request):
        task = _make_task()
        result = _make_task_result(task=task)
        mock_request.json.return_value = {"name": "NewTask", "points": 10}

        with patch("apps.web.api.tasks.routes.create_task", return_value=result):
            resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        body = json.loads(resp.body)
        assert body["name"] == "Task"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, mock_request):
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        mock_request.json.return_value = []

        resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_name_returns_400(self, mock_request):
        mock_request.json.return_value = {"points": 10}

        resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "name is required."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_name_not_string_returns_400(self, mock_request):
        mock_request.json.return_value = {"name": 123, "points": 10}

        resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_points_returns_400(self, mock_request):
        mock_request.json.return_value = {"name": "Task", "points": "not_int"}

        resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bool_points_returns_400(self, mock_request):
        mock_request.json.return_value = {"name": "Task", "points": True}

        resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_frequency_returns_400(self, mock_request):
        mock_request.json.return_value = {"name": "Task", "points": 10, "frequency_days": True}

        resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_next_due_date_returns_400(self, mock_request):
        mock_request.json.return_value = {"name": "Task", "points": 10, "next_due_date": "bad-date"}

        resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_next_due_date(self, mock_request):
        task = _make_task(next_due_date="2026-06-01")
        result = _make_task_result(task=task)
        mock_request.json.return_value = {
            "name": "Task",
            "points": 10,
            "next_due_date": "2026-06-01",
        }

        with patch("apps.web.api.tasks.routes.create_task", return_value=result) as mock_create:
            resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        mock_create.assert_called_once_with("Task", 10, None, "2026-06-01")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_error_returns_error_response(self, mock_request):
        result = _make_task_result(status=TaskOperationStatus.DUPLICATE_NAME)
        mock_request.json.return_value = {"name": "Task", "points": 10}

        with patch("apps.web.api.tasks.routes.create_task", return_value=result):
            resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["error"] == "duplicate_name"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_frequency_days(self, mock_request):
        task = _make_task(frequency_days=7)
        result = _make_task_result(task=task)
        mock_request.json.return_value = {"name": "Task", "points": 10, "frequency_days": 7}

        with patch("apps.web.api.tasks.routes.create_task", return_value=result) as mock_create:
            resp = await create(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        mock_create.assert_called_once_with("Task", 10, 7, None)


class TestTasksListTasks:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_task_list(self, mock_request):
        tasks = [_make_task(task_id=1), _make_task(task_id=2, name="Task2")]
        with patch("apps.web.api.tasks.routes.get_active_tasks", return_value=tasks):
            resp = await list_tasks(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert len(body) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_list(self, mock_request):
        with patch("apps.web.api.tasks.routes.get_active_tasks", return_value=[]):
            resp = await list_tasks(mock_request)

        assert resp.status_code == HTTPStatus.OK
        assert json.loads(resp.body) == []


class TestTasksUpdate:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_update(self, mock_request):
        task = _make_task(name="UpdatedTask")
        result = _make_task_result(task=task)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"name": "UpdatedTask"}

        with patch(
            "apps.web.api.tasks.routes.update_active_task", return_value=result
        ) as mock_update:
            resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, name="UpdatedTask")
        body = json.loads(resp.body)
        assert body["name"] == "UpdatedTask"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = "string"

        resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_editable_fields_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"unknown": "value"}

        resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "no valid fields to update."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_name_type_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"name": 123}

        resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_points_type_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"points": True}

        resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_frequency_type_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"frequency_days": "not_int"}

        resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_next_due_date_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"next_due_date": "bad-date"}

        resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_next_due_date_none_skips_parsing(self, mock_request):
        task = _make_task()
        result = _make_task_result(task=task)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"next_due_date": None}

        with patch(
            "apps.web.api.tasks.routes.update_active_task", return_value=result
        ) as mock_update:
            resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, next_due_date=None)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_next_due_date_parsed(self, mock_request):
        task = _make_task(next_due_date="2026-07-01")
        result = _make_task_result(task=task)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"next_due_date": "2026-07-01"}

        with patch(
            "apps.web.api.tasks.routes.update_active_task", return_value=result
        ) as mock_update:
            resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, next_due_date="2026-07-01")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_not_found_returns_error(self, mock_request):
        result = _make_task_result(status=TaskOperationStatus.NOT_FOUND)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"name": "NewName"}

        with patch("apps.web.api.tasks.routes.update_active_task", return_value=result):
            resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_frequency_days_none_accepted(self, mock_request):
        task = _make_task(frequency_days=None)
        result = _make_task_result(task=task)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"frequency_days": None}

        with patch(
            "apps.web.api.tasks.routes.update_active_task", return_value=result
        ) as mock_update:
            resp = await task_update(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, frequency_days=None)


class TestTasksDelete:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_delete(self, mock_request):
        task = _make_task()
        result = _make_task_result(task=task)
        mock_request.path_params["id"] = 1

        with patch("apps.web.api.tasks.routes.soft_delete_active_task", return_value=result):
            resp = await task_delete(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["name"] == "Task"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_not_found_returns_error(self, mock_request):
        result = _make_task_result(status=TaskOperationStatus.NOT_FOUND)
        mock_request.path_params["id"] = 1

        with patch("apps.web.api.tasks.routes.soft_delete_active_task", return_value=result):
            resp = await task_delete(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND


class TestTasksScores:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monthly_ranking(self, mock_request, frozen_today):
        users = [_make_user(user_id=1), _make_user(user_id=2, name="User2")]
        month_points = {1: 100, 2: 200}

        with (
            patch("apps.web.api.tasks.scores.get_users", return_value=users),
            patch("apps.web.api.tasks.scores.get_month_points", return_value=month_points),
            patch("apps.web.api.tasks.scores.month_key", return_value="2026-03"),
        ):
            resp = await monthly_ranking(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["month"] == "2026-03"
        assert len(body["ranking"]) == 2
        assert body["ranking"][0]["points"] == 200

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_daily_breakdown(self, mock_request, frozen_today):
        users = [_make_user(user_id=1)]
        daily = {"2026-03-15": {1: 50}}
        tasks_breakdown = {"2026-03-15": {1: [{"name": "T1", "points": 50}]}}

        with (
            patch("apps.web.api.tasks.scores.get_users", return_value=users),
            patch("apps.web.api.tasks.scores.get_daily_points", return_value=daily),
            patch(
                "apps.web.api.tasks.scores.get_daily_task_breakdown", return_value=tasks_breakdown
            ),
            patch("apps.web.api.tasks.scores.month_key", return_value="2026-03"),
        ):
            resp = await daily_breakdown(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["month"] == "2026-03"
        assert len(body["users"]) == 1
        assert body["daily"]["2026-03-15"]["1"] == 50
        assert body["tasks"]["2026-03-15"]["1"][0]["name"] == "T1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_today_board(self, mock_request, frozen_today):
        from datetime import date

        users = [_make_user(user_id=1)]
        board_data = {1: [{"task_id": 1, "name": "T1", "points": 10, "done": False}]}

        with (
            patch("apps.web.api.tasks.scores.get_users", return_value=users),
            patch("apps.web.api.tasks.scores.get_day_board", return_value=board_data),
            patch("apps.web.api.tasks.scores.get_today", return_value=date(2026, 3, 15)),
        ):
            resp = await today_board(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["date"] == "2026-03-15"
        assert len(body["users"]) == 1
        assert body["users"][0]["tasks"] == board_data[1]


class TestRemindersCreate:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_data_creates_reminder(self, mock_request):
        reminder = _make_reminder()
        result = _make_reminder_result(reminder=reminder)
        mock_request.json.return_value = {
            "user_id": 1,
            "message": "test",
            "trigger_at": "2026-12-01",
        }

        with (
            patch("apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()),
            patch("apps.web.api.reminders.routes.create_reminder", return_value=result),
        ):
            resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        body = json.loads(resp.body)
        assert body["message"] == "test"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, mock_request):
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        mock_request.json.return_value = []

        resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_user_id_returns_400(self, mock_request):
        mock_request.json.return_value = {"message": "test", "trigger_at": "2026-12-01"}

        resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bool_user_id_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "user_id": True,
            "message": "test",
            "trigger_at": "2026-12-01",
        }

        resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_inactive_user_id_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "user_id": 99,
            "message": "test",
            "trigger_at": "2026-12-01",
        }

        with patch("apps.web.api.reminders.routes.get_active_user_by_id", return_value=None):
            resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "user_id is not an active user."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_message_returns_400(self, mock_request):
        mock_request.json.return_value = {"user_id": 1, "trigger_at": "2026-12-01"}

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_message_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "user_id": 1,
            "message": "  ",
            "trigger_at": "2026-12-01",
        }

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_trigger_at_returns_400(self, mock_request):
        mock_request.json.return_value = {"user_id": 1, "message": "test"}

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_recurrence_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "user_id": 1,
            "message": "test",
            "trigger_at": "2026-12-01",
            "recurrence": "bad_value",
        }

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_trigger_time_type_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "user_id": 1,
            "message": "test",
            "trigger_at": "2026-12-01",
            "trigger_time": 123,
        }

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_error_returns_error_response(self, mock_request):
        result = _make_reminder_result(status=ReminderOperationStatus.PAST_TIME)
        mock_request.json.return_value = {
            "user_id": 1,
            "message": "test",
            "trigger_at": "2026-12-01",
        }

        with (
            patch("apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()),
            patch("apps.web.api.reminders.routes.create_reminder", return_value=result),
        ):
            resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["error"] == "past_time"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_trigger_time_and_recurrence(self, mock_request):
        reminder = _make_reminder(
            trigger_time="10:00",
            recurrence=ReminderRecurrence.DAILY,
        )
        result = _make_reminder_result(reminder=reminder)
        mock_request.json.return_value = {
            "user_id": 1,
            "message": "test",
            "trigger_at": "2026-12-01",
            "trigger_time": "10:00",
            "recurrence": "daily",
        }

        with (
            patch("apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()),
            patch(
                "apps.web.api.reminders.routes.create_reminder", return_value=result
            ) as mock_create,
        ):
            resp = await reminder_create(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        mock_create.assert_called_once_with(1, "test", "2026-12-01", "10:00", "daily")


class TestRemindersListReminders:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_without_query_returns_all(self, mock_request):
        reminders = [_make_reminder(), _make_reminder(reminder_id=2)]
        with patch("apps.web.api.reminders.routes.get_reminders", return_value=reminders):
            resp = await list_reminders(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert len(body) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_user_id_returns_user_reminders(self, mock_request):
        mock_request.query_params = {"user_id": "1"}
        reminders = [_make_reminder()]
        with patch("apps.web.api.reminders.routes.get_user_reminders", return_value=reminders):
            resp = await list_reminders(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert len(body) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_invalid_user_id_returns_400(self, mock_request):
        mock_request.query_params = {"user_id": "not_int"}

        resp = await list_reminders(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST


class TestRemindersUpdate:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_update(self, mock_request):
        reminder = _make_reminder(message="updated")
        result = _make_reminder_result(reminder=reminder)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1, "message": "updated"}

        with (
            patch("apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()),
            patch(
                "apps.web.api.reminders.routes.update_reminder", return_value=result
            ) as mock_update,
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, 1, message="updated")
        body = json.loads(resp.body)
        assert body["message"] == "updated"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_user_id_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"message": "updated"}

        resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_inactive_user_id_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 99, "message": "updated"}

        with patch("apps.web.api.reminders.routes.get_active_user_by_id", return_value=None):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_editable_fields_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1, "unknown": "value"}

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "no valid fields to update."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_message_type_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1, "message": 123}

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_message_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1, "message": "  "}

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_trigger_at_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1, "trigger_at": 123}

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_trigger_at_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1, "trigger_at": ""}

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_trigger_time_type_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1, "trigger_time": 123}

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_time_none_accepted(self, mock_request):
        reminder = _make_reminder()
        result = _make_reminder_result(reminder=reminder)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1, "trigger_time": None}

        with (
            patch("apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()),
            patch("apps.web.api.reminders.routes.update_reminder", return_value=result),
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.OK

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_recurrence_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {
            "user_id": 1,
            "recurrence": "invalid_rec",
        }

        with patch(
            "apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = []

        resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "body must be a JSON object."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_error_returns_error_response(self, mock_request):
        result = _make_reminder_result(status=ReminderOperationStatus.INVALID)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1, "message": "updated"}

        with (
            patch("apps.web.api.reminders.routes.get_active_user_by_id", return_value=_make_user()),
            patch("apps.web.api.reminders.routes.update_reminder", return_value=result),
        ):
            resp = await reminder_update(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["error"] == ReminderOperationStatus.INVALID.value


class TestRemindersDelete:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_delete(self, mock_request):
        reminder = _make_reminder()
        result = _make_reminder_result(reminder=reminder)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1}

        with patch("apps.web.api.reminders.routes.delete_reminder", return_value=result):
            resp = await reminder_delete(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["message"] == "test"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_user_id_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {}

        resp = await reminder_delete(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bool_user_id_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": True}

        resp = await reminder_delete(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_body_uses_default(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        resp = await reminder_delete(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_error_returns_error(self, mock_request):
        result = _make_reminder_result(status=ReminderOperationStatus.NOT_FOUND)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"user_id": 1}

        with patch("apps.web.api.reminders.routes.delete_reminder", return_value=result):
            resp = await reminder_delete(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND


class TestFinancesCreatePeriod:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_label_creates_period(self, mock_request):
        period = _make_period(label="Enero 2026")
        result = _make_period_result(period=period)
        mock_request.json.return_value = {"label": "Enero 2026"}

        with patch("apps.web.api.finances.routes.open_period", return_value=result) as mock_open:
            resp = await create_period(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        mock_open.assert_called_once_with("Enero 2026")
        body = json.loads(resp.body)
        assert body["label"] == "Enero 2026"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_without_body_defaults_to_none_label(self, mock_request):
        period = _make_period()
        result = _make_period_result(period=period)
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        with patch("apps.web.api.finances.routes.open_period", return_value=result) as mock_open:
            resp = await create_period(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        mock_open.assert_called_once_with(None)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_duplicate_label_returns_error(self, mock_request):
        result = _make_period_result(status=FinanceOperationStatus.DUPLICATE_LABEL)
        mock_request.json.return_value = {"label": "Duplicate"}

        with patch("apps.web.api.finances.routes.open_period", return_value=result):
            resp = await create_period(mock_request)

        assert resp.status_code == HTTPStatus.CONFLICT

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_label_type_returns_400(self, mock_request):
        mock_request.json.return_value = {"label": 123}

        resp = await create_period(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        mock_request.json.return_value = []

        resp = await create_period(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST


class TestFinancesListPeriods:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_periods(self, mock_request):
        periods = [_make_period(period_id=1), _make_period(period_id=2, label="Febrero 2026")]
        with patch("apps.web.api.finances.routes.get_periods", return_value=periods):
            resp = await list_periods(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert len(body) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_list(self, mock_request):
        with patch("apps.web.api.finances.routes.get_periods", return_value=[]):
            resp = await list_periods(mock_request)

        assert resp.status_code == HTTPStatus.OK
        assert json.loads(resp.body) == []


class TestFinancesGetPeriodDetail:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_period_returns_detail(self, mock_request):
        period = _make_period()
        detail = PeriodDetail(
            period=period,
            entries=[],
            summary=PeriodSummary(shared_total=0, contributions={}, people=[]),
        )
        result = _make_period_detail_result(detail=detail)
        mock_request.path_params["id"] = 1

        with patch("apps.web.api.finances.routes.get_period_detail", return_value=result):
            resp = await get_period_detail_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["label"] == "Enero 2026"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_not_found_returns_error(self, mock_request):
        result = _make_period_detail_result(status=FinanceOperationStatus.NOT_FOUND)
        mock_request.path_params["id"] = 1

        with patch("apps.web.api.finances.routes.get_period_detail", return_value=result):
            resp = await get_period_detail_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND


class TestFinancesListEntries:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_period_id_returns_400(self, mock_request):
        resp = await list_entries_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "period_id is required."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_period_id_returns_400(self, mock_request):
        mock_request.query_params = {"period_id": "bad"}

        resp = await list_entries_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_period_id_returns_entries(self, mock_request):
        entries = [_make_entry()]
        mock_request.query_params = {"period_id": "1"}

        with patch("apps.web.api.finances.routes.list_entries", return_value=entries):
            resp = await list_entries_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert len(body) == 1


class TestFinancesCreateEntry:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_data_creates_entry(self, mock_request):
        entry = _make_entry()
        result = _make_entry_result(entry=entry)
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": 1,
            "label": "entry",
        }

        with (
            patch("apps.web.api.finances.routes.get_active_user_by_id", return_value=_make_user()),
            patch("apps.web.api.finances.routes.add_entry", return_value=result) as mock_add,
        ):
            resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        mock_add.assert_called_once_with(1, "expense", "shared", 1, "entry", None, None)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, mock_request):
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        mock_request.json.return_value = []

        resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_period_id_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": True,
            "kind": "expense",
            "scope": "shared",
            "owner_id": 1,
            "label": "entry",
        }

        resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_owner_id_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": "bad_type",
            "label": "entry",
        }

        resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bool_owner_id_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": True,
            "label": "entry",
        }

        resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_inactive_owner_id_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": 99,
            "label": "entry",
        }

        with patch("apps.web.api.finances.routes.get_active_user_by_id", return_value=None):
            resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["message"] == "owner_id is not an active user."

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_kind_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": 123,
            "scope": "shared",
            "owner_id": 1,
            "label": "entry",
        }

        resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_scope_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": 123,
            "owner_id": 1,
            "label": "entry",
        }

        resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_label_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": 1,
            "label": 123,
        }

        with patch("apps.web.api.finances.routes.get_active_user_by_id", return_value=_make_user()):
            resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_amount_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": 1,
            "label": "entry",
            "amount": True,
        }

        with patch("apps.web.api.finances.routes.get_active_user_by_id", return_value=_make_user()):
            resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_tags_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": 1,
            "label": "entry",
            "tags": [123],
        }

        with patch("apps.web.api.finances.routes.get_active_user_by_id", return_value=_make_user()):
            resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tags_not_list_returns_400(self, mock_request):
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": 1,
            "label": "entry",
            "tags": "not_list",
        }

        with patch("apps.web.api.finances.routes.get_active_user_by_id", return_value=_make_user()):
            resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_amount_and_tags(self, mock_request):
        entry = _make_entry(amount=500, tags=[_make_tag()])
        result = _make_entry_result(entry=entry)
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": 1,
            "label": "entry",
            "amount": 500,
            "tags": ["tag1"],
        }

        with (
            patch("apps.web.api.finances.routes.get_active_user_by_id", return_value=_make_user()),
            patch("apps.web.api.finances.routes.add_entry", return_value=result) as mock_add,
        ):
            resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.CREATED
        mock_add.assert_called_once_with(1, "expense", "shared", 1, "entry", 500, ["tag1"])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_error_returns_error_response(self, mock_request):
        result = _make_entry_result(status=FinanceOperationStatus.INVALID_AMOUNT)
        mock_request.json.return_value = {
            "period_id": 1,
            "kind": "expense",
            "scope": "shared",
            "owner_id": 1,
            "label": "entry",
        }

        with (
            patch("apps.web.api.finances.routes.get_active_user_by_id", return_value=_make_user()),
            patch("apps.web.api.finances.routes.add_entry", return_value=result),
        ):
            resp = await create_entry(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST
        body = json.loads(resp.body)
        assert body["error"] == FinanceOperationStatus.INVALID_AMOUNT.value


class TestFinancesUpdateEntry:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_update(self, mock_request):
        entry = _make_entry(label="updated")
        result = _make_entry_result(entry=entry)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"label": "updated"}

        with patch("apps.web.api.finances.routes.update_entry", return_value=result) as mock_update:
            resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, label="updated")
        body = json.loads(resp.body)
        assert body["label"] == "updated"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_label_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"label": 123}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_owner_id_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"owner_id": True}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_inactive_owner_id_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"owner_id": 99}

        with patch("apps.web.api.finances.routes.get_active_user_by_id", return_value=None):
            resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_amount_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"amount": True}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_detail_mode_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"detail_mode": 123}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_details_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"details": [{"label": "test", "amount": True}]}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_details_not_list_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"details": "not_list"}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detail_item_not_dict_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"details": ["not_dict"]}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detail_missing_label_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"details": [{"label": 123, "amount": 100}]}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_tags_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"tags": "not_list"}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tags_with_non_string_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"tags": [123]}

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.side_effect = json.JSONDecodeError("msg", "", 0)

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_owner_id_update(self, mock_request):
        entry = _make_entry(owner_id=2)
        result = _make_entry_result(entry=entry)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"owner_id": 2}

        with (
            patch(
                "apps.web.api.finances.routes.get_active_user_by_id",
                return_value=_make_user(user_id=2),
            ),
            patch("apps.web.api.finances.routes.update_entry", return_value=result) as mock_update,
        ):
            resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, owner_id=2)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_details_parsing(self, mock_request):
        entry = _make_entry()
        result = _make_entry_result(entry=entry)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"details": [{"label": "A", "amount": 100}]}

        with patch("apps.web.api.finances.routes.update_entry", return_value=result) as mock_update:
            resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, details=[("A", 100)])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_body_not_dict_returns_400(self, mock_request):
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = []

        resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_amount(self, mock_request):
        entry = _make_entry(amount=500)
        result = _make_entry_result(entry=entry)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"amount": 500}

        with patch("apps.web.api.finances.routes.update_entry", return_value=result) as mock_update:
            resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, amount=500)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_detail_mode(self, mock_request):
        entry = _make_entry(detail_mode="top_down")
        result = _make_entry_result(entry=entry)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"detail_mode": "top_down"}

        with patch("apps.web.api.finances.routes.update_entry", return_value=result) as mock_update:
            resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, detail_mode="top_down")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_details(self, mock_request):
        entry = _make_entry()
        result = _make_entry_result(entry=entry)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"details": [{"label": "Sub", "amount": 200}]}

        with patch("apps.web.api.finances.routes.update_entry", return_value=result) as mock_update:
            resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, details=[("Sub", 200)])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_tags(self, mock_request):
        entry = _make_entry()
        result = _make_entry_result(entry=entry)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"tags": ["food"]}

        with patch("apps.web.api.finances.routes.update_entry", return_value=result) as mock_update:
            resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        mock_update.assert_called_once_with(1, tags=["food"])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_service_error_returns_error_response(self, mock_request):
        result = _make_entry_result(status=FinanceOperationStatus.NOT_FOUND)
        mock_request.path_params["id"] = 1
        mock_request.json.return_value = {"label": "updated"}

        with patch("apps.web.api.finances.routes.update_entry", return_value=result):
            resp = await update_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND
        body = json.loads(resp.body)
        assert body["error"] == FinanceOperationStatus.NOT_FOUND.value


class TestFinancesDeleteEntry:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_delete_returns_204(self, mock_request):
        result = _make_entry_result(entry=_make_entry())
        mock_request.path_params["id"] = 1

        with patch("apps.web.api.finances.routes.delete_entry", return_value=result):
            resp = await delete_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.NO_CONTENT

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_not_found_returns_error(self, mock_request):
        result = _make_entry_result(status=FinanceOperationStatus.NOT_FOUND)
        mock_request.path_params["id"] = 1

        with patch("apps.web.api.finances.routes.delete_entry", return_value=result):
            resp = await delete_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND


class TestFinancesConfirmEntry:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_confirm_returns_entry(self, mock_request):
        entry = _make_entry(status="confirmed")
        result = _make_entry_result(entry=entry)
        mock_request.path_params["id"] = 1

        with patch("apps.web.api.finances.routes.confirm_entry", return_value=result):
            resp = await confirm_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert body["status"] == "confirmed"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_not_found_returns_error(self, mock_request):
        result = _make_entry_result(status=FinanceOperationStatus.NOT_FOUND)
        mock_request.path_params["id"] = 1

        with patch("apps.web.api.finances.routes.confirm_entry", return_value=result):
            resp = await confirm_entry_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.NOT_FOUND


class TestFinancesListTags:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_tags(self, mock_request):
        tags = [_make_tag(), _make_tag(tag_id=2, name="tag2")]
        with patch("apps.web.api.finances.routes.list_tags", return_value=tags):
            resp = await list_tags_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        body = json.loads(resp.body)
        assert len(body) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_list(self, mock_request):
        with patch("apps.web.api.finances.routes.list_tags", return_value=[]):
            resp = await list_tags_endpoint(mock_request)

        assert resp.status_code == HTTPStatus.OK
        assert json.loads(resp.body) == []
