export type FinancePeriodStatus = "open" | "closed";

export interface FinancePeriod {
  id: number;
  label: string;
  status: FinancePeriodStatus;
  opened_at: string;
}
