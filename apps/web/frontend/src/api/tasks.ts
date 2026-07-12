import { api } from "./client";
import type {
  CreateTaskInput,
  DailyScoresResponse,
  ScoresResponse,
  Task,
  TodayBoard,
  UpdateTaskInput,
} from "../types";

export const tasksApi = {
  list: () => api.get<Task[]>("/tasks"),
  create: (input: CreateTaskInput) => api.post<Task>("/tasks", input),
  update: (id: number, input: UpdateTaskInput) =>
    api.patch<Task>(`/tasks/${id}`, input),
  remove: (id: number) => api.delete<Task>(`/tasks/${id}`),
  scores: () => api.get<ScoresResponse>("/tasks/scores"),
  dailyScores: () => api.get<DailyScoresResponse>("/tasks/scores/daily"),
  today: () => api.get<TodayBoard>("/tasks/today"),
};
