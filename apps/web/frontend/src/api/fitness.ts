import type {
  CreateExercisePayload,
  CreateWeightPayload,
  ExerciseEntry,
  FitnessStats,
  UpdateExercisePayload,
  WeightEntry,
} from "../types";
import { api } from "./client";

export const fitnessApi = {
  logWeight: (p: CreateWeightPayload) =>
    api.post<WeightEntry>("/fitness/weight", p),
  listWeights: (params?: { from_date?: string; to_date?: string }) => {
    const q = new URLSearchParams();
    if (params?.from_date) q.set("from_date", params.from_date);
    if (params?.to_date) q.set("to_date", params.to_date);
    const qs = q.toString();
    return api.get<WeightEntry[]>(`/fitness/weight${qs ? `?${qs}` : ""}`);
  },
  deleteWeight: (id: number) =>
    api.delete<WeightEntry>(`/fitness/weight/${id}`),

  createExercise: (p: CreateExercisePayload) =>
    api.post<ExerciseEntry>("/fitness/exercises", p),
  listExercises: (params?: {
    type?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.type) q.set("type", params.type);
    if (params?.from_date) q.set("from_date", params.from_date);
    if (params?.to_date) q.set("to_date", params.to_date);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return api.get<ExerciseEntry[]>(`/fitness/exercises${qs ? `?${qs}` : ""}`);
  },
  updateExercise: (id: number, p: UpdateExercisePayload) =>
    api.patch<ExerciseEntry>(`/fitness/exercises/${id}`, p),
  deleteExercise: (id: number) =>
    api.delete<ExerciseEntry>(`/fitness/exercises/${id}`),

  getStats: () => api.get<FitnessStats>("/fitness/stats"),
};
