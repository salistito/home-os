from core.utils.date import MONTHS, get_today, to_db_date
from modules.finances import repository
from modules.finances.types import (
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
