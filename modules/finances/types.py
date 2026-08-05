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
    MIXED = "mixed"


class EntryStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"


class DetailMode(StrEnum):
    NONE = "none"
    TOP_DOWN = "top_down"
    BOTTOM_UP = "bottom_up"


class FinanceOperationStatus(StrEnum):
    OK = "ok"
    INVALID_KIND = "invalid_kind"
    INVALID_SCOPE = "invalid_scope"
    INCOME_MUST_BE_PERSONAL = "income_must_be_personal"
    INVALID_LABEL = "invalid_label"
    DUPLICATE_LABEL = "duplicate_label"
    INVALID_AMOUNT = "invalid_amount"
    AMOUNT_REQUIRED = "amount_required"
    DETAILS_REQUIRED = "details_required"
    DETAILS_MISMATCH = "details_mismatch"
    INVALID_DETAIL_MODE = "invalid_detail_mode"
    INVALID_DETAIL_SCOPE = "invalid_detail_scope"
    INCOME_WITH_SHARED_DETAIL = "income_with_shared_detail"
    SHARED_ENTRY_WITH_PERSONAL_DETAIL = "shared_entry_with_personal_detail"
    PERSONAL_ENTRY_WITH_SHARED_DETAIL = "personal_entry_with_shared_detail"
    MIXED_REQUIRES_DETAILS = "mixed_requires_details"
    MIXED_DETAIL_SCOPE_REQUIRED = "mixed_detail_scope_required"
    MIXED_REQUIRES_BOTH_SCOPES = "mixed_requires_both_scopes"
    INVALID_TAG = "invalid_tag"
    NO_OPEN_PERIOD = "no_open_period"
    NOT_PENDING = "not_pending"
    NOT_FOUND = "not_found"


@dataclass
class Tag:
    id: int
    name: str
    color: str
    created_at: str


@dataclass
class EntryDetail:
    id: int
    entry_id: int
    scope: str | None
    label: str
    amount: int
    tags: list[Tag] = field(default_factory=list)


@dataclass
class Entry:
    id: int
    period_id: int
    kind: str
    scope: str
    owner_id: int
    label: str
    amount: int | None
    status: str
    paid_at: str | None
    detail_mode: str
    created_at: str
    details: list[EntryDetail] = field(default_factory=list)
    tags: list[Tag] = field(default_factory=list)

    @property
    def shared_amount(self) -> int | None:
        if self.details:
            return sum(
                d.amount for d in self.details if (d.scope or self.scope) == EntryScope.SHARED
            )
        return self.amount if self.scope == EntryScope.SHARED else 0


@dataclass
class Period:
    id: int
    label: str
    status: str
    opened_at: str


@dataclass
class PersonSummary:
    owner_id: int
    income: int
    expense: int
    balance: int


@dataclass
class PeriodSummary:
    shared_total: int
    contributions: dict[int, int]
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
