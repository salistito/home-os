import pytest

from apps.bots.telegram.handlers.utils.tasks import (
    parse_add_task_args,
    parse_edit_task_args,
    parse_delete_task_args,
    coerce_edit_value,
    add_task_reply,
    update_task_reply,
    delete_task_reply,
)
from modules.tasks.types import Task, TaskOperationResult, TaskOperationStatus


def _make_task(task_id=1, name="Task", points=10, frequency_days=None, next_due_date=None):
    return Task(
        id=task_id,
        name=name,
        points=points,
        frequency_days=frequency_days,
        next_due_date=next_due_date,
    )


def _make_result(task=None, status=TaskOperationStatus.OK):
    return TaskOperationResult(task=task, status=status)


class TestParseAddTaskArgs:
    @pytest.mark.unit
    def test_name_and_points(self):
        result = parse_add_task_args("/add_task Clean 5")
        assert result == ("Clean", 5, None, None)

    @pytest.mark.unit
    def test_name_points_frequency(self):
        result = parse_add_task_args("/add_task Wash the dishes 5 7")
        assert result == ("Wash the dishes", 5, 7, None)

    @pytest.mark.unit
    def test_name_points_frequency_date(self):
        result = parse_add_task_args("/add_task Wash the dishes 5 7 2026-03-15")
        assert result == ("Wash the dishes", 5, 7, "2026-03-15")

    @pytest.mark.unit
    def test_name_points_date_only(self):
        result = parse_add_task_args("/add_task Wash the dishes 5 2026-03-15")
        assert result == ("Wash the dishes", 5, None, "2026-03-15")

    @pytest.mark.unit
    def test_not_enough_args(self):
        assert parse_add_task_args("/add_task Clean") is None
        assert parse_add_task_args("/add_task") is None

    @pytest.mark.unit
    def test_invalid_points(self):
        assert parse_add_task_args("/add_task Clean abc") is None

    @pytest.mark.unit
    def test_multi_word_name(self):
        result = parse_add_task_args("/add_task Wash the dishes 10")
        assert result == ("Wash the dishes", 10, None, None)

    @pytest.mark.unit
    def test_invalid_frequency_with_date_cascade(self):
        result = parse_add_task_args("/add_task Clean 5 bad 2026-03-15")
        assert result is None


class TestParseEditTaskArgs:
    @pytest.mark.unit
    def test_valid_args(self):
        result = parse_edit_task_args("/edit_task Clean name Wash")
        assert result == ("Clean", "name", "Wash")

    @pytest.mark.unit
    def test_invalid_not_enough_args(self):
        assert parse_edit_task_args("/edit_task Clean name") is None

    @pytest.mark.unit
    def test_field_not_found(self):
        assert parse_edit_task_args("/edit_task Clean bad value") is None

    @pytest.mark.unit
    def test_multi_word_name(self):
        result = parse_edit_task_args("/edit_task Wash the dishes name Clean dishes")
        assert result == ("Wash the dishes", "name", "Clean dishes")


class TestParseDeleteTaskArgs:
    @pytest.mark.unit
    def test_valid_args(self):
        result = parse_delete_task_args("/delete_task Clean")
        assert result == "Clean"

    @pytest.mark.unit
    def test_no_args(self):
        assert parse_delete_task_args("/delete_task") is None

    @pytest.mark.unit
    def test_multi_word_name(self):
        result = parse_delete_task_args("/delete_task Wash the dishes")
        assert result == "Wash the dishes"


class TestCoerceEditValue:
    @pytest.mark.unit
    def test_points_int(self):
        assert coerce_edit_value("points", "10") == 10

    @pytest.mark.unit
    def test_frequency_days_int(self):
        assert coerce_edit_value("frequency_days", "7") == 7

    @pytest.mark.unit
    def test_frequency_days_zero_returns_none(self):
        assert coerce_edit_value("frequency_days", "0") is None

    @pytest.mark.unit
    def test_frequency_days_dash_returns_none(self):
        assert coerce_edit_value("frequency_days", "-") is None

    @pytest.mark.unit
    def test_next_due_date_valid(self):
        assert coerce_edit_value("next_due_date", "2026-03-15") == "2026-03-15"

    @pytest.mark.unit
    def test_next_due_date_invalid_raises(self):
        with pytest.raises(ValueError):
            coerce_edit_value("next_due_date", "not-a-date")

    @pytest.mark.unit
    def test_name_passthrough(self):
        assert coerce_edit_value("name", "New Name") == "New Name"


class TestAddTaskReply:
    @pytest.mark.unit
    def test_ok(self):
        task = _make_task()
        result = _make_result(task=task, status=TaskOperationStatus.OK)
        reply = add_task_reply(result)
        assert task.name in reply

    @pytest.mark.unit
    def test_invalid_name(self):
        result = _make_result(status=TaskOperationStatus.INVALID_NAME)
        assert "nombre" in add_task_reply(result)

    @pytest.mark.unit
    def test_invalid_points(self):
        result = _make_result(status=TaskOperationStatus.INVALID_POINTS)
        assert "puntos" in add_task_reply(result)

    @pytest.mark.unit
    def test_invalid_frequency(self):
        result = _make_result(status=TaskOperationStatus.INVALID_FREQUENCY)
        assert "frecuencia" in add_task_reply(result)

    @pytest.mark.unit
    def test_duplicate_name(self):
        task = _make_task(name="Dup")
        result = _make_result(task=task, status=TaskOperationStatus.DUPLICATE_NAME)
        assert "Dup" in add_task_reply(result)


class TestUpdateTaskReply:
    @pytest.mark.unit
    def test_ok(self):
        task = _make_task(name="NewName")
        result = _make_result(task=task, status=TaskOperationStatus.OK)
        reply = update_task_reply(result, "OldName", "name", "OldName", "NewName")
        assert "NewName" in reply or "actualizada" in reply

    @pytest.mark.unit
    def test_not_found(self):
        result = _make_result(status=TaskOperationStatus.NOT_FOUND)
        reply = update_task_reply(result, "Missing", "name", "Missing", "New")
        assert "Missing" in reply

    @pytest.mark.unit
    def test_invalid_name(self):
        result = _make_result(status=TaskOperationStatus.INVALID_NAME)
        reply = update_task_reply(result, "Task", "name", "Task", "")
        assert "nombre" in reply

    @pytest.mark.unit
    def test_invalid_points(self):
        result = _make_result(status=TaskOperationStatus.INVALID_POINTS)
        reply = update_task_reply(result, "Task", "points", "5", "bad")
        assert "puntos" in reply

    @pytest.mark.unit
    def test_invalid_frequency(self):
        result = _make_result(status=TaskOperationStatus.INVALID_FREQUENCY)
        reply = update_task_reply(result, "Task", "freq", "5", "bad")
        assert "frecuencia" in reply

    @pytest.mark.unit
    def test_duplicate_name(self):
        task = _make_task(name="Dup")
        result = _make_result(task=task, status=TaskOperationStatus.DUPLICATE_NAME)
        reply = update_task_reply(result, "Dup", "name", "Old", "Dup")
        assert "Dup" in reply


class TestDeleteTaskReply:
    @pytest.mark.unit
    def test_ok(self):
        task = _make_task(name="Deleted")
        result = _make_result(task=task, status=TaskOperationStatus.OK)
        reply = delete_task_reply(result, "Deleted")
        assert "Deleted" in reply

    @pytest.mark.unit
    def test_not_found(self):
        result = _make_result(status=TaskOperationStatus.NOT_FOUND)
        reply = delete_task_reply(result, "Missing")
        assert "Missing" in reply

    @pytest.mark.unit
    def test_has_assignments(self):
        task = _make_task(name="MyTask")
        result = _make_result(task=task, status=TaskOperationStatus.HAS_ASSIGNMENTS)
        reply = delete_task_reply(result, "MyTask")
        assert "Mytask" in reply
