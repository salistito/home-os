import { api } from "./client";
import type {
  Task,
  CreateTaskPayload,
  UpdateTaskInputPayload,
  MonthlyRankingResponse,
  DailyBreakdownResponse,
  TodayBoardResponse,

} from "../types";

export const tasksApi = {
  create: (payload: CreateTaskPayload) => api.post<Task>("/tasks", payload),
  list: () => api.get<Task[]>("/tasks"),
  update: (id: number, payload: UpdateTaskInputPayload) => api.patch<Task>(`/tasks/${id}`, payload),
  delete: (id: number) => api.delete<Task>(`/tasks/${id}`),
  getMonthlyRanking: () => api.get<MonthlyRankingResponse>("/tasks/monthly-ranking"),
  getDailyBreakdown: () => api.get<DailyBreakdownResponse>("/tasks/daily-breakdown"),
  getTodayBoard: () => api.get<TodayBoardResponse>("/tasks/today-board"),
};
