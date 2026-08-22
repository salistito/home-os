export type ExerciseIntensity = "low" | "medium" | "high";

export interface SetBreakdownRow {
  name: string | null;
  weight_kg: number;
  reps: number;
  sets: number;
}

export type ExerciseMetricValue = number | string | SetBreakdownRow[];
export type ExerciseMetrics = Record<string, ExerciseMetricValue>;

export interface WeightEntry {
  id: number;
  user_id: number;
  weight_kg: number;
  measured_at: string;
  notes: string | null;
  created_at: string;
}

export interface ExerciseEntry {
  id: number;
  user_id: number;
  exercise_type: string;
  duration_min: number | null;
  intensity: ExerciseIntensity | null;
  calories_burned: number | null;
  performed_at: string;
  notes: string | null;
  created_at: string;
  metrics: ExerciseMetrics;
}

export interface FitnessStats {
  latest_weight_kg: number | null;
  latest_measured_at: string | null;
  weight_delta_7d: number | null;
  weight_delta_30d: number | null;
  minutes_last_7d: number;
  sessions_last_7d: number;
  minutes_last_30d: number;
  sessions_last_30d: number;
  by_type_last_30d: Record<string, number>;
}

export type CreateWeightPayload = {
  weight_kg: number;
  measured_at?: string;
  notes?: string;
};

export type CreateExercisePayload = {
  exercise_type: string;
  duration_min: number;
  intensity?: ExerciseIntensity | "";
  calories_burned?: number;
  performed_at?: string;
  notes?: string;
};

export type UpdateExercisePayload = Partial<{
  exercise_type: string;
  duration_min: number;
  intensity: ExerciseIntensity | null;
  calories_burned: number | null;
  performed_at: string;
  notes: string | null;
}>;
