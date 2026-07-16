import { api } from "./client";
import type {
  CreateFinanceEntryInput,
  FinanceEntry,
  FinancePeriod,
  FinancePeriodDetail,
  FinanceTag,
  UpdateFinanceEntryInput,
} from "../types";

export const financesApi = {
  listPeriods: () => api.get<FinancePeriod[]>("/finances/periods"),
  openPeriod: (label?: string) =>
    api.post<FinancePeriod>("/finances/periods", label ? { label } : {}),
  getPeriod: (id: number) =>
    api.get<FinancePeriodDetail>(`/finances/periods/${id}`),
  listTags: () => api.get<FinanceTag[]>("/finances/tags"),
  createEntry: (input: CreateFinanceEntryInput) =>
    api.post<FinanceEntry>("/finances/entries", input),
  updateEntry: (id: number, input: UpdateFinanceEntryInput) =>
    api.patch<FinanceEntry>(`/finances/entries/${id}`, input),
  deleteEntry: (id: number) => api.delete<void>(`/finances/entries/${id}`),
  confirmEntry: (id: number) =>
    api.post<FinanceEntry>(`/finances/entries/${id}/confirm`, {}),
};
