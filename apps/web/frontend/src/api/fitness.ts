import type {
  Exercise,
  ExerciseEntry,
  WeightEntry,
  CreateExercisePayload,
  CreateExerciseEntryPayload,
  CreateWeightEntryPayload,
  UpdateExercisePayload,
  UpdateExerciseEntryPayload,
  UpdateWeightEntryPayload,
  FitnessStats,
} from "../types";
import { api } from "./client";

export const fitnessApi = {
  createExercise: (p: CreateExercisePayload) =>
    api.post<Exercise>("/fitness/exercises", p),
  listExercises: () =>
    api.get<Exercise[]>("/fitness/exercises"),
  updateExercise: (id: number, p: UpdateExercisePayload) =>
    api.patch<Exercise>(`/fitness/exercises/${id}`, p),
  deleteExercise: (id: number) =>
    api.delete<Exercise>(`/fitness/exercises/${id}`),

  logExerciseEntry: (p: CreateExerciseEntryPayload) =>
    api.post<ExerciseEntry>("/fitness/exercise-entries", p),
  listExerciseEntries: (params?: {
    exercise_id?: number;
    from_date?: string;
    to_date?: string;
    limit?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.exercise_id) q.set("exercise_id", String(params.exercise_id));
    if (params?.from_date) q.set("from_date", params.from_date);
    if (params?.to_date) q.set("to_date", params.to_date);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return api.get<ExerciseEntry[]>(`/fitness/exercise-entries${qs ? `?${qs}` : ""}`);
  },
  updateExerciseEntry: (id: number, p: UpdateExerciseEntryPayload) =>
    api.patch<ExerciseEntry>(`/fitness/exercise-entries/${id}`, p),
  deleteExerciseEntry: (id: number) =>
    api.delete<ExerciseEntry>(`/fitness/exercise-entries/${id}`),

  logWeightEntry: (p: CreateWeightEntryPayload) =>
    api.post<WeightEntry>("/fitness/weight", p),
  listWeightsEntries: (params?: { from_date?: string; to_date?: string }) => {
    const q = new URLSearchParams();
    if (params?.from_date) q.set("from_date", params.from_date);
    if (params?.to_date) q.set("to_date", params.to_date);
    const qs = q.toString();
    return api.get<WeightEntry[]>(`/fitness/weight${qs ? `?${qs}` : ""}`);
  },
  updateWeightEntry: (id: number, p: UpdateWeightEntryPayload) =>
    api.patch<WeightEntry>(`/fitness/weight/${id}`, p),
  deleteWeightEntry: (id: number) =>
    api.delete<WeightEntry>(`/fitness/weight/${id}`),

  getStats: () => api.get<FitnessStats>("/fitness/stats"),
};
