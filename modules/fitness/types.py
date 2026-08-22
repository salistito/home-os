from dataclasses import dataclass, field
from enum import StrEnum


class ExerciseIntensity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FitnessOperationStatus(StrEnum):
    OK = "ok"
    INVALID_ID = "invalid_id"
    INVALID_WEIGHT = "invalid_weight"
    INVALID_MEASURED_AT = "invalid_measured_at"
    INVALID_EXERCISE_TYPE = "invalid_exercise_type"
    INVALID_DURATION = "invalid_duration"
    INVALID_INTENSITY = "invalid_intensity"
    INVALID_CALORIES = "invalid_calories"
    INVALID_PERFORMED_AT = "invalid_performed_at"
    INVALID_METRICS = "invalid_metrics"
    NOT_FOUND = "not_found"


@dataclass
class WeightEntry:
    id: int
    user_id: int
    weight_kg: float
    measured_at: str
    notes: str | None
    created_at: str


@dataclass
class ExerciseEntry:
    id: int
    user_id: int
    exercise_type: str
    duration_min: int
    intensity: ExerciseIntensity | None
    calories_burned: float | None
    performed_at: str
    notes: str | None
    created_at: str
    metrics: dict = field(default_factory=dict)


@dataclass
class FitnessStats:
    latest_weight_kg: float | None = None
    latest_measured_at: str | None = None
    weight_delta_7d: float | None = None
    weight_delta_30d: float | None = None
    minutes_last_7d: int = 0
    sessions_last_7d: int = 0
    minutes_last_30d: int = 0
    sessions_last_30d: int = 0
    by_type_last_30d: dict[str, int] = field(default_factory=dict)


@dataclass
class FitnessOperationResult:
    weight_entry: WeightEntry | None = None
    exercise_entry: ExerciseEntry | None = None
    status: FitnessOperationStatus = FitnessOperationStatus.OK
