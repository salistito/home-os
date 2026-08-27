from dataclasses import dataclass, field
from enum import StrEnum


class FitnessOperationStatus(StrEnum):
    OK = "ok"
    INVALID_ID = "invalid_id"
    INVALID_NAME = "invalid_name"
    DUPLICATE_NAME = "duplicate_name"
    INVALID_KIND = "invalid_kind"
    INVALID_ROUTINE_ID = "invalid_routine_id"
    INVALID_ROUTINE_CATEGORY = "invalid_routine_category"
    INVALID_ROUTINE_DESCRIPTION = "invalid_routine_description"
    INVALID_ROUTINE_EXERCISES = "invalid_routine_exercises"
    INVALID_ROUTINE_EXERCISE_POSITION = "invalid_routine_exercise_position"
    INVALID_EXERCISE_ID = "invalid_exercise_id"
    INVALID_DURATION_MIN = "invalid_duration_min"
    INVALID_CALORIES_BURNED = "invalid_calories_burned"
    INVALID_SETS_BREAKDOWN = "invalid_sets_breakdown"
    INVALID_METRICS = "invalid_metrics"
    INVALID_PERFORMED_AT = "invalid_performed_at"
    INVALID_WEIGHT = "invalid_weight"
    INVALID_MEASURED_AT = "invalid_measured_at"
    DUPLICATE_DATE = "duplicate_date"
    NOT_FOUND = "not_found"


@dataclass
class Exercise:
    id: int
    name: str
    kind: str | None
    created_at: str
    updated_at: str
    deleted_at: str | None


@dataclass
class Routine:
    id: int
    name: str
    category: str | None
    description: str | None
    created_at: str
    updated_at: str
    deleted_at: str | None


@dataclass
class RoutineExercise:
    id: int
    routine_id: int
    exercise_id: int
    weight_kg: float | None
    reps: int
    sets: int
    position: int


@dataclass
class WorkoutEntry:
    id: int
    user_id: int
    exercise_id: int | None
    routine_id: int | None
    duration_min: int | None
    calories_burned: float | None
    sets_breakdown: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    notes: str | None = None
    performed_at: str = ""
    created_at: str = ""


@dataclass
class WeightEntry:
    id: int
    user_id: int
    weight_kg: float
    notes: str | None
    measured_at: str
    created_at: str


@dataclass
class FitnessStats:
    sessions_last_7d: int = 0
    minutes_last_7d: int = 0
    volume_kg_last_7d: float | None = None
    reps_last_7d: int = 0
    sessions_last_30d: int = 0
    minutes_last_30d: int = 0
    volume_kg_last_30d: float | None = None
    reps_last_30d: int = 0
    by_exercise_last_30d: dict[str, dict] = field(default_factory=dict)
    latest_weight_kg: float | None = None
    latest_measured_at: str | None = None
    weight_delta_7d: float | None = None
    weight_delta_30d: float | None = None


@dataclass
class FitnessOperationResult:
    exercise: Exercise | None = None
    routine: Routine | None = None
    routine_exercises: list[RoutineExercise] = field(default_factory=list)
    workout_entry: WorkoutEntry | None = None
    workout_entries: list[WorkoutEntry] = field(default_factory=list)
    weight_entry: WeightEntry | None = None
    status: FitnessOperationStatus = FitnessOperationStatus.OK
