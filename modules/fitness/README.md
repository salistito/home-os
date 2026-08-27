# Fitness Module

Body-weight and exercise tracking, scoped per user. Exercises are managed through a shared catalog (`fitness_exercises`, soft-delete) referenced by every session entry (`fitness_workout_entries`).

## Service API

### Exercise catalog

```python
def create_exercise(name: str, kind: str | None = None) -> FitnessOperationResult
```

Names (max 80 chars) are unique among active exercises (`DUPLICATE_NAME`). `kind` is an optional free-text label (max 40 chars, e.g. `"fuerza"`, `"cardio"`); blanks normalize to `None`.

```python
def list_exercises(include_deleted: bool = False) -> list[Exercise]
```

```python
def get_exercise_name_map() -> dict[int, str]
```

Includes deleted exercises so historical entries can always resolve a name.

```python
def update_exercise(exercise_id: int, **fields) -> FitnessOperationResult
```

Partial update of `name`, `kind`. Bumps `updated_at`.

```python
def delete_exercise(exercise_id: int) -> FitnessOperationResult
```

Soft-deletes the catalog exercise; historical entries keep referencing it.

### Workout entries

```python
def log_workout(user_id: int, exercise_id: int, duration_min: int | None = None, calories_burned: float | None = None, sets_breakdown: list | None = None, metrics: dict | None = None, notes: str | None = None, performed_at: str | None = None) -> FitnessOperationResult
```

`exercise_id` must reference an active catalog exercise (`INVALID_EXERCISE_ID`). At least one of `duration_min` (1-1440) or a non-empty `sets_breakdown` is required (`INVALID_DURATION_MIN` otherwise), so both timed sessions and pure strength sessions are valid.

```python
def list_workout_entries(user_id: int, exercise_id: int | None = None, from_date: str | None = None, to_date: str | None = None, limit: int | None = None) -> list[WorkoutEntry]
```

```python
def update_workout_entry(entry_id: int, user_id: int, **fields) -> FitnessOperationResult
```

Partial update of editable fields: `exercise_id`, `routine_id`, `duration_min`, `calories_burned`, `sets_breakdown`, `metrics`, `notes`, `performed_at`. Passing `duration_min: null` or an empty `sets_breakdown` clears that field; the resulting entry must still keep duration or sets (`INVALID_DURATION_MIN`). The edit workflow lets you switch freely between manual and routine mode: setting `routine_id` clears `exercise_id`, and vice versa.

```python
def delete_workout_entry(entry_id: int, user_id: int) -> FitnessOperationResult
```

### Sets breakdown

`sets_breakdown` is a first-class field (stored as JSON on the entry row, not inside `metrics`). It holds strength-training rows `{exercise_id?, exercise_name, weight_kg?, reps, sets?}` — max 50 rows. `exercise_id` is optional for manual entries but required for routine entries (every row must reference an existing catalog exercise when the entry belongs to a routine); `exercise_name` is required (max 60 chars) and is free text for manual entries. `weight_kg` is optional (> 0 and <= 500 kg when present, so bodyweight work needs no load), integer reps 1-1000, integer sets 1-100 (defaults to 1).

Volume and reps are never stored on the row. They are derived at serialization time:

- `volume_kg = sum(weight_kg * reps * sets over rows with weight)` — `null` when no row has a load.
- `total_reps = sum(reps * sets over all rows)`.

The same derivation powers the stats totals below.

### Metrics

`metrics` is an optional flat object (max 15 keys, key names up to 40 chars) whose values must be numbers (rounded to 2 decimals) or short strings (max 50 chars); booleans are rejected. Use it for free-form measurements such as `distance_km`, `rpe` or `surface`.

### Weight

```python
def log_weight(user_id: int, weight_kg: float, notes: str | None = None, measured_at: str | None = None) -> FitnessOperationResult
```

Upserts the weigh-in for `measured_at` (defaults to today; one entry per user per day). `weight_kg` must be > 0 and <= 500 kg (`INVALID_WEIGHT`).

```python
def list_weight_entries(user_id: int, from_date: str | None = None, to_date: str | None = None) -> list[WeightEntry]
```

```python
def update_weight_entry(entry_id: int, user_id: int, **fields) -> FitnessOperationResult
```

Edits an existing weigh-in (`weight_kg`, `notes`, `measured_at`). Changing the date to one that already has another entry for the same user returns `DUPLICATE_DATE` (HTTP 409).

```python
def delete_weight_entry(entry_id: int, user_id: int) -> FitnessOperationResult
```

### Stats

```python
def get_fitness_stats(user_id: int) -> FitnessStats
```

Weekly/monthly sessions and minutes, training volume (`volume_kg_last_7d/30d`, `null` without loaded sets) and total reps (`reps_last_7d/30d`), per-exercise usage over the last 30 days (`by_exercise_last_30d`, a map of `{exercise_name: {count, minutes}}` where direct entries count their `exercise_id` and routine drills only count rows that carry an `exercise_id`), plus the latest weight and its deltas vs 7/30 days ago.

### Errors

| Error | Raised when |
|---|---|
| `ExerciseAlreadyExistsError` | An insert or rename collides with an active exercise name (the service pre-checks and returns `DUPLICATE_NAME` first) |
| `WeightEntryDateConflictError` | A concurrent write trips the per-user unique `(user_id, measured_at)` constraint |

Web API mapping: validation statuses return HTTP `400`, `NOT_FOUND` returns `404`, and `DUPLICATE_NAME` / `DUPLICATE_DATE` return `409`.
