from core.utils.date import MONTHS, get_today, to_db_date
from modules.finances import repository
from modules.finances.types import (
    Entry,
    EntryKind,
    EntryOperationResult,
    EntryScope,
    EntryStatus,
    FinanceOperationStatus,
    Period,
    PeriodOperationResult,
)


def _label_for(month: int, year: int) -> str:
    return f"{MONTHS[month - 1].capitalize()} {year}"


def _next_month(month: int, year: int) -> tuple[int, int]:
    return (1, year + 1) if month == 12 else (month + 1, year)


def _parse_label(label: str) -> tuple[int, int] | None:
    parts = label.split()
    if len(parts) != 2:
        return None
    name, year = parts[0].lower(), parts[1]
    if name not in MONTHS or not year.isdigit():
        return None
    return MONTHS.index(name) + 1, int(year)


def _default_period_label() -> str:
    periods = repository.get_periods()
    if periods and (parsed := _parse_label(periods[0].label)) is not None:
        return _label_for(*_next_month(*parsed))

    today = get_today()
    return _label_for(*_next_month(today.month, today.year))


def open_period(label: str | None = None) -> PeriodOperationResult:
    label = (label or _default_period_label()).strip()
    if not label:
        return PeriodOperationResult(period=None, status=FinanceOperationStatus.INVALID_LABEL)

    if repository.get_period_by_label(label) is not None:
        return PeriodOperationResult(
            period=None, status=FinanceOperationStatus.DUPLICATE_LABEL
        )

    repository.close_open_period()
    period = repository.create_period(label, to_db_date(get_today()))
    return PeriodOperationResult(period=period, status=FinanceOperationStatus.OK)


def get_periods() -> list[Period]:
    return repository.get_periods()


def get_period(period_id: int) -> PeriodOperationResult:
    period = repository.get_period_by_id(period_id)
    if period is None:
        return PeriodOperationResult(period=None, status=FinanceOperationStatus.NOT_FOUND)
    return PeriodOperationResult(period=period, status=FinanceOperationStatus.OK)


def add_entry(
    period_id: int,
    kind: str,
    scope: str,
    owner_id: str,
    label: str,
    amount: int,
) -> EntryOperationResult:
    label = label.strip()
    if not label:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_LABEL)
    if kind not in (EntryKind.INCOME, EntryKind.EXPENSE):
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_KIND)
    if scope not in (EntryScope.SHARED, EntryScope.PERSONAL):
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_SCOPE)
    if amount < 0:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_AMOUNT)
    if kind == EntryKind.INCOME and scope != EntryScope.PERSONAL:
        return EntryOperationResult(
            entry=None, status=FinanceOperationStatus.INCOME_MUST_BE_PERSONAL
        )

    if repository.get_period_by_id(period_id) is None:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.NOT_FOUND)

    entry = repository.create_entry(
        period_id, kind, scope, owner_id, label, amount, to_db_date(get_today())
    )
    return EntryOperationResult(entry=entry, status=FinanceOperationStatus.OK)


def confirm_entry(entry_id: int) -> EntryOperationResult:
    entry = repository.get_entry_by_id(entry_id)
    if entry is None:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.NOT_FOUND)
    if entry.status != EntryStatus.PENDING:
        return EntryOperationResult(entry=entry, status=FinanceOperationStatus.NOT_PENDING)

    updated = repository.set_entry_status(
        entry_id, EntryStatus.CONFIRMED, to_db_date(get_today())
    )
    return EntryOperationResult(entry=updated, status=FinanceOperationStatus.OK)


def reject_entry(entry_id: int) -> EntryOperationResult:
    entry = repository.get_entry_by_id(entry_id)
    if entry is None:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.NOT_FOUND)
    if entry.status != EntryStatus.PENDING:
        return EntryOperationResult(entry=entry, status=FinanceOperationStatus.NOT_PENDING)

    repository.delete_entry(entry_id)
    return EntryOperationResult(entry=entry, status=FinanceOperationStatus.OK)


def list_entries(period_id: int) -> list[Entry]:
    return repository.get_entries_by_period(period_id)
