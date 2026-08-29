import pytest

import modules.dates.repository as repository
from modules.dates.errors import EventAlreadyExistsError

_D = "2026-03-15"


@pytest.fixture
def couple(db_user, db_second_user):
    created = repository.create_couple(created_at=_D, updated_at=_D, started_at=_D)
    repository.replace_couple_members(created.id, [db_user.id, db_second_user.id])
    return created


# Couples


@pytest.mark.integration
def test_create_and_get_couple(db, db_user, db_second_user):
    created = repository.create_couple(
        created_at=_D, updated_at=_D, started_at=_D, relationship_status="married"
    )
    repository.replace_couple_members(created.id, [db_user.id, db_second_user.id])

    found = repository.get_couple_by_id(created.id)
    assert found is not None
    assert found.started_at == _D
    assert found.relationship_status == "married"
    assert found.status == "active"
    assert found.created_at == _D
    assert found.updated_at == _D
    assert sorted(found.member_ids) == sorted([db_user.id, db_second_user.id])


@pytest.mark.integration
def test_get_couples_includes_members_and_filters(db, db_user, db_second_user):
    a = repository.create_couple(created_at=_D, updated_at=_D)
    b = repository.create_couple(created_at=_D, updated_at=_D)
    repository.replace_couple_members(a.id, [db_user.id])
    repository.replace_couple_members(b.id, [db_second_user.id])

    active = repository.get_couples()
    assert len(active) == 2
    by_id = {c.id: c for c in active}
    assert by_id[a.id].member_ids == [db_user.id]
    assert by_id[b.id].member_ids == [db_second_user.id]

    repository.update_couple(b.id, _D, status="archived")
    assert len(repository.get_couples()) == 1
    assert len(repository.get_couples(status=None)) == 2


@pytest.mark.integration
def test_update_and_delete_couple(db, couple):
    assert repository.update_couple(
        couple.id, _D, started_at="2025-01-01", relationship_status="married"
    )
    updated = repository.get_couple_by_id(couple.id)
    assert updated.started_at == "2025-01-01"
    assert updated.relationship_status == "married"

    assert repository.update_couple(couple.id, _D, status="archived")
    assert repository.get_couple_by_id(couple.id).status == "archived"

    assert repository.delete_couple(couple.id)
    assert repository.get_couple_by_id(couple.id) is None


@pytest.mark.integration
def test_replace_couple_members(db, couple, db_user, db_second_user):
    repository.replace_couple_members(couple.id, [db_second_user.id])
    assert repository.get_couple_member_ids(couple.id) == [db_second_user.id]


# Milestones


@pytest.mark.integration
def test_create_and_list_milestones(db, couple):
    m = repository.create_milestone(
        couple_id=couple.id,
        milestone_type="anniversary",
        date=_D,
        label="Aniversario de novios",
        created_at=_D,
        notes="3 años",
    )
    assert m.id > 0
    assert m.type == "anniversary"
    assert m.date == _D
    assert m.label == "Aniversario de novios"
    assert m.notes == "3 años"

    assert repository.list_milestones(couple.id)[0].id == m.id


@pytest.mark.integration
def test_get_and_delete_milestone(db, couple):
    m = repository.create_milestone(
        couple_id=couple.id,
        milestone_type="monthly",
        date=_D,
        label="Cumple-mes",
        created_at=_D,
    )
    found = repository.get_milestone_by_id(m.id)
    assert found is not None
    assert found.type == "monthly"

    assert repository.delete_milestone(m.id)
    assert repository.get_milestone_by_id(m.id) is None


# Events


@pytest.mark.integration
def test_create_and_get_event(db, couple, db_user):
    event = repository.create_event(
        couple_id=couple.id,
        week_start="2026-03-16",
        planned_by=db_user.id,
        created_at=_D,
        updated_at=_D,
    )
    assert event.id > 0
    assert event.week_start == "2026-03-16"
    assert event.planned_by == db_user.id
    assert event.status == "planned"

    found = repository.get_event_by_id(event.id)
    assert found is not None
    assert found.couple_id == couple.id


@pytest.mark.integration
def test_create_event_duplicate_week_raises(db, couple, db_user):
    repository.create_event(
        couple_id=couple.id,
        week_start="2026-03-16",
        planned_by=db_user.id,
        created_at=_D,
        updated_at=_D,
    )
    with pytest.raises(EventAlreadyExistsError):
        repository.create_event(
            couple_id=couple.id,
            week_start="2026-03-16",
            planned_by=db_user.id,
            created_at=_D,
            updated_at=_D,
        )


@pytest.mark.integration
def test_update_event(db, couple, db_user, db_second_user):
    event = repository.create_event(
        couple_id=couple.id,
        week_start="2026-03-16",
        planned_by=db_user.id,
        created_at=_D,
        updated_at=_D,
    )
    assert repository.update_event(
        event.id,
        _D,
        planned_by=db_second_user.id,
        scheduled_date="2026-03-20",
        status="scheduled",
    )
    updated = repository.get_event_by_id(event.id)
    assert updated.planned_by == db_second_user.id
    assert updated.scheduled_date == "2026-03-20"
    assert updated.status == "scheduled"


@pytest.mark.integration
def test_list_events_filters(db, couple, db_user):
    repository.create_event(couple.id, "2026-03-16", db_user.id, _D, _D)
    repository.create_event(couple.id, "2026-03-23", db_user.id, _D, _D)
    repository.create_event(couple.id, "2026-04-06", db_user.id, _D, _D)

    all_events = repository.list_events(couple_id=couple.id)
    assert len(all_events) == 3

    filtered = repository.list_events(
        couple_id=couple.id, from_date="2026-03-01", to_date="2026-03-31"
    )
    assert len(filtered) == 2

    couple_filtered = repository.list_events(couple_id=couple.id, from_date="2026-04-01")
    assert len(couple_filtered) == 1


@pytest.mark.integration
def test_get_last_event(db, couple, db_user):
    repository.create_event(couple.id, "2026-03-16", db_user.id, _D, _D)
    repository.create_event(couple.id, "2026-03-23", db_user.id, _D, _D)

    last = repository.get_last_event(couple.id)
    assert last is not None
    assert last.week_start == "2026-03-23"


@pytest.mark.integration
def test_delete_event(db, couple, db_user):
    event = repository.create_event(couple.id, "2026-03-16", db_user.id, _D, _D)
    assert repository.delete_event(event.id)
    assert repository.get_event_by_id(event.id) is None


# Attributes


@pytest.mark.integration
def test_replace_and_get_attributes(db, couple, db_user):
    event = repository.create_event(couple.id, "2026-03-16", db_user.id, _D, _D)
    repository.replace_event_attributes(
        event.id,
        [("place", "Restaurante", True, "2026-03-16"), ("vibes", "romantico", False, None)],
    )
    attrs = repository.get_event_attributes(event.id)
    assert len(attrs) == 2
    place = next(a for a in attrs if a.key == "place")
    assert place.is_secret is True
    assert place.reveal_on == "2026-03-16"

    event_with_attrs = repository.get_event_by_id(event.id)
    assert len(event_with_attrs.attributes) == 2


# Memories


@pytest.mark.integration
def test_create_and_list_memories(db, couple, db_user):
    event = repository.create_event(couple.id, "2026-03-16", db_user.id, _D, _D)
    memory = repository.create_memory(
        event_id=event.id,
        kind="photo",
        created_at=_D,
        media_url="https://example.com/photo.jpg",
        caption="Qué lindo",
        taken_by=db_user.id,
    )
    assert memory.kind == "photo"
    assert memory.media_url == "https://example.com/photo.jpg"

    memories = repository.list_memories(event.id)
    assert len(memories) == 1

    assert repository.delete_memory(memory.id)
    assert repository.list_memories(event.id) == []


@pytest.mark.integration
def test_get_memory_by_id(db, couple, db_user):
    event = repository.create_event(couple.id, "2026-03-16", db_user.id, _D, _D)
    memory = repository.create_memory(event.id, "note", _D, caption="Recuerdo")
    found = repository.get_memory_by_id(memory.id)
    assert found is not None
    assert found.caption == "Recuerdo"


@pytest.mark.integration
def test_couple_delete_cascades(db, couple, db_user):
    event = repository.create_event(couple.id, "2026-03-16", db_user.id, _D, _D)
    repository.replace_event_attributes(event.id, [("place", "X", False, None)])
    repository.create_memory(event.id, "note", _D, caption="m")
    repository.create_milestone(
        couple_id=couple.id,
        milestone_type="custom",
        date=_D,
        label="hito",
        created_at=_D,
    )

    repository.delete_couple(couple.id)

    assert repository.get_event_by_id(event.id) is None
    assert repository.list_events(couple_id=couple.id) == []
    assert repository.list_milestones(couple.id) == []
