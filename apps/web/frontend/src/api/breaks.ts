import { api } from "./client";
import type { BreakPeriod, CreateBreakPeriodPayload, UpdateBreakPeriodPayload } from "../types";

export const breakPeriodsApi = {
  create: (payload: CreateBreakPeriodPayload) =>
    api.post<BreakPeriod>("/break-periods", payload),
  list: () => api.get<BreakPeriod[]>("/break-periods"),
  update: (id: number, payload: UpdateBreakPeriodPayload) =>
    api.patch<BreakPeriod>(`/break-periods/${id}`, payload),
  delete: (id: number) => api.delete<BreakPeriod>(`/break-periods/${id}`),
};