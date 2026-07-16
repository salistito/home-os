from dataclasses import dataclass, field
from enum import StrEnum


class PeriodStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class EntryKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class EntryScope(StrEnum):
    SHARED = "shared"
    PERSONAL = "personal"


class EntryStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class DetailMode(StrEnum):
    NONE = "none"
    TOP_DOWN = "top_down"
    BOTTOM_UP = "bottom_up"


class FinanceOperationStatus(StrEnum):
    OK = "ok"
    INVALID_LABEL = "invalid_label"
    DUPLICATE_LABEL = "duplicate_label"
    INVALID_AMOUNT = "invalid_amount"
    INVALID_KIND = "invalid_kind"
    INVALID_SCOPE = "invalid_scope"
    INVALID_DETAIL_MODE = "invalid_detail_mode"
    INCOME_MUST_BE_PERSONAL = "income_must_be_personal"
    NO_OPEN_PERIOD = "no_open_period"
    NOT_PENDING = "not_pending"
    NOT_FOUND = "not_found"


@dataclass
class EntryDetail:
    id: int
    entry_id: int
    label: str
    amount: int


@dataclass
class Entry:
    id: int
    period_id: int
    kind: str
    scope: str
    owner_id: str
    label: str
    amount: int
    status: str
    paid_at: str | None
    detail_mode: str
    created_at: str
    details: list[EntryDetail] = field(default_factory=list)


@dataclass
class Period:
    id: int
    label: str
    status: str
    opened_at: str


@dataclass
class PersonSummary:
    owner_id: str
    income: int
    expense: int
    balance: int


@dataclass
class PeriodSummary:
    shared_total: int
    contributions: dict[str, int]
    people: list[PersonSummary]


@dataclass
class PeriodDetail:
    period: Period
    entries: list[Entry]
    summary: PeriodSummary


@dataclass
class EntryOperationResult:
    entry: Entry | None
    status: FinanceOperationStatus


@dataclass
class PeriodOperationResult:
    period: Period | None
    status: FinanceOperationStatus


@dataclass
class PeriodDetailResult:
    detail: PeriodDetail | None
    status: FinanceOperationStatus
