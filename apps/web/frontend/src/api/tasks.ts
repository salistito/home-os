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
  getTodayBoard: () => api.get<TodayBoardResponse>("/tasks/today-board"),
  toggleAssignment: (assignmentId: number) =>
    api.post<{ done: boolean }>(`/tasks/today-board/${assignmentId}/toggle`, {}),
  getDailyBreakdown: (month?: string) => {
    const params = month ? `?month=${month}` : "";
    return api.get<DailyBreakdownResponse>(`/tasks/daily-breakdown${params}`);
  },
  getMonthlyRanking: (month?: string) => {
    const params = month ? `?month=${month}` : "";
    return api.get<MonthlyRankingResponse>(`/tasks/monthly-ranking${params}`);
  },
};
