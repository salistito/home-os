from core.utils.date import MONTHS, get_today, to_db_date
from modules.finances import repository
from modules.finances.types import (
    DetailMode,
    Entry,
    EntryKind,
    EntryOperationResult,
    EntryScope,
    EntryStatus,
    FinanceOperationStatus,
    Period,
    PeriodDetail,
    PeriodDetailResult,
    PeriodOperationResult,
    PeriodSummary,
    PersonSummary,
    Tag,
)

_MAX_TAG_LEN = 30


def _normalize_tags(raw: list[str]) -> list[str] | None:
    seen: set[str] = set()
    result: list[str] = []
    for name in raw:
        name = name.strip()
        if not name:
            continue
        if len(name) > _MAX_TAG_LEN:
            return None
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(name)
    return result


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

    previous = repository.get_open_period()
    repository.close_open_period()
    opened_at = to_db_date(get_today())
    period = repository.create_period(label, opened_at)
    if previous is not None:
        repository.clone_confirmed_entries(previous.id, period.id, opened_at)
    return PeriodOperationResult(period=period, status=FinanceOperationStatus.OK)


def get_periods() -> list[Period]:
    return repository.get_periods()


def _summarize(entries: list[Entry]) -> PeriodSummary:
    income: dict[str, int] = {}
    expense: dict[str, int] = {}
    contributions: dict[str, int] = {}
    shared_total = 0

    for e in entries:
        amount = e.amount or 0
        if e.kind == EntryKind.INCOME:
            income[e.owner_id] = income.get(e.owner_id, 0) + amount
        else:
            expense[e.owner_id] = expense.get(e.owner_id, 0) + amount
            if e.scope == EntryScope.SHARED:
                shared_total += amount
                contributions[e.owner_id] = contributions.get(e.owner_id, 0) + amount

    owner_ids = sorted(set(income) | set(expense))
    people = [
        PersonSummary(
            owner_id=owner_id,
            income=income.get(owner_id, 0),
            expense=expense.get(owner_id, 0),
            balance=income.get(owner_id, 0) - expense.get(owner_id, 0),
        )
        for owner_id in owner_ids
    ]
    return PeriodSummary(shared_total=shared_total, contributions=contributions, people=people)


def get_period_detail(period_id: int) -> PeriodDetailResult:
    period = repository.get_period_by_id(period_id)
    if period is None:
        return PeriodDetailResult(detail=None, status=FinanceOperationStatus.NOT_FOUND)

    entries = repository.get_entries_by_period(period_id)
    detail = PeriodDetail(period=period, entries=entries, summary=_summarize(entries))
    return PeriodDetailResult(detail=detail, status=FinanceOperationStatus.OK)


def add_entry(
    period_id: int,
    kind: str,
    scope: str,
    owner_id: str,
    label: str,
    amount: int | None,
    tags: list[str] | None = None,
) -> EntryOperationResult:
    label = label.strip()
    if not label:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_LABEL)
    if kind not in (EntryKind.INCOME, EntryKind.EXPENSE):
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_KIND)
    if scope not in (EntryScope.SHARED, EntryScope.PERSONAL):
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_SCOPE)
    if amount is not None and amount < 0:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_AMOUNT)
    if kind == EntryKind.INCOME and scope != EntryScope.PERSONAL:
        return EntryOperationResult(
            entry=None, status=FinanceOperationStatus.INCOME_MUST_BE_PERSONAL
        )

    clean_tags: list[str] | None = None
    if tags is not None:
        clean_tags = _normalize_tags(tags)
        if clean_tags is None:
            return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_TAG)

    if repository.get_period_by_id(period_id) is None:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.NOT_FOUND)

    created_at = to_db_date(get_today())
    entry = repository.create_entry(
        period_id, kind, scope, owner_id, label, amount, created_at
    )
    if clean_tags:
        tag_ids = repository.get_or_create_tag_ids(clean_tags, created_at)
        repository.set_entry_tags(entry.id, tag_ids)
        entry = repository.get_entry_by_id(entry.id)
    return EntryOperationResult(entry=entry, status=FinanceOperationStatus.OK)


def update_entry(
    entry_id: int,
    *,
    label: str | None = None,
    owner_id: str | None = None,
    amount: int | None = None,
    detail_mode: str | None = None,
    details: list[tuple[str, int]] | None = None,
    tags: list[str] | None = None,
) -> EntryOperationResult:
    entry = repository.get_entry_by_id(entry_id)
    if entry is None:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.NOT_FOUND)

    clean_tags: list[str] | None = None
    if tags is not None:
        clean_tags = _normalize_tags(tags)
        if clean_tags is None:
            return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_TAG)

    new_label = entry.label if label is None else label.strip()
    if not new_label:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_LABEL)

    new_owner_id = entry.owner_id if owner_id is None else owner_id

    new_mode = entry.detail_mode if detail_mode is None else detail_mode
    if new_mode not in (DetailMode.NONE, DetailMode.TOP_DOWN, DetailMode.BOTTOM_UP):
        return EntryOperationResult(
            entry=None, status=FinanceOperationStatus.INVALID_DETAIL_MODE
        )

    clean_details: list[tuple[str, int]] | None = None
    if details is not None:
        clean_details = []
        for d_label, d_amount in details:
            d_label = d_label.strip()
            if not d_label:
                return EntryOperationResult(
                    entry=None, status=FinanceOperationStatus.INVALID_LABEL
                )
            if d_amount < 0:
                return EntryOperationResult(
                    entry=None, status=FinanceOperationStatus.INVALID_AMOUNT
                )
            clean_details.append((d_label, d_amount))

    new_amount = entry.amount if amount is None else amount
    if new_mode == DetailMode.BOTTOM_UP:
        source = (
            clean_details
            if clean_details is not None
            else [(d.label, d.amount) for d in entry.details]
        )
        new_amount = sum(a for _, a in source)
    if new_amount is not None and new_amount < 0:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.INVALID_AMOUNT)

    repository.update_entry(entry_id, new_label, new_owner_id, new_amount, new_mode)
    if clean_details is not None:
        repository.replace_entry_details(entry_id, clean_details)
    if clean_tags is not None:
        tag_ids = repository.get_or_create_tag_ids(clean_tags, to_db_date(get_today()))
        repository.set_entry_tags(entry_id, tag_ids)

    return EntryOperationResult(
        entry=repository.get_entry_by_id(entry_id), status=FinanceOperationStatus.OK
    )


def delete_entry(entry_id: int) -> EntryOperationResult:
    entry = repository.get_entry_by_id(entry_id)
    if entry is None:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.NOT_FOUND)

    repository.delete_entry(entry_id)
    return EntryOperationResult(entry=entry, status=FinanceOperationStatus.OK)


def confirm_entry(entry_id: int) -> EntryOperationResult:
    entry = repository.get_entry_by_id(entry_id)
    if entry is None:
        return EntryOperationResult(entry=None, status=FinanceOperationStatus.NOT_FOUND)
    if entry.status != EntryStatus.PENDING:
        return EntryOperationResult(entry=entry, status=FinanceOperationStatus.NOT_PENDING)
    if entry.amount is None:
        return EntryOperationResult(
            entry=entry, status=FinanceOperationStatus.AMOUNT_REQUIRED
        )

    updated = repository.set_entry_status(
        entry_id, EntryStatus.CONFIRMED, to_db_date(get_today())
    )
    return EntryOperationResult(entry=updated, status=FinanceOperationStatus.OK)


def list_entries(period_id: int) -> list[Entry]:
    return repository.get_entries_by_period(period_id)


def list_tags() -> list[Tag]:
    return repository.get_tags()
