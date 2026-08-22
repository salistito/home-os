# Fitness Module

Body-weight and exercise tracking, scoped per user.

## Service API

### Weight

```python
def log_weight(user_id: int, weight_kg: float, measured_at: str | None = None, notes: str | None = None) -> FitnessOperationResult
```

Upserts the weigh-in for `measured_at` (defaults to today; one entry per user per day).

```python
def list_weight_entries(user_id: int, from_date: str | None = None, to_date: str | None = None) -> list[WeightEntry]
```

```python
def delete_weight_entry(entry_id: int, user_id: int) -> FitnessOperationResult
```

### Exercise

```python
def create_exercise(user_id: int, exercise_type: str, duration_min: int, intensity: str | None = None, calories_burned: float | None = None, performed_at: str | None = None, notes: str | None = None) -> FitnessOperationResult
```

```python
def list_exercises(user_id: int, exercise_type: str | None = None, from_date: str | None = None, to_date: str | None = None, limit: int | None = None) -> list[ExerciseEntry]
```

```python
def update_exercise(entry_id: int, user_id: int, **fields) -> FitnessOperationResult
```

Partial update of editable fields: `exercise_type`, `duration_min`, `intensity`, `calories_burned`, `performed_at`, `notes`.

```python
def delete_exercise(entry_id: int, user_id: int) -> FitnessOperationResult
```

### Stats

```python
def get_stats(user_id: int) -> FitnessStats
```

Latest weight, weight deltas vs 7/30 days ago, weekly/monthly minutes and sessions, minutes by exercise type (last 30 days).
