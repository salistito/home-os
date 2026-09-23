from datetime import date
from unittest.mock import patch

import pytest

from modules.breaks.service import (
    create_break_period,
    delete_break_period,
    get_active_break_period_for_user,
    get_active_break_period_user_ids,
    get_break_period_by_id,
    get_break_period_summary_by_user,
    get_break_periods,
    is_user_on_break_period,
    serialize_break_period_info,
    serialize_break_period_infos,
    update_break_period,
)
from modules.breaks.types import (
    BreakPeriod,
    BreakPeriodOperationStatus,
)
from modules.users.types import User


def _make_break_period(
    period_id=1,
    label="Vacaciones",
    start_date="2026-03-10",
    end_date=None,
    user_ids=None,
):
    return BreakPeriod(
        id=period_id,
        label=label,
        start_date=start_date,
        end_date=end_date,
        created_at="2026-03-01",
        user_ids=user_ids or [1],
    )


@pytest.mark.unit
@patch("modules.breaks.service.repository")
@patch("modules.breaks.service.get_active_user_by_id")
def test_create_break_period_ok(mock_get_user, mock_repo):
    mock_get_user.return_value = User(1, "Test", "admin")
    mock_repo.create_break_period.return_value = _make_break_period()

    result = create_break_period("Vacaciones", "2026-03-10", "2026-03-20", [1])

    assert result.status == BreakPeriodOperationStatus.OK
    assert result.break_period.id == 1
    mock_repo.create_break_period.assert_called_once()


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_create_break_period_invalid_start_date(mock_repo):
    result = create_break_period("Vacaciones", "not-a-date", None, [1])

    assert result.status == BreakPeriodOperationStatus.INVALID_START_DATE
    mock_repo.create_break_period.assert_not_called()


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_create_break_period_invalid_end_date(mock_repo):
    result = create_break_period("Vacaciones", "2026-03-10", "10/03/2026", [1])

    assert result.status == BreakPeriodOperationStatus.INVALID_END_DATE
    mock_repo.create_break_period.assert_not_called()


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_create_break_period_invalid_date_range(mock_repo):
    result = create_break_period("Vacaciones", "2026-03-20", "2026-03-10", [1])

    assert result.status == BreakPeriodOperationStatus.INVALID_DATE_RANGE
    mock_repo.create_break_period.assert_not_called()


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_create_break_period_invalid_user_ids_empty(mock_repo):
    result = create_break_period("Vacaciones", "2026-03-10", None, [])

    assert result.status == BreakPeriodOperationStatus.INVALID_USER_IDS
    mock_repo.create_break_period.assert_not_called()


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_create_break_period_invalid_user_ids_wrong_type(mock_repo):
    result = create_break_period("Vacaciones", "2026-03-10", None, [1, "a"])

    assert result.status == BreakPeriodOperationStatus.INVALID_USER_IDS
    mock_repo.create_break_period.assert_not_called()


@pytest.mark.unit
@patch("modules.breaks.service.repository")
@patch("modules.breaks.service.get_active_user_by_id")
def test_create_break_period_invalid_user_ids_unknown(mock_get_user, mock_repo):
    mock_get_user.return_value = None

    result = create_break_period("Vacaciones", "2026-03-10", None, [9999])

    assert result.status == BreakPeriodOperationStatus.INVALID_USER_IDS


@pytest.mark.unit
@patch("modules.breaks.service.repository")
@patch("modules.breaks.service.get_active_user_by_id")
def test_create_break_period_blank_label_normalized(mock_get_user, mock_repo):
    mock_get_user.return_value = User(1, "Test", "admin")
    mock_repo.create_break_period.return_value = _make_break_period(label=None)

    result = create_break_period("   ", "2026-03-10", None, [1])

    assert result.status == BreakPeriodOperationStatus.OK
    called_kwargs = mock_repo.create_break_period.call_args.kwargs
    assert called_kwargs["label"] is None


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_period_by_id_ok(mock_repo):
    mock_repo.get_break_period_by_id.return_value = _make_break_period()

    result = get_break_period_by_id(1)

    assert result.status == BreakPeriodOperationStatus.OK
    assert result.break_period.id == 1


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_period_by_id_not_found(mock_repo):
    mock_repo.get_break_period_by_id.return_value = None

    result = get_break_period_by_id(9999)

    assert result.status == BreakPeriodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_periods(mock_repo):
    mock_repo.get_break_periods.return_value = [_make_break_period()]

    periods = get_break_periods()

    assert len(periods) == 1


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_update_break_period_ok(mock_repo):
    mock_repo.get_break_period_by_id.side_effect = [
        _make_break_period(),
        _make_break_period(end_date="2026-03-20"),
    ]

    result = update_break_period(1, end_date="2026-03-20")

    assert result.status == BreakPeriodOperationStatus.OK
    assert result.break_period.end_date == "2026-03-20"
    mock_repo.update_break_period.assert_called_once_with(1, end_date="2026-03-20")


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_update_break_period_not_found(mock_repo):
    mock_repo.get_break_period_by_id.return_value = None

    result = update_break_period(9999, end_date="2026-03-20")

    assert result.status == BreakPeriodOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_update_break_period_invalid_date_range(mock_repo):
    mock_repo.get_break_period_by_id.return_value = _make_break_period(start_date="2026-03-20")

    result = update_break_period(1, end_date="2026-03-10")

    assert result.status == BreakPeriodOperationStatus.INVALID_DATE_RANGE


@pytest.mark.unit
@patch("modules.breaks.service.repository")
@patch("modules.breaks.service.get_active_user_by_id")
def test_update_break_period_invalid_user_ids(mock_get_user, mock_repo):
    mock_repo.get_break_period_by_id.return_value = _make_break_period()
    mock_get_user.return_value = None

    result = update_break_period(1, user_ids=[9999])

    assert result.status == BreakPeriodOperationStatus.INVALID_USER_IDS
    mock_repo.set_break_period_user_ids.assert_not_called()


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_update_break_period_invalid_start_date_type(mock_repo):
    mock_repo.get_break_period_by_id.return_value = _make_break_period()

    result = update_break_period(1, start_date=20260310)

    assert result.status == BreakPeriodOperationStatus.INVALID_START_DATE
    mock_repo.update_break_period.assert_not_called()


@pytest.mark.unit
@patch("modules.breaks.service.repository")
@patch("modules.breaks.service.get_active_user_by_id")
def test_update_break_period_with_user_ids(mock_get_user, mock_repo):
    mock_get_user.return_value = User(1, "Test", "admin")
    mock_repo.get_break_period_by_id.side_effect = [
        _make_break_period(user_ids=[1]),
        _make_break_period(user_ids=[1, 2]),
    ]

    result = update_break_period(1, label="Nuevo", user_ids=[1, 2])

    assert result.status == BreakPeriodOperationStatus.OK
    mock_repo.update_break_period.assert_called_once_with(1, label="Nuevo")
    mock_repo.set_break_period_user_ids.assert_called_once_with(1, [1, 2])


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_update_break_period_blank_label_normalized(mock_repo):
    mock_repo.get_break_period_by_id.side_effect = [
        _make_break_period(),
        _make_break_period(label=None),
    ]

    result = update_break_period(1, label="   ")

    assert result.status == BreakPeriodOperationStatus.OK
    mock_repo.update_break_period.assert_called_once_with(1, label=None)


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_delete_break_period_ok(mock_repo):
    mock_repo.get_break_period_by_id.return_value = _make_break_period()

    result = delete_break_period(1)

    assert result.status == BreakPeriodOperationStatus.OK
    assert result.break_period.id == 1
    mock_repo.delete_break_period.assert_called_once_with(1)


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_delete_break_period_not_found(mock_repo):
    mock_repo.get_break_period_by_id.return_value = None

    result = delete_break_period(9999)

    assert result.status == BreakPeriodOperationStatus.NOT_FOUND
    mock_repo.delete_break_period.assert_not_called()


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_active_break_period_for_user_delegates(mock_repo):
    expected = _make_break_period()
    mock_repo.get_active_break_period_for_user.return_value = expected

    result = get_active_break_period_for_user(1, date(2026, 3, 15))

    assert result is expected
    mock_repo.get_active_break_period_for_user.assert_called_once_with(1, "2026-03-15")


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_is_user_on_break_period(mock_repo):
    mock_repo.get_active_break_period_for_user.return_value = None
    assert is_user_on_break_period(1, date(2026, 3, 15)) is False

    mock_repo.get_active_break_period_for_user.return_value = _make_break_period()
    assert is_user_on_break_period(1, date(2026, 3, 15)) is True


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_active_break_period_user_ids_delegates(mock_repo):
    mock_repo.get_active_break_period_user_ids.return_value = {1, 2}

    result = get_active_break_period_user_ids(date(2026, 3, 15))

    assert result == {1, 2}
    mock_repo.get_active_break_period_user_ids.assert_called_once_with("2026-03-15")


@pytest.mark.unit
def test_serialize_break_period_info():
    period = _make_break_period(start_date="2026-03-10", end_date="2026-03-12")

    result = serialize_break_period_info(period)

    assert result == {
        "label": "Vacaciones",
        "start_date": "2026-03-10",
        "end_date": "2026-03-12",
        "days": 3,
    }


@pytest.mark.unit
def test_serialize_break_period_info_open_ended():
    result = serialize_break_period_info(_make_break_period(start_date="2026-03-10", end_date=None))

    assert result["days"] is None


@pytest.mark.unit
def test_serialize_break_period_info_none():
    assert serialize_break_period_info(None) is None


@pytest.mark.unit
def test_serialize_break_period_infos_filters_none():
    period = _make_break_period(start_date="2026-03-10", end_date=None)

    result = serialize_break_period_infos([None, period, None])

    assert len(result) == 1
    assert result[0]["label"] == "Vacaciones"


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_summary_by_user_inside_period(mock_repo):
    mock_repo.get_break_periods.return_value = [
        _make_break_period(start_date="2026-03-10", end_date="2026-03-12", user_ids=[1, 2])
    ]

    result = get_break_period_summary_by_user("2026-03")

    assert result == {
        1: [
            {
                "label": "Vacaciones",
                "start_date": "2026-03-10",
                "end_date": "2026-03-12",
                "days": 3,
            }
        ],
        2: [
            {
                "label": "Vacaciones",
                "start_date": "2026-03-10",
                "end_date": "2026-03-12",
                "days": 3,
            }
        ],
    }


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_summary_by_user_open_ended_end_of_month(mock_repo):
    mock_repo.get_break_periods.return_value = [
        _make_break_period(start_date="2026-03-10", end_date=None)
    ]

    result = get_break_period_summary_by_user("2026-03")

    assert result[1] == [
        {"label": "Vacaciones", "start_date": "2026-03-10", "end_date": None, "days": None}
    ]


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_summary_by_user_cross_month_period_included(mock_repo):
    mock_repo.get_break_periods.return_value = [
        _make_break_period(start_date="2026-02-20", end_date="2026-03-10", user_ids=[1])
    ]

    result = get_break_period_summary_by_user("2026-03")

    assert result[1] == [
        {
            "label": "Vacaciones",
            "start_date": "2026-02-20",
            "end_date": "2026-03-10",
            "days": 19,
        }
    ]


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_summary_by_user_no_overlap(mock_repo):
    mock_repo.get_break_periods.return_value = [
        _make_break_period(start_date="2026-02-01", end_date="2026-02-27")
    ]

    result = get_break_period_summary_by_user("2026-03")

    assert result == {}


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_summary_by_user_overlapping_periods(mock_repo):
    mock_repo.get_break_periods.return_value = [
        _make_break_period(
            period_id=1,
            start_date="2026-03-05",
            end_date="2026-03-15",
            user_ids=[1],
        ),
        _make_break_period(
            period_id=2,
            start_date="2026-03-10",
            end_date="2026-03-20",
            user_ids=[1],
        ),
    ]

    result = get_break_period_summary_by_user("2026-03")

    assert [p["label"] for p in result[1]] == ["Vacaciones", "Vacaciones"]
    assert [p["days"] for p in result[1]] == [11, 11]
    assert len(result[1]) == 2


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_summary_by_user_periods_sorted(mock_repo):
    mock_repo.get_break_periods.return_value = [
        _make_break_period(
            period_id=1,
            label="Segundo",
            start_date="2026-03-15",
            end_date="2026-03-20",
            user_ids=[1],
        ),
        _make_break_period(
            period_id=2,
            label="Primero",
            start_date="2026-03-01",
            end_date="2026-03-05",
            user_ids=[1, 2],
        ),
    ]

    result = get_break_period_summary_by_user("2026-03")

    assert [p["label"] for p in result[1]] == ["Primero", "Segundo"]
    assert [p["days"] for p in result[1]] == [5, 6]
    assert len(result[2]) == 1


@pytest.mark.unit
@patch("modules.breaks.service.repository")
def test_get_break_summary_by_user_invalid_month(mock_repo):
    result = get_break_period_summary_by_user("not-a-month")

    assert result == {}
    mock_repo.get_break_periods.assert_not_called()
