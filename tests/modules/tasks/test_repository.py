from datetime import date

import pytest

import modules.tasks.repository as repository
import modules.users.repository as users_repository
from modules.tasks.errors import TaskAlreadyExistsError


@pytest.fixture
def task_user(db):
    return users_repository.create_user("Task User")


@pytest.fixture
def task_user2(db):
    return users_repository.create_user("Task User 2")


@pytest.fixture
def db_task(db, frozen_today):
    return repository.create_task("Clean", 5, 7, "2026-03-15")


@pytest.mark.integration
def test_create_task(db, frozen_today):
    task = repository.create_task("Clean", 5, 7, "2026-03-15")

    assert task.name == "Clean"
    assert task.points == 5
    assert task.frequency_days == 7
    assert task.next_due_date == "2026-03-15"


@pytest.mark.integration
def test_create_duplicate_task_raises(db, frozen_today):
    repository.create_task("clean", 5, 7, "2026-03-15")

    with pytest.raises(TaskAlreadyExistsError):
        repository.create_task("clean", 5, 7, "2026-03-15")


@pytest.mark.integration
def test_get_active_task_by_id_finds(db, db_task):
    task = repository.get_active_task_by_id(db_task.id)

    assert task is not None
    assert task.id == db_task.id


@pytest.mark.integration
def test_get_active_task_by_id_nonexistent(db):
    result = repository.get_active_task_by_id(9999)

    assert result is None


@pytest.mark.integration
def test_get_active_task_by_name_finds(db, db_task):
    task = repository.get_active_task_by_name("clean")

    assert task is not None
    assert task.id == db_task.id


@pytest.mark.integration
def test_get_active_tasks_lists(db, db_task):
    tasks = repository.get_active_tasks()

    assert any(t.id == db_task.id for t in tasks)


@pytest.mark.integration
def test_get_due_scheduled_tasks_returns_due(db, db_task, frozen_today):
    tasks = repository.get_due_scheduled_tasks(date(2026, 3, 15))

    assert any(t.id == db_task.id for t in tasks)


@pytest.mark.integration
def test_get_due_scheduled_tasks_before_due(db, db_task):
    tasks = repository.get_due_scheduled_tasks(date(2026, 3, 14))

    assert not any(t.id == db_task.id for t in tasks)


@pytest.mark.integration
def test_update_active_task_name(db, db_task):
    result = repository.update_active_task(db_task.id, name="New name")
    task = repository.get_active_task_by_id(db_task.id)

    assert result is True
    assert task.name == "New name"


@pytest.mark.integration
def test_update_active_task_nonexistent(db):
    result = repository.update_active_task(9999, name="x")

    assert result is False


@pytest.mark.integration
def test_update_active_task_invalid_field(db, db_task):
    with pytest.raises(ValueError):
        repository.update_active_task(db_task.id, invalid="x")


@pytest.mark.integration
def test_set_task_next_due_date(db, db_task):
    result = repository.set_task_next_due_date(db_task.id, "2026-03-22")
    task = repository.get_active_task_by_id(db_task.id)

    assert result is True
    assert task.next_due_date == "2026-03-22"


@pytest.mark.integration
def test_soft_delete_active_task(db, db_task):
    result = repository.soft_delete_active_task(db_task.id)
    task = repository.get_active_task_by_id(db_task.id)

    assert result is True
    assert task is None


@pytest.mark.integration
def test_soft_delete_active_task_deletes_pending_assignments(db, db_task, task_user, frozen_today):
    day = date(2026, 3, 15)
    repository.create_assignment(db_task.id, task_user.id, day)
    assert repository.get_pending_assignment_id(db_task.id) is not None

    result = repository.soft_delete_active_task(db_task.id)

    assert result is True
    assert repository.get_pending_assignment_id(db_task.id) is None
    assert repository.get_day_assignments(day) == []


@pytest.mark.integration
def test_soft_delete_active_task_keeps_completed_assignments(db, db_task, task_user):
    repository.create_completed_assignment(
        db_task.id, task_user.id, 5, date(2026, 3, 15), "2026-03-15"
    )

    result = repository.soft_delete_active_task(db_task.id)

    assert result is True
    assert repository.get_completed_assignment_id(db_task.id, date(2026, 3, 15)) is not None


@pytest.mark.integration
def test_soft_delete_active_task_nonexistent(db):
    result = repository.soft_delete_active_task(9999)

    assert result is False


@pytest.mark.integration
def test_create_assignment(db, db_task, task_user, frozen_today):
    day = date(2026, 3, 15)
    repository.create_assignment(db_task.id, task_user.id, day)
    assignments = repository.get_day_assignments(day)

    assert any(a.task_id == db_task.id and a.user_id == task_user.id for a in assignments)


@pytest.mark.integration
def test_create_completed_assignment(db, db_task, task_user, frozen_today):
    day = date(2026, 3, 15)
    repository.create_completed_assignment(db_task.id, task_user.id, 10, day, "2026-03-15")


@pytest.mark.integration
def test_get_day_assignments(db, db_task, task_user, frozen_today):
    day = date(2026, 3, 15)
    repository.create_assignment(db_task.id, task_user.id, day)
    assignments = repository.get_day_assignments(day)

    assert len(assignments) >= 1


@pytest.mark.integration
def test_get_day_assignment_states(db, db_task, task_user, frozen_today):
    day = date(2026, 3, 15)
    repository.create_assignment(db_task.id, task_user.id, day)
    states = repository.get_day_assignment_states(day)

    assert any(s["task_id"] == db_task.id for s in states)


@pytest.mark.integration
def test_get_pending_daily_assignments(db, db_task, task_user, frozen_today):
    day = date(2026, 3, 15)
    repository.create_assignment(db_task.id, task_user.id, day)
    assignments = repository.get_pending_daily_assignments(day)

    assert any(a.task_id == db_task.id for a in assignments)


@pytest.mark.integration
def test_get_pending_assignment_id(db, db_task, task_user, frozen_today):
    repository.create_assignment(db_task.id, task_user.id, date(2026, 3, 15))
    assign_id = repository.get_pending_assignment_id(db_task.id)

    assert assign_id is not None


@pytest.mark.integration
def test_get_pending_assignment_returns_full_row(db, db_task, task_user, frozen_today):
    repository.create_assignment(db_task.id, task_user.id, date(2026, 3, 15))
    result = repository.get_pending_assignment(db_task.id)

    assert result is not None
    assert result["id"] is not None
    assert result["task_id"] == db_task.id
    assert result["user_id"] == task_user.id
    assert result["status"] == "pending"


@pytest.mark.integration
def test_get_completed_assignment_id_returns_none_for_pending(db, db_task, task_user, frozen_today):
    day = date(2026, 3, 15)
    repository.create_assignment(db_task.id, task_user.id, day)
    result = repository.get_completed_assignment_id(db_task.id, day)

    assert result is None


@pytest.mark.integration
def test_complete_assignment(db, db_task, task_user, frozen_today):
    repository.create_assignment(db_task.id, task_user.id, date(2026, 3, 15))
    assign_id = repository.get_pending_assignment_id(db_task.id)
    result = repository.complete_assignment(assign_id, task_user.id, 10, "2026-03-15")

    assert result is True


@pytest.mark.integration
def test_fail_stale_pending_assignments(db, db_task, task_user):
    repository.create_assignment(db_task.id, task_user.id, date(2026, 3, 10))
    count = repository.fail_stale_pending_assignments(date(2026, 3, 15))

    assert count >= 1


@pytest.mark.integration
def test_month_points_by_user(db, db_task, task_user):
    result = repository.month_points_by_user("2026-03")

    assert task_user.id in result


@pytest.mark.integration
def test_daily_points_by_user(db):
    result = repository.daily_points_by_user("2026-03")

    assert isinstance(result, dict)


@pytest.mark.integration
def test_daily_task_breakdown_by_user(db):
    result = repository.daily_task_breakdown_by_user("2026-03")

    assert isinstance(result, dict)


@pytest.mark.integration
def test_update_active_task_no_fields_returns_true(db, db_task):
    result = repository.update_active_task(db_task.id)

    assert result is True


@pytest.mark.integration
def test_update_active_task_sets_column_to_null(db, db_task):
    result = repository.update_active_task(db_task.id, next_due_date=None)
    task = repository.get_active_task_by_id(db_task.id)

    assert result is True
    assert task.next_due_date is None


@pytest.mark.integration
def test_update_active_task_duplicate_name_raises_task_already_exists(db, db_task):
    task_b = repository.create_task("Task B", 5, None, None)

    with pytest.raises(TaskAlreadyExistsError):
        repository.update_active_task(task_b.id, name="Clean")


@pytest.mark.integration
def test_daily_points_by_user_groups_by_day_and_user(db, db_user):
    task = repository.create_task("Task X", 10, None, None)
    repository.create_completed_assignment(task.id, db_user.id, 10, date(2026, 3, 15), "2026-03-15")

    result = repository.daily_points_by_user("2026-03")

    assert "2026-03-15" in result
    assert result["2026-03-15"][db_user.id] == 10


@pytest.mark.integration
def test_get_assignment_by_id_found(db, db_task, task_user, frozen_today):
    repository.create_assignment(db_task.id, task_user.id, date(2026, 3, 15))
    assign_id = repository.get_pending_assignment_id(db_task.id)
    result = repository.get_assignment_by_id(assign_id)

    assert result is not None
    assert result["id"] == assign_id
    assert result["task_id"] == db_task.id
    assert result["user_id"] == task_user.id
    assert result["assigned_at"] == "2026-03-15"
    assert result["status"] == "pending"
    assert result["frequency_days"] == 7


@pytest.mark.integration
def test_get_assignment_by_id_not_found(db):
    result = repository.get_assignment_by_id(9999)

    assert result is None


@pytest.mark.integration
def test_complete_assignment_by_id(db, db_task, task_user, frozen_today):
    repository.create_assignment(db_task.id, task_user.id, date(2026, 3, 15))
    assign_id = repository.get_pending_assignment_id(db_task.id)
    result = repository.complete_assignment_by_id(assign_id, "2026-03-15", 5)

    assert result is True
    updated = repository.get_assignment_by_id(assign_id)
    assert updated["status"] == "completed"


@pytest.mark.integration
def test_complete_assignment_by_id_already_completed(db, db_task, task_user, frozen_today):
    repository.create_assignment(db_task.id, task_user.id, date(2026, 3, 15))
    assign_id = repository.get_pending_assignment_id(db_task.id)
    repository.complete_assignment_by_id(assign_id, "2026-03-15", 5)
    result = repository.complete_assignment_by_id(assign_id, "2026-03-16", 5)

    assert result is False


@pytest.mark.integration
def test_revert_assignment_by_id(db, db_task, task_user, frozen_today):
    repository.create_assignment(db_task.id, task_user.id, date(2026, 3, 15))
    assign_id = repository.get_pending_assignment_id(db_task.id)
    repository.complete_assignment_by_id(assign_id, "2026-03-15", 5)
    result = repository.revert_assignment_by_id(assign_id)

    assert result is True
    updated = repository.get_assignment_by_id(assign_id)
    assert updated["status"] == "pending"


@pytest.mark.integration
def test_revert_assignment_by_id_already_pending(db, db_task, task_user, frozen_today):
    repository.create_assignment(db_task.id, task_user.id, date(2026, 3, 15))
    assign_id = repository.get_pending_assignment_id(db_task.id)
    result = repository.revert_assignment_by_id(assign_id)

    assert result is False


@pytest.mark.integration
def test_daily_task_breakdown_by_user_groups(db, db_user):
    task = repository.create_task("Task X", 10, None, None)
    repository.create_completed_assignment(task.id, db_user.id, 10, date(2026, 3, 15), "2026-03-15")

    result = repository.daily_task_breakdown_by_user("2026-03")

    assert "2026-03-15" in result
    assert result["2026-03-15"][db_user.id][0]["name"] == "Task x"
    assert result["2026-03-15"][db_user.id][0]["points"] == 10


@pytest.mark.integration
def test_get_cooking_task_creates_single_task(db):
    task = repository.get_cooking_task()
    task2 = repository.get_cooking_task()

    assert task.id == task2.id
    assert task.name == "Cocinar"
    assert task.points == 2
    assert [t.name for t in repository.get_active_tasks()] == ["Cocinar"]


@pytest.mark.integration
def test_create_cooking_assignment_counts_in_points(db, db_user, frozen_today):
    task = repository.get_cooking_task()
    details = {
        "recipe_name": "Pescado",
        "recipe_category": "Cena",
        "portions": 4,
        "cooked_at": "2026-03-15",
    }
    repository.create_cooking_assignment(
        task.id, db_user.id, "2026-03-15", "2026-03-15", 2, 1, details
    )

    points = repository.month_points_by_user("2026-03")

    assert points[db_user.id] == 2


@pytest.mark.integration
def test_create_cooking_assignment_in_daily_breakdown(db, db_user, frozen_today):
    task = repository.get_cooking_task()
    details = {
        "recipe_name": "Pescado",
        "recipe_category": "Cena",
        "portions": 4,
        "cooked_at": "2026-03-15",
    }
    repository.create_cooking_assignment(
        task.id, db_user.id, "2026-03-15", "2026-03-15", 2, 1, details
    )

    result = repository.daily_task_breakdown_by_user("2026-03")

    item = result["2026-03-15"][db_user.id][0]
    assert item["name"] == "Cocinar"
    assert item["points"] == 2
    assert item["source_entity_id"] == 1
    assert item["source_entity_details"] == details


@pytest.mark.integration
def test_get_day_assignments_excludes_cooking(db, db_user, frozen_today):
    day = date(2026, 3, 15)
    task = repository.get_cooking_task()
    details = {
        "recipe_name": "Pescado",
        "recipe_category": "Cena",
        "portions": 4,
        "cooked_at": "2026-03-15",
    }
    repository.create_cooking_assignment(
        task.id, db_user.id, "2026-03-15", "2026-03-15", 2, 1, details
    )

    assignments = repository.get_day_assignments(day)

    assert not any(a.task_id == task.id for a in assignments)


@pytest.mark.integration
def test_get_day_assignment_states_includes_cooking_details(db, db_user, frozen_today):
    day = date(2026, 3, 15)
    task = repository.get_cooking_task()
    details = {
        "recipe_name": "Pescado",
        "recipe_category": "Cena",
        "portions": 4,
        "cooked_at": "2026-03-15",
    }
    repository.create_cooking_assignment(
        task.id, db_user.id, "2026-03-15", "2026-03-15", 2, 1, details
    )

    states = repository.get_day_assignment_states(day)

    cooking = [s for s in states if s["source"] == "cooking"]
    assert len(cooking) == 1
    assert cooking[0]["source_entity_id"] == 1
    assert cooking[0]["source_entity_details"] == details


@pytest.mark.integration
def test_get_assignment_by_id_includes_cooking_details(db, db_user, frozen_today):
    task = repository.get_cooking_task()
    details = {
        "recipe_name": "Pescado",
        "recipe_category": "Cena",
        "portions": 4,
        "cooked_at": "2026-03-15",
    }
    repository.create_cooking_assignment(
        task.id, db_user.id, "2026-03-15", "2026-03-15", 2, 1, details
    )

    row = repository.get_assignment_by_id(1)

    assert row["source"] == "cooking"
    assert row["source_entity_id"] == 1
    assert row["source_entity_details"] == details
