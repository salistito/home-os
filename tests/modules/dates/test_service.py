from unittest.mock import patch

import pytest

import modules.dates.repository as repository
from modules.dates.service import (
    add_memory,
    complete_event,
    create_couple,
    create_event,
    create_milestone,
    delete_couple,
    delete_event,
    delete_memory,
    delete_milestone,
    get_couples,
    get_event_detail,
    is_valid_reveal_on,
    list_events,
    list_memories,
    list_milestones,
    update_couple,
    update_event,
    who_plans_next,
)
from modules.dates.types import (
    DateAttribute,
    DateCouple,
    DateEvent,
    DateMemory,
    DateMilestone,
    DateOperationStatus,
)


def _couple(member_ids=(1, 2)):
    return DateCouple(
        id=1,
        member_ids=list(member_ids),
        started_at="2026-03-15",
        relationship_status="couple",
        status="active",
        created_at="2026-03-15",
        updated_at="2026-03-15",
    )


def _event(planned_by=1, **kwargs):
    return DateEvent(
        id=10,
        couple_id=1,
        week_start="2026-03-16",
        planned_by=planned_by,
        attributes=[],
        **kwargs,
    )


@pytest.fixture
def mock_repo():
    with patch("modules.dates.service.repository") as m, patch(
        "modules.dates.service.get_active_user_by_id", return_value=object()
    ):
        m.get_couple_by_id.return_value = _couple()
        m.get_last_event.return_value = None
        m.create_event.return_value = _event()
        m.get_event_by_id.return_value = _event()
        m.create_memory.return_value = DateMemory(1, 10, "photo")
        yield m


@pytest.fixture
def mock_reminders():
    with patch(
        "modules.dates.service.create_system_reminder"
    ) as create, patch(
        "modules.dates.service.delete_system_reminders_by_entity"
    ) as delete:
        yield create, delete


# reveal_on validation


def test_is_valid_reveal_on():
    assert is_valid_reveal_on(None)
    assert is_valid_reveal_on("2026-03-16")
    assert is_valid_reveal_on("2026-03-16T18:00")
    assert not is_valid_reveal_on("2026-16-03")
    assert not is_valid_reveal_on("2026-03-16 18:00")
    assert not is_valid_reveal_on("")


# Couples


def test_create_couple_ok(mock_repo):
    mock_repo.get_couple_by_id.return_value = _couple()
    mock_repo.create_couple.return_value = _couple()
    result = create_couple([1, 2], started_at="2026-03-15", relationship_status="married")
    assert result.status is DateOperationStatus.OK
    mock_repo.replace_couple_members.assert_called_once_with(1, [1, 2])
    call_kwargs = mock_repo.create_couple.call_args.kwargs
    assert call_kwargs["started_at"] == "2026-03-15"
    assert call_kwargs["relationship_status"] == "married"


def test_create_couple_invalid_started_at(mock_repo):
    result = create_couple([1], started_at="2026-03-16 18:00")
    assert result.status is DateOperationStatus.INVALID_STARTED_AT


def test_create_couple_invalid_relationship_status(mock_repo):
    result = create_couple([1], relationship_status="single")
    assert result.status is DateOperationStatus.INVALID_RELATIONSHIP_STATUS


def test_create_couple_empty_members(mock_repo):
    result = create_couple([])
    assert result.status is DateOperationStatus.EMPTY_MEMBERS


def test_create_couple_invalid_member(mock_repo):
    with patch("modules.dates.service.get_active_user_by_id", return_value=None):
        result = create_couple([99])
    assert result.status is DateOperationStatus.INVALID_MEMBERS


def test_get_couples_active_only(mock_repo):
    mock_repo.get_couples.return_value = [_couple()]
    result = get_couples()
    assert result.status is DateOperationStatus.OK
    assert len(result.couples) == 1
    mock_repo.get_couples.assert_called_once_with(status="active")


def test_get_couples_include_archived(mock_repo):
    mock_repo.get_couples.return_value = [_couple()]
    result = get_couples(include_archived=True)
    assert result.status is DateOperationStatus.OK
    mock_repo.get_couples.assert_called_once_with(status=None)


def test_update_couple_not_found(mock_repo):
    mock_repo.get_couple_by_id.return_value = None
    result = update_couple(1, viewer_user_id=1)
    assert result.status is DateOperationStatus.NOT_FOUND


def test_update_couple_forbidden(mock_repo):
    result = update_couple(1, viewer_user_id=99)
    assert result.status is DateOperationStatus.FORBIDDEN


def test_update_couple_ok(mock_repo):
    result = update_couple(
        1,
        viewer_user_id=1,
        started_at="2025-01-01",
        relationship_status="married",
        status="active",
    )
    assert result.status is DateOperationStatus.OK
    call_kwargs = mock_repo.update_couple.call_args.kwargs
    assert call_kwargs["started_at"] == "2025-01-01"
    assert call_kwargs["relationship_status"] == "married"
    assert call_kwargs["status"] == "active"


def test_update_couple_bad_member(mock_repo):
    with patch("modules.dates.service.get_active_user_by_id", return_value=None):
        result = update_couple(1, viewer_user_id=1, member_ids=[99])
    assert result.status is DateOperationStatus.INVALID_MEMBERS


def test_update_couple_invalid_status(mock_repo):
    result = update_couple(1, viewer_user_id=1, status="deleted")
    assert result.status is DateOperationStatus.INVALID_STATUS


def test_delete_couple_ok(mock_repo):
    result = delete_couple(1)
    assert result.status is DateOperationStatus.OK
    mock_repo.delete_couple.assert_called_once_with(1)


def test_delete_couple_not_found(mock_repo):
    mock_repo.get_couple_by_id.return_value = None
    result = delete_couple(1)
    assert result.status is DateOperationStatus.NOT_FOUND


# Milestones


def _milestone(couple_id=1):
    return DateMilestone(
        id=3,
        couple_id=couple_id,
        type="monthly",
        date="2026-03-15",
        label="Cumple-mes",
        notes=None,
        created_at="2026-03-15",
    )


def test_create_milestone_ok(mock_repo):
    returned = _milestone()
    returned.label = "Aniversario"
    mock_repo.create_milestone.return_value = returned
    result = create_milestone(
        1, 1, milestone_type="anniversary", date="2026-03-15", label="Aniversario"
    )
    assert result.status is DateOperationStatus.OK
    assert result.milestone.label == "Aniversario"


def test_create_milestone_couple_not_found(mock_repo):
    mock_repo.get_couple_by_id.return_value = None
    result = create_milestone(1, 1, "monthly", "2026-03-15", "x")
    assert result.status is DateOperationStatus.NOT_FOUND


def test_create_milestone_forbidden(mock_repo):
    result = create_milestone(1, 99, "monthly", "2026-03-15", "x")
    assert result.status is DateOperationStatus.FORBIDDEN


def test_create_milestone_invalid_type(mock_repo):
    result = create_milestone(1, 1, "birthday", "2026-03-15", "x")
    assert result.status is DateOperationStatus.INVALID_MILESTONE_TYPE


def test_create_milestone_invalid_date(mock_repo):
    result = create_milestone(1, 1, "monthly", "2026-15-03", "x")
    assert result.status is DateOperationStatus.INVALID_MILESTONE_DATE


def test_create_milestone_invalid_label(mock_repo):
    result = create_milestone(1, 1, "monthly", "2026-03-15", "   ")
    assert result.status is DateOperationStatus.INVALID_MILESTONE_LABEL


def test_list_milestones_ok(mock_repo):
    mock_repo.list_milestones.return_value = [_milestone()]
    result = list_milestones(1, 1)
    assert result.status is DateOperationStatus.OK
    assert len(result.milestones) == 1


def test_list_milestones_not_found(mock_repo):
    mock_repo.get_couple_by_id.return_value = None
    result = list_milestones(1, 1)
    assert result.status is DateOperationStatus.NOT_FOUND


def test_list_milestones_forbidden(mock_repo):
    result = list_milestones(1, 99)
    assert result.status is DateOperationStatus.FORBIDDEN


def test_delete_milestone_ok(mock_repo):
    mock_repo.get_milestone_by_id.return_value = _milestone()
    result = delete_milestone(3, 1)
    assert result.status is DateOperationStatus.OK
    mock_repo.delete_milestone.assert_called_once_with(3)


def test_delete_milestone_not_found(mock_repo):
    mock_repo.get_milestone_by_id.return_value = None
    result = delete_milestone(3, 1)
    assert result.status is DateOperationStatus.NOT_FOUND


def test_delete_milestone_forbidden(mock_repo):
    mock_repo.get_milestone_by_id.return_value = _milestone()
    result = delete_milestone(3, 99)
    assert result.status is DateOperationStatus.FORBIDDEN


# who_plans_next


def test_who_plans_next_no_events(mock_repo):
    mock_repo.get_last_event.return_value = None
    assert who_plans_next(1) == 1


def test_who_plans_next_round_robin(mock_repo):
    mock_repo.get_last_event.return_value = _event(planned_by=1)
    assert who_plans_next(1) == 2


def test_who_plans_next_no_couple(mock_repo):
    mock_repo.get_couple_by_id.return_value = None
    assert who_plans_next(1) is None


# Events


def test_create_event_not_found(mock_repo):
    mock_repo.get_couple_by_id.return_value = None
    result = create_event(1, "2026-03-16", viewer_user_id=1)
    assert result.status is DateOperationStatus.NOT_FOUND


def test_create_event_forbidden(mock_repo):
    result = create_event(1, "2026-03-16", viewer_user_id=99)
    assert result.status is DateOperationStatus.FORBIDDEN


def test_create_event_invalid_week(mock_repo):
    result = create_event(1, "2026-16-03", viewer_user_id=1)
    assert result.status is DateOperationStatus.INVALID_WEEK_START


def test_create_event_invalid_planned_by(mock_repo):
    result = create_event(1, "2026-03-16", viewer_user_id=1, planned_by=99)
    assert result.status is DateOperationStatus.INVALID_PLANNED_BY


def test_create_event_invalid_scheduled_time(mock_repo):
    result = create_event(1, "2026-03-16", viewer_user_id=1, scheduled_time="25:99")
    assert result.status is DateOperationStatus.INVALID_SCHEDULED_TIME


def test_create_event_duplicate(mock_repo):
    mock_repo.create_event.side_effect = repository.EventAlreadyExistsError(1, "2026-03-16")
    result = create_event(1, "2026-03-16", viewer_user_id=1)
    assert result.status is DateOperationStatus.DUPLICATE_WEEK


def test_create_event_ok_with_attributes(mock_repo, mock_reminders):
    from datetime import date

    with patch("modules.dates.service.get_today", return_value=date(2026, 3, 15)):
        result = create_event(
            1,
            "2026-03-16",
            viewer_user_id=1,
            attributes=[
                {"key": "place", "value": "X", "is_secret": True, "reveal_on": "2026-03-16"}
            ],
        )
    assert result.status is DateOperationStatus.OK
    mock_repo.replace_event_attributes.assert_called_once()
    create, _ = mock_reminders
    assert create.called


def test_create_event_auto_planned_by(mock_repo):
    mock_repo.get_last_event.return_value = _event(planned_by=2)
    create_event(1, "2026-03-16", viewer_user_id=1)
    call_kwargs = mock_repo.create_event.call_args.kwargs
    assert call_kwargs["planned_by"] == 1


def test_create_event_invalid_attributes(mock_repo):
    result = create_event(
        1, "2026-03-16", viewer_user_id=1, attributes=[{"key": ""}]
    )
    assert result.status is DateOperationStatus.INVALID_ATTRIBUTES


def test_create_event_invalid_reveal_on(mock_repo):
    result = create_event(
        1,
        "2026-03-16",
        viewer_user_id=1,
        attributes=[{"key": "place", "value": "X", "is_secret": True, "reveal_on": "bad"}],
    )
    assert result.status is DateOperationStatus.INVALID_REVEAL_ON


def test_list_events_forbidden(mock_repo):
    result = list_events(viewer_user_id=99, couple_id=1)
    assert result.status is DateOperationStatus.FORBIDDEN


def test_list_events_ok(mock_repo):
    mock_repo.list_events.return_value = [_event()]
    result = list_events(viewer_user_id=1, couple_id=1)
    assert result.status is DateOperationStatus.OK
    assert len(result.events) == 1


def test_list_events_none_couple_filters_visible(mock_repo):
    other = _couple()
    other.id = 2
    mock_repo.get_couples.return_value = [other]
    mock_repo.list_events.return_value = [_event()]
    result = list_events(viewer_user_id=1)
    assert result.status is DateOperationStatus.OK
    assert len(result.events) == 1


def test_get_event_detail_not_found(mock_repo):
    mock_repo.get_event_by_id.return_value = None
    result = get_event_detail(10, 1)
    assert result.status is DateOperationStatus.NOT_FOUND


def test_get_event_detail_forbidden(mock_repo):
    result = get_event_detail(10, 99)
    assert result.status is DateOperationStatus.FORBIDDEN


def test_get_event_detail_hides_secret(mock_repo):
    event = _event()
    event.attributes = [
        DateAttribute(1, 10, "place", "Restaurante", is_secret=True, reveal_on="2099-01-01"),
        DateAttribute(2, 10, "vibes", "romantico", is_secret=False, reveal_on=None),
    ]
    mock_repo.get_event_by_id.return_value = event
    result = get_event_detail(10, 2)
    assert result.status is DateOperationStatus.OK
    keys = [a.key for a in result.event.attributes]
    assert "vibes" in keys
    assert "place" not in keys


def test_get_event_detail_planner_sees_secrets(mock_repo):
    event = _event(planned_by=1)
    event.attributes = [
        DateAttribute(1, 10, "place", "Restaurante", is_secret=True, reveal_on=None)
    ]
    mock_repo.get_event_by_id.return_value = event
    result = get_event_detail(10, 1)
    assert result.status is DateOperationStatus.OK
    assert result.event.attributes[0].key == "place"


def test_update_event_not_found(mock_repo):
    mock_repo.get_event_by_id.return_value = None
    result = update_event(10, 1, title="X")
    assert result.status is DateOperationStatus.NOT_FOUND


def test_update_event_forbidden(mock_repo):
    result = update_event(10, 99, title="X")
    assert result.status is DateOperationStatus.FORBIDDEN


def test_update_event_ok(mock_repo, mock_reminders):
    result = update_event(10, 1, scheduled_date="2026-03-20")
    assert result.status is DateOperationStatus.OK
    mock_repo.update_event.assert_called()


def test_complete_event_ok(mock_repo, mock_reminders):
    result = complete_event(10, 1)
    assert result.status is DateOperationStatus.OK
    _, delete = mock_reminders
    assert delete.called


def test_delete_event_ok(mock_repo, mock_reminders):
    result = delete_event(10, 1)
    assert result.status is DateOperationStatus.OK
    mock_repo.delete_event.assert_called_once_with(10)


def test_delete_event_not_found(mock_repo):
    mock_repo.get_event_by_id.return_value = None
    result = delete_event(10, 1)
    assert result.status is DateOperationStatus.NOT_FOUND


def test_delete_event_forbidden(mock_repo):
    result = delete_event(10, 99)
    assert result.status is DateOperationStatus.FORBIDDEN


# Memories


def test_add_memory_ok(mock_repo):
    result = add_memory(10, 1, "photo", media_url="https://example.com/x.jpg")
    assert result.status is DateOperationStatus.OK


def test_add_memory_photo_requires_url(mock_repo):
    result = add_memory(10, 1, "photo")
    assert result.status is DateOperationStatus.INVALID_MEDIA_URL


def test_add_memory_invalid_kind(mock_repo):
    result = add_memory(10, 1, "video")
    assert result.status is DateOperationStatus.INVALID_KIND


def test_add_memory_invalid_taken_by(mock_repo):
    result = add_memory(10, 1, "photo", media_url="url", taken_by=99)
    assert result.status is DateOperationStatus.INVALID_MEMBERS


def test_add_memory_event_not_found(mock_repo):
    mock_repo.get_event_by_id.return_value = None
    result = add_memory(10, 1, "photo", media_url="url")
    assert result.status is DateOperationStatus.NOT_FOUND


def test_list_memories_ok(mock_repo):
    mock_repo.list_memories.return_value = []
    result = list_memories(10, 1)
    assert result.status is DateOperationStatus.OK


def test_list_memories_forbidden(mock_repo):
    result = list_memories(10, 99)
    assert result.status is DateOperationStatus.FORBIDDEN


def test_delete_memory_ok(mock_repo):
    mock_repo.get_memory_by_id.return_value = DateMemory(5, 10, "note")
    result = delete_memory(5, 1)
    assert result.status is DateOperationStatus.OK
    mock_repo.delete_memory.assert_called_once_with(5)


def test_delete_memory_not_found(mock_repo):
    mock_repo.get_memory_by_id.return_value = None
    result = delete_memory(5, 1)
    assert result.status is DateOperationStatus.NOT_FOUND


def test_delete_memory_forbidden(mock_repo):
    mock_repo.get_memory_by_id.return_value = DateMemory(5, 10, "note")
    result = delete_memory(5, 99)
    assert result.status is DateOperationStatus.FORBIDDEN
