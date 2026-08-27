export interface Exercise {
  id: number;
  name: string;
  kind: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface RoutineExercise {
  id: number;
  routine_id: number;
  exercise_id: number;
  exercise_name: string;
  weight_kg: number | null;
  reps: number;
  sets: number;
  position: number;
}

export interface Routine {
  id: number;
  name: string;
  category: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  exercises: RoutineExercise[];
}

export interface SetBreakdownRow {
  exercise_id: number | null;
  exercise_name: string;
  weight_kg: number | null;
  reps: number;
  sets: number;
}

export type ExerciseMetrics = Record<string, number | string>;

export interface WorkoutEntry {
  id: number;
  user_id: number;
  exercise_id: number;
  exercise_name: string | null;
  routine_id: number | null;
  routine_name: string | null;
  duration_min: number | null;
  calories_burned: number | null;
  sets_breakdown: SetBreakdownRow[];
  volume_kg: number | null;
  total_reps: number | null;
  metrics: ExerciseMetrics;
  notes: string | null;
  performed_at: string;
  created_at: string;
}

export interface WeightEntry {
  id: number;
  user_id: number;
  weight_kg: number;
  notes: string | null;
  measured_at: string;
  created_at: string;
}

export interface FitnessStats {
  sessions_last_7d: number;
  minutes_last_7d: number;
  volume_kg_last_7d: number | null;
  reps_last_7d: number;
  sessions_last_30d: number;
  minutes_last_30d: number;
  volume_kg_last_30d: number | null;
  reps_last_30d: number;
  by_exercise_last_30d: Record<string, { count: number; minutes: number }>;
  latest_weight_kg: number | null;
  latest_measured_at: string | null;
  weight_delta_7d: number | null;
  weight_delta_30d: number | null;
}

export type CreateExercisePayload = {
  name: string;
  kind?: string;
};

export type UpdateExercisePayload = Partial<{
  name: string;
  kind: string | null;
}>;

export type CreateRoutinePayload = {
  name: string;
  category?: string;
  description?: string;
  exercises?: {
    exercise_id: number;
    weight_kg?: number;
    reps: number;
    sets?: number;
    position?: number;
  }[];
};

export type UpdateRoutinePayload = Partial<{
  name: string;
  category: string | null;
  description: string | null;
}>;

export type ReplaceRoutineExercisesPayload = {
  exercises: {
    exercise_id: number;
    weight_kg?: number;
    reps: number;
    sets?: number;
    position?: number;
  }[];
};

export type CreateWorkoutEntryPayload = {
  exercise_id?: number;
  routine_id?: number;
  duration_min?: number;
  calories_burned?: number;
  sets_breakdown?: SetBreakdownRow[];
  metrics?: ExerciseMetrics;
  notes?: string;
  performed_at?: string;
};

export type UpdateWorkoutEntryPayload = Partial<{
  exercise_id: number;
  routine_id: number;
  duration_min: number | null;
  calories_burned: number | null;
  sets_breakdown: SetBreakdownRow[] | null;
  metrics: ExerciseMetrics;
  notes: string | null;
  performed_at: string;
}>;

export type CreateWeightEntryPayload = {
  weight_kg: number;
  notes?: string;
  measured_at?: string;
};

export type UpdateWeightEntryPayload = Partial<{
  weight_kg: number;
  notes: string | null;
  measured_at: string;
}>;
