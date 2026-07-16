import { api } from "./client";
import type {
  CreateFinanceEntryInput,
  FinanceEntry,
  FinancePeriod,
  FinancePeriodDetail,
} from "../types";

export const financesApi = {
  listPeriods: () => api.get<FinancePeriod[]>("/finances/periods"),
  openPeriod: (label?: string) =>
    api.post<FinancePeriod>("/finances/periods", label ? { label } : {}),
  getPeriod: (id: number) =>
    api.get<FinancePeriodDetail>(`/finances/periods/${id}`),
  createEntry: (input: CreateFinanceEntryInput) =>
    api.post<FinanceEntry>("/finances/entries", input),
  confirmEntry: (id: number) =>
    api.post<FinanceEntry>(`/finances/entries/${id}/confirm`, {}),
  rejectEntry: (id: number) =>
    api.post<FinanceEntry>(`/finances/entries/${id}/reject`, {}),
};
