from calendar import monthrange
from datetime import date

from core.utils.date import is_isoformat_date, to_db_date
from modules.breaks import repository
from modules.breaks.types import (
    BreakModule,
    BreakPeriod,
    BreakPeriodOperationResult,
    BreakPeriodOperationStatus,
)
from modules.users.repository import get_active_user_by_id

_UNSET = object()


def _normalize_label(label: object) -> str | None:
    if label is None:
        return None
    if not isinstance(label, str):
        return None
    stripped = label.strip()
    return stripped or None


def _validate_dates(start_date, end_date) -> BreakPeriodOperationStatus:
    if not isinstance(start_date, str) or not is_isoformat_date(start_date):
        return BreakPeriodOperationStatus.INVALID_START_DATE
    if end_date is not None:
        if not isinstance(end_date, str) or not is_isoformat_date(end_date):
            return BreakPeriodOperationStatus.INVALID_END_DATE
        if end_date < start_date:
            return BreakPeriodOperationStatus.INVALID_DATE_RANGE
    return BreakPeriodOperationStatus.OK


def _validate_user_ids(user_ids) -> BreakPeriodOperationStatus:
    if not user_ids or not isinstance(user_ids, list):
        return BreakPeriodOperationStatus.INVALID_USER_IDS
    if any(not isinstance(user_id, int) or isinstance(user_id, bool) for user_id in user_ids):
        return BreakPeriodOperationStatus.INVALID_USER_IDS
    if any(get_active_user_by_id(user_id) is None for user_id in user_ids):
        return BreakPeriodOperationStatus.INVALID_USER_IDS
    return BreakPeriodOperationStatus.OK


def _validate_modules(modules) -> BreakPeriodOperationStatus:
    if not modules or not isinstance(modules, list):
        return BreakPeriodOperationStatus.INVALID_MODULES
    if any(not isinstance(module, str) or module not in BreakModule.values() for module in modules):
        return BreakPeriodOperationStatus.INVALID_MODULES
    return BreakPeriodOperationStatus.OK


def _month_bounds(month_str: str) -> tuple[date, date] | None:
    if not isinstance(month_str, str):
        return None
    parts = month_str.split("-")
    if len(parts) != 2:
        return None
    try:
        year = int(parts[0])
        month = int(parts[1])
        first = date(year, month, 1)
        last = date(year, month, monthrange(year, month)[1])
        return first, last
    except ValueError:
        return None


def _overlap_start_end(
    start_date: str, end_date: str | None, month_bounds: tuple[date, date]
) -> tuple[date, date] | None:
    first, last = month_bounds
    start = max(date.fromisoformat(start_date), first)
    end = min(date.fromisoformat(end_date), last) if end_date else last
    if start > end:
        return None
    return start, end


def _break_period_days(start_date: str, end_date: str | None) -> int | None:
    if end_date is None:
        return None
    return (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1


def create_break_period(
    label: str | None,
    start_date: str,
    end_date: str | None,
    user_ids: list[int],
    modules: list[str],
) -> BreakPeriodOperationResult:
    normalized_label = _normalize_label(label)

    dates_status = _validate_dates(start_date, end_date)
    if dates_status is not BreakPeriodOperationStatus.OK:
        return BreakPeriodOperationResult(status=dates_status)

    users_status = _validate_user_ids(user_ids)
    if users_status is not BreakPeriodOperationStatus.OK:
        return BreakPeriodOperationResult(status=users_status)

    modules_status = _validate_modules(modules)
    if modules_status is not BreakPeriodOperationStatus.OK:
        return BreakPeriodOperationResult(status=modules_status)

    break_period = repository.create_break_period(
        label=normalized_label,
        start_date=start_date,
        end_date=end_date,
        created_at=to_db_date(date.today()),
        user_ids=user_ids,
        modules=modules,
    )
    return BreakPeriodOperationResult(
        break_period=break_period, status=BreakPeriodOperationStatus.OK
    )


def get_break_periods() -> list[BreakPeriod]:
    return repository.get_break_periods()


def get_break_period_by_id(break_period_id: int) -> BreakPeriodOperationResult:
    break_period = repository.get_break_period_by_id(break_period_id)
    if break_period is None:
        return BreakPeriodOperationResult(status=BreakPeriodOperationStatus.NOT_FOUND)
    return BreakPeriodOperationResult(
        break_period=break_period, status=BreakPeriodOperationStatus.OK
    )


def serialize_break_period_info(break_period: BreakPeriod | None) -> dict | None:
    if break_period is None:
        return None
    return {
        "label": break_period.label,
        "start_date": break_period.start_date,
        "end_date": break_period.end_date,
        "days": _break_period_days(break_period.start_date, break_period.end_date),
        "modules": break_period.modules or [],
    }


def serialize_break_period_infos(break_periods: list[BreakPeriod | None]) -> list[dict]:
    return [
        info
        for break_period in break_periods
        if (info := serialize_break_period_info(break_period)) is not None
    ]


def get_break_period_summary_by_user(month: str, module: str) -> dict[int, list]:
    month_bounds = _month_bounds(month)
    if month_bounds is None:
        return {}

    result: dict[int, list] = {}
    for break_period in repository.get_break_periods():
        if module not in (break_period.modules or []):
            continue
        overlap = _overlap_start_end(break_period.start_date, break_period.end_date, month_bounds)
        if overlap is None:
            continue
        for user_id in break_period.user_ids:
            result.setdefault(user_id, []).append(serialize_break_period_info(break_period))

    for periods in result.values():
        periods.sort(key=lambda period: period["start_date"])
    return result


def get_active_break_period_user_ids(day: date, module: str) -> set[int]:
    return repository.get_active_break_period_user_ids(to_db_date(day), module)


def get_active_break_periods_for_user(
    user_id: int, day: date, module: str | None = None
) -> list[BreakPeriod]:
    return repository.get_active_break_periods_for_user(user_id, to_db_date(day), module)


def get_active_break_period_for_user(
    user_id: int, day: date, module: str | None = None
) -> BreakPeriod | None:
    return repository.get_active_break_period_for_user(user_id, to_db_date(day), module)


def is_user_on_break_period(user_id: int, day: date) -> bool:
    return get_active_break_period_for_user(user_id, day) is not None


def update_break_period(
    break_period_id: int,
    label=_UNSET,
    start_date=_UNSET,
    end_date=_UNSET,
    user_ids=_UNSET,
    modules=_UNSET,
) -> BreakPeriodOperationResult:
    break_period = repository.get_break_period_by_id(break_period_id)
    if break_period is None:
        return BreakPeriodOperationResult(status=BreakPeriodOperationStatus.NOT_FOUND)

    effective_label = break_period.label
    if label is not _UNSET:
        effective_label = _normalize_label(label)

    effective_start_date = break_period.start_date
    if start_date is not _UNSET:
        if not isinstance(start_date, str):
            return BreakPeriodOperationResult(status=BreakPeriodOperationStatus.INVALID_START_DATE)
        effective_start_date = start_date

    effective_end_date = break_period.end_date
    if end_date is not _UNSET:
        effective_end_date = end_date

    dates_status = _validate_dates(effective_start_date, effective_end_date)
    if dates_status is not BreakPeriodOperationStatus.OK:
        return BreakPeriodOperationResult(status=dates_status)

    effective_user_ids: list[int] | None = None
    if user_ids is not _UNSET:
        users_status = _validate_user_ids(user_ids)
        if users_status is not BreakPeriodOperationStatus.OK:
            return BreakPeriodOperationResult(status=users_status)
        effective_user_ids = user_ids

    effective_modules: list[str] | None = None
    if modules is not _UNSET:
        modules_status = _validate_modules(modules)
        if modules_status is not BreakPeriodOperationStatus.OK:
            return BreakPeriodOperationResult(status=modules_status)
        effective_modules = modules

    fields: dict[str, str | None] = {}
    if label is not _UNSET:
        fields["label"] = effective_label
    if start_date is not _UNSET:
        fields["start_date"] = effective_start_date
    if end_date is not _UNSET:
        fields["end_date"] = effective_end_date
    if fields:
        repository.update_break_period(break_period_id, **fields)
    if effective_user_ids is not None:
        repository.set_break_period_user_ids(break_period_id, effective_user_ids)
    if effective_modules is not None:
        repository.set_break_period_modules(break_period_id, effective_modules)

    break_period = repository.get_break_period_by_id(break_period_id)
    return BreakPeriodOperationResult(
        break_period=break_period, status=BreakPeriodOperationStatus.OK
    )


def delete_break_period(break_period_id: int) -> BreakPeriodOperationResult:
    break_period = repository.get_break_period_by_id(break_period_id)
    if break_period is None:
        return BreakPeriodOperationResult(status=BreakPeriodOperationStatus.NOT_FOUND)
    repository.delete_break_period(break_period_id)
    return BreakPeriodOperationResult(
        break_period=break_period, status=BreakPeriodOperationStatus.OK
    )
