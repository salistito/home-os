import pytest

from datetime import date
from unittest.mock import patch

from modules.finances.service import (
    add_entry,
    confirm_entry,
    default_period_label,
    delete_entry,
    get_period_detail,
    get_periods,
    list_entries,
    list_tags,
    normalize_tags,
    open_period,
    parse_label,
    update_entry,
)
from modules.finances.types import (
    DetailMode,
    Entry,
    EntryKind,
    EntryScope,
    EntryStatus,
    FinanceOperationStatus,
    Period,
)


@pytest.fixture
def mock_period():
    return Period(1, "Marzo 2026", "open", "2026-03-15")


@pytest.fixture
def mock_entry():
    return Entry(
        1,
        1,
        EntryKind.INCOME,
        EntryScope.PERSONAL,
        1,
        "Salary",
        5000,
        EntryStatus.CONFIRMED,
        "2026-03-15",
        DetailMode.NONE,
        "2026-03-15",
    )


@pytest.mark.unit
@patch("modules.finances.service.get_today")
@patch("modules.finances.service.repository")
def test_open_period_generates_default_label(mock_repo, mock_today, mock_period):
    mock_today.return_value = date(2026, 2, 15)
    mock_repo.get_periods.return_value = []
    mock_repo.get_period_by_label.return_value = None
    mock_repo.get_open_period.return_value = None
    mock_repo.create_period.return_value = mock_period

    result = open_period()

    assert result.status == FinanceOperationStatus.OK


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_open_period_empty_label(mock_repo):
    result = open_period("   ")

    assert result.status == FinanceOperationStatus.INVALID_LABEL


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_open_period_duplicate_label(mock_repo, mock_period):
    mock_repo.get_period_by_label.return_value = mock_period
    result = open_period("Marzo 2026")

    assert result.status == FinanceOperationStatus.DUPLICATE_LABEL


@pytest.mark.unit
@patch("modules.finances.service.get_today")
@patch("modules.finances.service.repository")
def test_open_period_clones_confirmed_from_previous(mock_repo, mock_today, mock_period):
    mock_today.return_value = date(2026, 3, 15)
    previous = Period(0, "Febrero 2026", "open", "2026-02-15")
    mock_repo.get_periods.return_value = []
    mock_repo.get_period_by_label.return_value = None
    mock_repo.get_open_period.return_value = previous
    mock_repo.create_period.return_value = mock_period

    result = open_period()

    mock_repo.close_open_period.assert_called_once()
    mock_repo.clone_confirmed_entries.assert_called_once()
    assert result.status == FinanceOperationStatus.OK


@pytest.mark.unit
@patch("modules.finances.service.get_today")
@patch("modules.finances.service.repository")
def test_open_period_no_previous_no_clone(mock_repo, mock_today, mock_period):
    mock_today.return_value = date(2026, 3, 15)
    mock_repo.get_periods.return_value = []
    mock_repo.get_period_by_label.return_value = None
    mock_repo.get_open_period.return_value = None
    mock_repo.create_period.return_value = mock_period

    result = open_period()

    mock_repo.clone_confirmed_entries.assert_not_called()
    assert result.status == FinanceOperationStatus.OK


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_get_periods_delegates(mock_repo):
    mock_repo.get_periods.return_value = []
    result = get_periods()

    assert result == []


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_get_period_detail_not_found(mock_repo):
    mock_repo.get_period_by_id.return_value = None
    result = get_period_detail(1)

    assert result.status == FinanceOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_get_period_detail_valid(mock_repo, mock_period):
    mock_repo.get_period_by_id.return_value = mock_period
    mock_repo.get_entries_by_period.return_value = []
    result = get_period_detail(1)

    assert result.status == FinanceOperationStatus.OK
    assert result.detail is not None


@pytest.mark.unit
@patch("modules.finances.service.get_today")
@patch("modules.finances.service.repository")
def test_add_entry_empty_label(mock_repo, mock_today):
    result = add_entry(1, "income", "personal", 1, "", None)

    assert result.status == FinanceOperationStatus.INVALID_LABEL


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_add_entry_invalid_kind(mock_repo):
    result = add_entry(1, "invalid", "personal", 1, "X", None)

    assert result.status == FinanceOperationStatus.INVALID_KIND


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_add_entry_invalid_scope(mock_repo):
    result = add_entry(1, "income", "invalid", 1, "X", None)

    assert result.status == FinanceOperationStatus.INVALID_SCOPE


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_add_entry_negative_amount(mock_repo):
    result = add_entry(1, "income", "personal", 1, "X", -100)

    assert result.status == FinanceOperationStatus.INVALID_AMOUNT


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_add_entry_income_must_be_personal(mock_repo):
    result = add_entry(1, "income", "shared", 1, "X", 100)

    assert result.status == FinanceOperationStatus.INCOME_MUST_BE_PERSONAL


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_add_entry_invalid_tags(mock_repo):
    result = add_entry(1, "income", "personal", 1, "X", 100, tags=["a" * 31])

    assert result.status == FinanceOperationStatus.INVALID_TAG


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_add_entry_period_not_found(mock_repo):
    mock_repo.get_period_by_id.return_value = None
    result = add_entry(1, "income", "personal", 1, "X", 100)

    assert result.status == FinanceOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.finances.service.get_today")
@patch("modules.finances.service.repository")
def test_add_entry_valid(mock_repo, mock_today, mock_entry):
    mock_today.return_value = date(2026, 3, 15)
    mock_repo.get_period_by_id.return_value = Period(1, "P", "open", "")
    mock_repo.create_entry.return_value = mock_entry
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = add_entry(1, "income", "personal", 1, "Salary", 5000)

    assert result.status == FinanceOperationStatus.OK


@pytest.mark.unit
@patch("modules.finances.service.get_today")
@patch("modules.finances.service.repository")
def test_add_entry_with_tags(mock_repo, mock_today, mock_entry):
    mock_today.return_value = date(2026, 3, 15)
    mock_repo.get_period_by_id.return_value = Period(1, "P", "open", "")
    mock_repo.create_entry.return_value = mock_entry
    mock_repo.get_or_create_tag_ids.return_value = [1]
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = add_entry(1, "income", "personal", 1, "Salary", 5000, tags=["work"])

    assert result.status == FinanceOperationStatus.OK
    mock_repo.get_or_create_tag_ids.assert_called_once()
    mock_repo.set_entry_tags.assert_called_once()


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_not_found(mock_repo):
    mock_repo.get_entry_by_id.return_value = None
    result = update_entry(1)

    assert result.status == FinanceOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_empty_label(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = update_entry(1, label="")

    assert result.status == FinanceOperationStatus.INVALID_LABEL


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_invalid_detail_mode(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = update_entry(1, detail_mode="invalid")

    assert result.status == FinanceOperationStatus.INVALID_DETAIL_MODE


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_invalid_detail_label(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = update_entry(1, details=[("", 100)])

    assert result.status == FinanceOperationStatus.INVALID_LABEL


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_invalid_detail_amount(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = update_entry(1, details=[("X", -1)])

    assert result.status == FinanceOperationStatus.INVALID_AMOUNT


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_invalid_tags(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = update_entry(1, tags=["a" * 31])

    assert result.status == FinanceOperationStatus.INVALID_TAG


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_negative_amount(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = update_entry(1, amount=-5)

    assert result.status == FinanceOperationStatus.INVALID_AMOUNT


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_bottom_up_calculates_amount(mock_repo):
    entry = Entry(
        1,
        1,
        EntryKind.EXPENSE,
        EntryScope.SHARED,
        1,
        "Shop",
        None,
        EntryStatus.PENDING,
        None,
        DetailMode.BOTTOM_UP,
        "2026-03-15",
    )
    mock_repo.get_entry_by_id.return_value = entry
    mock_repo.get_entry_by_id.return_value = entry
    result = update_entry(1, details=[("A", 100), ("B", 200)])

    assert result.status == FinanceOperationStatus.OK
    args = mock_repo.update_entry.call_args
    assert args[0][3] == 300


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_valid(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.side_effect = [mock_entry, mock_entry]
    result = update_entry(1, label="Updated")

    assert result.status == FinanceOperationStatus.OK


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_delete_entry_not_found(mock_repo):
    mock_repo.get_entry_by_id.return_value = None
    result = delete_entry(1)

    assert result.status == FinanceOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_delete_entry_exists(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = delete_entry(1)

    assert result.status == FinanceOperationStatus.OK
    assert result.entry == mock_entry
    mock_repo.delete_entry.assert_called_once_with(1)


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_confirm_entry_not_found(mock_repo):
    mock_repo.get_entry_by_id.return_value = None
    result = confirm_entry(1)

    assert result.status == FinanceOperationStatus.NOT_FOUND


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_confirm_entry_not_pending(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.return_value = mock_entry
    result = confirm_entry(1)

    assert result.status == FinanceOperationStatus.NOT_PENDING


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_confirm_entry_no_amount(mock_repo):
    entry = Entry(
        1,
        1,
        EntryKind.EXPENSE,
        EntryScope.SHARED,
        1,
        "Rent",
        None,
        EntryStatus.PENDING,
        None,
        DetailMode.NONE,
        "2026-03-15",
    )
    mock_repo.get_entry_by_id.return_value = entry
    result = confirm_entry(1)

    assert result.status == FinanceOperationStatus.AMOUNT_REQUIRED


@pytest.mark.unit
@patch("modules.finances.service.get_today")
@patch("modules.finances.service.repository")
def test_confirm_entry_valid(mock_repo, mock_today):
    mock_today.return_value = date(2026, 3, 15)
    entry = Entry(
        1,
        1,
        EntryKind.EXPENSE,
        EntryScope.SHARED,
        1,
        "Rent",
        1000,
        EntryStatus.PENDING,
        None,
        DetailMode.NONE,
        "2026-03-15",
    )
    mock_repo.get_entry_by_id.return_value = entry
    mock_repo.set_entry_status.return_value = entry
    result = confirm_entry(1)

    assert result.status == FinanceOperationStatus.OK


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_list_entries_delegates(mock_repo):
    mock_repo.get_entries_by_period.return_value = []
    result = list_entries(1)

    assert result == []


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_list_tags_delegates(mock_repo):
    mock_repo.get_tags.return_value = []
    result = list_tags()

    assert result == []


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_get_period_detail_summary_with_income(mock_repo, mock_period):
    entry = Entry(
        1,
        1,
        EntryKind.INCOME,
        EntryScope.PERSONAL,
        1,
        "Salary",
        5000,
        EntryStatus.CONFIRMED,
        "2026-03-15",
        DetailMode.NONE,
        "2026-03-15",
    )
    mock_repo.get_period_by_id.return_value = mock_period
    mock_repo.get_entries_by_period.return_value = [entry]
    result = get_period_detail(1)

    assert result.status == FinanceOperationStatus.OK
    assert result.detail.summary.people[0].income == 5000
    assert result.detail.summary.people[0].balance == 5000


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_get_period_detail_summary_with_shared_expense(mock_repo, mock_period):
    entry = Entry(
        1,
        1,
        EntryKind.EXPENSE,
        EntryScope.SHARED,
        1,
        "Rent",
        3000,
        EntryStatus.CONFIRMED,
        "2026-03-15",
        DetailMode.NONE,
        "2026-03-15",
    )
    mock_repo.get_period_by_id.return_value = mock_period
    mock_repo.get_entries_by_period.return_value = [entry]
    result = get_period_detail(1)

    assert result.status == FinanceOperationStatus.OK
    assert result.detail.summary.shared_total == 3000
    assert result.detail.summary.contributions[1] == 3000
    assert result.detail.summary.people[0].balance == -3000


@pytest.mark.unit
def test_normalize_tags_skips_empty_and_duplicates():
    result = normalize_tags(["", "  ", "Tag", "tag"])

    assert result == ["Tag"]


@pytest.mark.unit
def test_normalize_tags_long_name_returns_none():
    result = normalize_tags(["a" * 31])

    assert result is None


@pytest.mark.unit
def test_parse_label_valid():
    result = parse_label("Enero 2026")

    assert result == (1, 2026)


@pytest.mark.unit
def test_parse_label_invalid_format():
    result = parse_label("January 2026")

    assert result is None


@pytest.mark.unit
def test_parse_label_no_year():
    result = parse_label("Enero")

    assert result is None


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_update_entry_with_tags(mock_repo, mock_entry):
    mock_repo.get_entry_by_id.return_value = mock_entry
    mock_repo.get_or_create_tag_ids.return_value = [1, 2]
    result = update_entry(1, tags=["tag1", "tag2"])

    assert result.status == FinanceOperationStatus.OK
    mock_repo.get_or_create_tag_ids.assert_called_once()
    mock_repo.set_entry_tags.assert_called_once()


@pytest.mark.unit
@patch("modules.finances.service.repository")
def test_default_period_label_uses_existing_period(mock_repo):
    from modules.finances.types import Period

    mock_repo.get_periods.return_value = [Period(1, "Enero 2026", "closed", "2026-01-01")]

    result = default_period_label()
    assert result == "Febrero 2026"
