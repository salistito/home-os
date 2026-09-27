# breaks

Domain module for break periods: date ranges scoped to a set of users and a set of modules, during which those users are "on break".

## Public API

```python
def create_break_period(label: str | None, start_date: str, end_date: str | None, user_ids: list[int], modules: list[str]) -> BreakPeriodOperationResult

def get_break_periods() -> list[BreakPeriod]

def get_break_period_by_id(break_period_id: int) -> BreakPeriodOperationResult

def update_break_period(break_period_id: int, label=_UNSET, start_date=_UNSET, end_date=_UNSET, user_ids=_UNSET, modules=_UNSET) -> BreakPeriodOperationResult

def delete_break_period(break_period_id: int) -> BreakPeriodOperationResult

def get_break_period_summary_by_user(month: str, module: str) -> dict[int, list[dict]]

def get_break_periods_user_ids(day: date, module: str) -> set[int]

def get_break_periods_in_range(user_id: int, from_date: date, to_date: date, module: str | None = None) -> list[BreakPeriod]

def is_user_on_tasks_break_period(user_id: int, day: date) -> bool

def serialize_break_period_info(break_period: BreakPeriod | None) -> dict | None

def serialize_break_period_infos(break_periods: list[BreakPeriod | None]) -> list[dict]
```

## Key types

| Type | Description |
|---|---|
| `BreakPeriod` | A break range with `id`, nullable `label`, ISO `start_date`, nullable `end_date`, `created_at`, and the resolved `user_ids` / `modules` lists |
| `BreakModule` | StrEnum of the modules that can be part of a break: `TASKS`, `FINANCES`, `FOOD`, `FITNESS`, `REMINDERS` |
| `BreakPeriodOperationResult` | Result of break period operations with `BreakPeriod | None` and `BreakPeriodOperationStatus` |
| `BreakPeriodOperationStatus` | Enum: `OK`, `INVALID_START_DATE`, `INVALID_END_DATE`, `INVALID_DATE_RANGE`, `INVALID_USER_IDS`, `INVALID_MODULES`, `NOT_FOUND` |

## Behavior notes

- A break period is **half-open by day, inclusive on both ends**: a user is on break on `day` when `start_date <= day` and (`end_date` is `NULL` or `day <= end_date`). A `NULL` `end_date` means the period is open-ended.
- `label` is optional and free text; blank/whitespace-only values normalize to `None`. Dates must be ISO (`YYYY-MM-DD`) and `end_date >= start_date`, otherwise `INVALID_START_DATE` / `INVALID_END_DATE` / `INVALID_DATE_RANGE`.
- `user_ids` must be a non-empty list of **active** user ids (`INVALID_USER_IDS` otherwise); `modules` must be a non-empty list of `BreakModule` values (`INVALID_MODULES` otherwise). A period always needs at least one user and one module.
- `update_break_period` is a partial update driven by a `_UNSET` sentinel: only the fields actually passed are written, but the resulting range is always re-validated as a whole (e.g. sending only `end_date` that precedes the stored `start_date` returns `INVALID_DATE_RANGE`). `user_ids` and `modules` are replaced wholesale, not merged.
- `get_break_periods` and `get_break_period_by_id` return periods ordered by `start_date DESC, id DESC`; `get_break_periods_in_range` returns the same list reversed (oldest first) and only those overlapping `[from_date, to_date]`.
- `get_break_period_summary_by_user(month, module)` clips every period to the requested month bounds and groups the serialized infos by user, sorted by `start_date`. Used by the tasks monthly ranking.
- `get_break_periods_user_ids(day, module)` is the set of users on break for `module` on a given day. It is the query the tasks module uses to exclude users from the daily rotation.
- `is_user_on_tasks_break_period(user_id, day)` is the tasks-specific convenience wrapper (`module = tasks`).
- `serialize_break_period_info` / `serialize_break_period_infos` produce the read-only shape exposed by the API: `label`, `start_date`, `end_date`, `days` (inclusive count, `None` for open-ended periods) and `modules`. `None` entries are dropped.

## Module behavior

Only `tasks` is enforced today. `food` and `fitness` are accepted and surfaced in the web UI as informational banners; `finances` and `reminders` are accepted by the API but not rendered anywhere yet.

For `tasks` (enforced by `modules/tasks/service.py`):

- Users on break are excluded from the daily assignment rotation.
- Their `pending` assignments for that day are flipped to `failed` before the rotation runs.
- `mark_assignment_done` and `toggle_assignment` refuse to complete tasks for those users.
- The Telegram bot answers with a "período de receso" message instead of the assignment list.

## Errors

| Error | Description |
|---|---|
| — | This module raises no custom exceptions. Invalid input is reported through `BreakPeriodOperationStatus`. The repository raises `ValueError` when `update_break_period` is called with a non-editable column |

## Dependencies

- `core/` for DB connection and date utilities
- `modules/users/` to validate that the referenced users are active
- Does NOT import from `apps/`
