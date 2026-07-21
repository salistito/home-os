import pytest

from datetime import date
from unittest.mock import patch


from modules.tasks.errors import TaskAlreadyExistsError
from modules.tasks.service import (
    create_task,
    fail_stale_pending_assignments,
    get_daily_assignments,
    get_daily_points,
    get_daily_task_breakdown,
    get_day_board,
    get_month_points,
    get_pending_daily_assignments,
    mark_assignment_done,
    soft_delete_active_task,
    update_active_task,
)
from modules.tasks.types import (
    Assignment,
    AssignmentCompletionStatus,
    Task,
    TaskOperationStatus,
)
from modules.users.types import User


@pytest.fixture
def mock_task():
    return Task(1, "Clean", 5, 7, "2026-03-15")


@pytest.fixture
def mock_assignment():
    return Assignment(1, "Clean", 1, 5)


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_create_task_success(mock_repo, mock_task):
    mock_repo.create_task.return_value = mock_task
    result = create_task("Clean", 5)

    assert result.status == TaskOperationStatus.OK
    assert result.task == mock_task
    mock_repo.create_task.assert_called_once_with("Clean", 5, None, None)


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_create_task_empty_name(mock_repo):
    result = create_task("", 5)

    assert result.status == TaskOperationStatus.INVALID_NAME


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_create_task_zero_points(mock_repo):
    result = create_task("Clean", 0)

    assert result.status == TaskOperationStatus.INVALID_POINTS


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_create_task_negative_frequency(mock_repo):
    result = create_task("Clean", 5, -1)

    assert result.status == TaskOperationStatus.INVALID_FREQUENCY


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_create_task_duplicate_name(mock_repo, mock_task):
    mock_repo.create_task.side_effect = TaskAlreadyExistsError(mock_task)
    result = create_task("Dup", 5)

    assert result.status == TaskOperationStatus.DUPLICATE_NAME
    assert result.task == mock_task


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_update_active_task_success(mock_repo, mock_task):
    mock_repo.get_active_task_by_id.return_value = mock_task
    mock_repo.get_active_task_by_name.return_value = None
    result = update_active_task(1, name="New")

    assert result.status == TaskOperationStatus.OK


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_update_active_task_not_found(mock_repo):
    mock_repo.get_active_task_by_id.return_value = None
    result = update_active_task(9999, name="X")

    assert result.status == TaskOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_update_active_task_empty_name(mock_repo, mock_task):
    mock_repo.get_active_task_by_id.return_value = mock_task
    result = update_active_task(1, name="")

    assert result.status == TaskOperationStatus.INVALID_NAME


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_update_active_task_duplicate_name(mock_repo, mock_task):
    existing = Task(2, "Existing", 5, 7, "2026-03-15")
    mock_repo.get_active_task_by_id.return_value = mock_task
    mock_repo.get_active_task_by_name.return_value = existing
    result = update_active_task(1, name="Existing")

    assert result.status == TaskOperationStatus.DUPLICATE_NAME


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_update_active_task_zero_points(mock_repo, mock_task):
    mock_repo.get_active_task_by_id.return_value = mock_task
    result = update_active_task(1, points=0)

    assert result.status == TaskOperationStatus.INVALID_POINTS


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_update_active_task_zero_frequency(mock_repo, mock_task):
    mock_repo.get_active_task_by_id.return_value = mock_task
    result = update_active_task(1, frequency_days=0)

    assert result.status == TaskOperationStatus.INVALID_FREQUENCY


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_soft_delete_active_task_success(mock_repo, mock_task):
    mock_repo.get_active_task_by_id.return_value = mock_task
    mock_repo.task_has_pending_assignments.return_value = False
    result = soft_delete_active_task(1)

    assert result.status == TaskOperationStatus.OK


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_soft_delete_active_task_not_found(mock_repo):
    mock_repo.get_active_task_by_id.return_value = None
    result = soft_delete_active_task(9999)

    assert result.status == TaskOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_soft_delete_active_task_has_assignments(mock_repo, mock_task):
    mock_repo.get_active_task_by_id.return_value = mock_task
    mock_repo.task_has_pending_assignments.return_value = True
    result = soft_delete_active_task(1)

    assert result.status == TaskOperationStatus.HAS_ASSIGNMENTS


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_get_daily_assignments_existing(mock_repo, mock_assignment):
    day = date(2026, 3, 15)
    mock_repo.get_day_assignments.return_value = [mock_assignment]
    result = get_daily_assignments(day)

    assert result == [mock_assignment]


@pytest.mark.unit
@patch("modules.tasks.service.random")
@patch("modules.tasks.service.get_active_users")
@patch("modules.tasks.service.get_users")
@patch("modules.tasks.service.repository")
def test_get_daily_assignments_creates_new(
    mock_repo, mock_get_users, mock_get_active, mock_rand, mock_task
):
    day = date(2026, 3, 15)
    user = User(1, "Test", "admin")
    due_task = mock_task

    mock_repo.get_day_assignments.return_value = []
    mock_get_active.return_value = [user]
    mock_repo.month_points_by_user.return_value = {}
    mock_repo.get_due_scheduled_tasks.return_value = [due_task]
    mock_rand.choice.return_value = user

    result = get_daily_assignments(day)

    assert len(result) == 1
    mock_repo.create_assignment.assert_called_once_with(due_task.id, user.id, day)


@pytest.mark.unit
@patch("modules.tasks.service.get_active_users")
@patch("modules.tasks.service.repository")
def test_get_daily_assignments_no_users(mock_repo, mock_get_active):
    day = date(2026, 3, 15)
    mock_repo.get_day_assignments.return_value = []
    mock_get_active.return_value = []

    result = get_daily_assignments(day)

    assert result == []


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_mark_assignment_done_success(mock_repo, mock_task):
    day = date(2026, 3, 15)
    mock_repo.get_active_task_by_name.return_value = mock_task
    mock_repo.get_completed_assignment_id.return_value = None
    mock_repo.get_pending_assignment_id.return_value = 1

    result = mark_assignment_done("Clean", 1, day)

    assert result.status == AssignmentCompletionStatus.OK
    assert result.points_awarded == 5


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_mark_assignment_done_not_found(mock_repo):
    day = date(2026, 3, 15)
    mock_repo.get_active_task_by_name.return_value = None

    result = mark_assignment_done("unknown", 1, day)

    assert result.status == AssignmentCompletionStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_mark_assignment_done_already_done(mock_repo, mock_task):
    day = date(2026, 3, 15)
    mock_repo.get_active_task_by_name.return_value = mock_task
    mock_repo.get_completed_assignment_id.return_value = 5

    result = mark_assignment_done("Clean", 1, day)

    assert result.status == AssignmentCompletionStatus.ALREADY_DONE


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_mark_assignment_done_scheduled_completes_pending(mock_repo, mock_task):
    day = date(2026, 3, 15)
    mock_repo.get_active_task_by_name.return_value = mock_task
    mock_repo.get_completed_assignment_id.return_value = None
    mock_repo.get_pending_assignment_id.return_value = 42

    result = mark_assignment_done("Clean", 1, day)

    mock_repo.complete_assignment.assert_called_once_with(42, 1, 5, "2026-03-15")
    mock_repo.set_task_next_due_date.assert_called_once()
    assert result.status == AssignmentCompletionStatus.OK


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_mark_assignment_done_occasional_creates_completed(mock_repo):
    day = date(2026, 3, 15)
    occasional = Task(2, "One-off", 10, None, None)
    mock_repo.get_active_task_by_name.return_value = occasional
    mock_repo.get_completed_assignment_id.return_value = None

    result = mark_assignment_done("One-off", 1, day)

    mock_repo.create_completed_assignment.assert_called_once_with(2, 1, 10, day, "2026-03-15")
    assert result.status == AssignmentCompletionStatus.OK


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_get_pending_daily_assignments_delegates(mock_repo):
    day = date(2026, 3, 15)
    mock_repo.get_pending_daily_assignments.return_value = []
    result = get_pending_daily_assignments(day)

    mock_repo.get_pending_daily_assignments.assert_called_once_with(day)
    assert result == []


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_fail_stale_pending_assignments_delegates(mock_repo):
    day = date(2026, 3, 15)
    mock_repo.fail_stale_pending_assignments.return_value = 3
    result = fail_stale_pending_assignments(day)

    assert result == 3
    mock_repo.fail_stale_pending_assignments.assert_called_once_with(day)


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_get_month_points_delegates(mock_repo):
    mock_repo.month_points_by_user.return_value = {1: 50}
    result = get_month_points("2026-03")

    assert result == {1: 50}


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_get_daily_points_delegates(mock_repo):
    expected = {"2026-03-15": {1: 10}}
    mock_repo.daily_points_by_user.return_value = expected
    result = get_daily_points("2026-03")

    assert result == expected


@pytest.mark.unit
@patch("modules.tasks.service.repository")
def test_get_daily_task_breakdown_delegates(mock_repo):
    expected = {"2026-03-15": {1: [{"name": "Clean", "points": 5}]}}
    mock_repo.daily_task_breakdown_by_user.return_value = expected
    result = get_daily_task_breakdown("2026-03")

    assert result == expected


@pytest.mark.unit
@patch("modules.tasks.service.get_users")
@patch("modules.tasks.service.repository")
def test_get_day_board(mock_repo, mock_get_users):
    day = date(2026, 3, 15)
    user = User(1, "Test", "admin")
    mock_get_users.return_value = [user]
    mock_repo.get_day_assignment_states.return_value = [
        {"task_id": 1, "task_name": "Clean", "user_id": 1, "points": 5, "status": "completed"}
    ]

    board = get_day_board(day)

    assert 1 in board
    assert board[1][0]["done"] is True
