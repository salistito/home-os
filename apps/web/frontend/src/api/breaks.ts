import type { ModuleId } from "../modules";
import type {
  BreakPeriod,
  BreakPeriodsInRange,
  CreateBreakPeriodPayload,
  UpdateBreakPeriodPayload,
} from "../types";
import { api } from "./client";

function parseBreakPeriodsInRangeQueryParams(params: {
  module?: ModuleId;
  from_date?: string;
  to_date?: string;
}): string {
  const searchParams = new URLSearchParams();
  if (params.module) searchParams.set("module", params.module);
  if (params.from_date) searchParams.set("from_date", params.from_date);
  if (params.to_date) searchParams.set("to_date", params.to_date);
  const queryParams = searchParams.toString();
  return queryParams ? `?${queryParams}` : "";
}

export const breakPeriodsApi = {
  create: (payload: CreateBreakPeriodPayload) =>
    api.post<BreakPeriod>("/break-periods", payload),
  list: () => api.get<BreakPeriod[]>("/break-periods"),
  inRange: (params: { module?: ModuleId; from_date?: string; to_date?: string }) =>
    api.get<BreakPeriodsInRange>("/break-periods/in-range" + parseBreakPeriodsInRangeQueryParams(params)),
  update: (id: number, payload: UpdateBreakPeriodPayload) =>
    api.patch<BreakPeriod>(`/break-periods/${id}`, payload),
  delete: (id: number) => api.delete<BreakPeriod>(`/break-periods/${id}`),
};
