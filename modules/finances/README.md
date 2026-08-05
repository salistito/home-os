# finances

Domain module for household finance management: monthly periods, income/expense entries, and tags.

## Public API

```python
def open_period(label: str | None = None) -> PeriodOperationResult

def get_periods() -> list[Period]

def get_period_detail(period_id: int) -> PeriodDetailResult

def add_entry(period_id: int, kind: str, scope: str, owner_id: int, label: str, amount: int | None, tags: list[str] | None = None) -> EntryOperationResult

def update_entry(entry_id: int, *, label: str | None = None, owner_id: int | None = None, amount: int | None = None, detail_mode: str | None = None, details: list[tuple[str, int]] | None = None, tags: list[str] | None = None) -> EntryOperationResult

def delete_entry(entry_id: int) -> EntryOperationResult

def confirm_entry(entry_id: int) -> EntryOperationResult

def list_entries(period_id: int) -> list[Entry]

def list_tags() -> list[Tag]
```

## Key types

| Type | Description |
|---|---|
| `Period` | A monthly budget period with `label`, `status`, and `opened_at` |
| `Entry` | An income or expense with `kind`, `scope`, `owner_id`, `amount` (nullable while pending), `status`, `detail_mode`, `details`, and `tags` |
| `EntryDetail` | A line item breaking down an entry (optional `scope` that overrides the entry's scope when set, `label` and `amount`) |
| `Tag` | A label with a `color` that can be attached to entries |
| `PersonSummary` | Per-user `income`, `expense`, and `balance` within a period (keyed by integer `owner_id`) |
| `PeriodSummary` | Aggregate of a period: `shared_total`, `contributions` per user, and `people` |
| `PeriodDetail` | A period bundled with its entries and summary |
| `PeriodStatus` | Enum: `OPEN`, `CLOSED` |
| `EntryKind` | Enum: `INCOME`, `EXPENSE` |
| `EntryScope` | Enum: `SHARED`, `PERSONAL`, `MIXED` |
| `EntryStatus` | Enum: `PENDING`, `CONFIRMED` |
| `DetailMode` | Enum: `NONE`, `TOP_DOWN`, `BOTTOM_UP` |
| `FinanceOperationStatus` | Enum: `OK`, `INVALID_KIND`, `INVALID_SCOPE`, `INCOME_MUST_BE_PERSONAL`, `INVALID_LABEL`, `DUPLICATE_LABEL`, `INVALID_AMOUNT`, `AMOUNT_REQUIRED`, `DETAILS_REQUIRED`, `DETAILS_MISMATCH`, `INVALID_DETAIL_MODE`, `INVALID_DETAIL_SCOPE`, `INCOME_WITH_SHARED_DETAIL`, `SHARED_ENTRY_WITH_PERSONAL_DETAIL`, `PERSONAL_ENTRY_WITH_SHARED_DETAIL`, `MIXED_REQUIRES_DETAILS`, `MIXED_DETAIL_SCOPE_REQUIRED`, `MIXED_REQUIRES_BOTH_SCOPES`, `INVALID_TAG`, `NO_OPEN_PERIOD`, `NOT_PENDING`, `NOT_FOUND` |
| `EntryOperationResult` | Result of entry create/update/delete/confirm with `Entry | None` and `FinanceOperationStatus` |
| `PeriodOperationResult` | Result of period operations with `Period | None` and `FinanceOperationStatus` |
| `PeriodDetailResult` | Result of `get_period_detail` with `PeriodDetail | None` and `FinanceOperationStatus` |

## Errors

| Error | Description |
|---|---|
| `OpenPeriodExistsError` | Raised when opening a period while another is still open |

## Behavior notes

- Only one period can be `open` at a time (enforced by a partial unique index). Opening a new period closes the previous one and clones its confirmed entries into the new period.
- An entry can be created without an `amount`; it stays `pending` until confirmed. Confirming requires a non-null amount.
- Income entries must be `personal` (`INCOME_MUST_BE_PERSONAL`).
- Only `shared` expenses count toward the period's `shared_total` and per-user `contributions`. When an entry has details, each detail may carry its own `scope` (`shared`/`personal`); a `None` detail scope inherits the entry's scope. The shared portion of an entry is the sum of its details whose effective scope is `shared` (or the full amount when the entry has no details).
- Three scopes exist for expenses: `personal`, `shared`, and `mixed`. A `mixed` entry requires a breakdown (`detail_mode != none`) with at least one `personal` line and one `shared` line, and every line must have an explicit `scope`. A `personal` entry cannot contain `shared` details (`PERSONAL_ENTRY_WITH_SHARED_DETAIL`), a `shared` entry cannot contain `personal` details (`SHARED_ENTRY_WITH_PERSONAL_DETAIL`), and a shared detail inside an income is rejected (`INCOME_WITH_SHARED_DETAIL`). Income must always be `personal`.
- With `detail_mode = bottom_up`, an entry's `amount` is derived from the sum of its details.
- Tags are deduplicated case-insensitively and capped at 30 characters. They are purely organizational (colors, filters) and never affect the financial summary.

## Dependencies

- `core/` for DB connection and date utilities
- Does NOT import from `apps/`
