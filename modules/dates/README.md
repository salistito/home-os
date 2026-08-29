# dates

Domain module for couple date planning.

## Public API

```python
def is_valid_reveal_on(value: str | None) -> bool

def who_plans_next(couple_id: int) -> int | None

def create_couple(name: str, member_ids: list[int]) -> DateOperationResult

def get_couples() -> DateOperationResult

def update_couple(couple_id: int, name: str | None = None, member_ids: list[int] | None = None) -> DateOperationResult

def delete_couple(couple_id: int) -> DateOperationResult

def create_event(couple_id: int, week_start: str, viewer_user_id: int, planned_by: int | None = None, title: str | None = None, scheduled_date: str | None = None, scheduled_time: str | None = None, attributes: list[dict] | None = None) -> DateOperationResult

def list_events(viewer_user_id: int, couple_id: int | None = None, from_date: str | None = None, to_date: str | None = None) -> DateOperationResult

def get_event_detail(event_id: int, viewer_user_id: int) -> DateOperationResult

def update_event(event_id: int, viewer_user_id: int, planned_by: int | None = None, scheduled_date: str | None = None, scheduled_time: str | None = None, title: str | None = None, attributes: list[dict] | None = None) -> DateOperationResult

def complete_event(event_id: int, viewer_user_id: int) -> DateOperationResult

def delete_event(event_id: int, viewer_user_id: int) -> DateOperationResult

def add_memory(event_id: int, viewer_user_id: int, kind: str, media_url: str | None = None, caption: str | None = None, taken_by: int | None = None) -> DateOperationResult

def list_memories(event_id: int, viewer_user_id: int) -> DateOperationResult

def delete_memory(memory_id: int, viewer_user_id: int) -> DateOperationResult
```

## Key types

| Type | Description |
|---|---|
| `DateCouple` | A couple (pair/group of active users) with `member_ids`. |
| `DateEvent` | A weekly date event with `couple_id`, `week_start` (ISO `YYYY-MM-DD`, unique per couple), `planned_by`, optional `scheduled_date`/`scheduled_time`, `title`, `status` (`planned`/`scheduled`/`done`), and `attributes`. |
| `DateAttribute` | An attribute (`place`/`dresscode`/`vibes`/custom) with `value`, `is_secret`, and `reveal_on` (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM` or `NULL`). |
| `DateMemory` | A post-event memory: `photo` (media_url reference) or `note` (caption). |
| `DateOperationStatus` | Enum: `OK`, `NOT_FOUND`, `FORBIDDEN`, `INVALID_*`, `DUPLICATE_WEEK`, `EMPTY_MEMBERS`. |
| `DateOperationResult` | Wrapper with status + `couple`/`couples`/`event`/`events`/`memory`/`memories`. |

## Rules

- A couple must have at least one active user. `member_ids` are validated against active users.
- `week_start` is unique per couple (one date per week).
- Rotation: `who_plans_next()` returns the next active member after the one who planned the most recent event (round-robin).
- Secret attributes: visible to the planner always; to other members only when `now >= reveal_on`. `reveal_on = NULL` never reveals via chat (surprise in person).
- Access: only members of the event's couple can read/edit/delete events and memories; otherwise `FORBIDDEN`.

## Integrations

Uses `modules/reminders` system reminders (`system_ref_entity` `dates:plan` and
`dates:event`) to notify who plans and when the date/event happens. Sending runs
through the existing `/trigger_day_reminders` / `/trigger_timed_reminders`
flows; reminders are created/cleaned inline on create/plan/update/delete.

## Dependencies

- `core/` for DB connection and date utilities.
- `modules/reminders` for system reminders.
- `modules/users` to validate active users.
- Does NOT import from `apps/`.
