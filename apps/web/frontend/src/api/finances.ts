import { api } from "./client";
import type { FinancePeriod } from "../types";

export const financesApi = {
  listPeriods: () => api.get<FinancePeriod[]>("/finances/periods"),
  openPeriod: (label?: string) =>
    api.post<FinancePeriod>("/finances/periods", label ? { label } : {}),
  getPeriod: (id: number) => api.get<FinancePeriod>(`/finances/periods/${id}`),
};
