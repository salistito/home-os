export type FinancePeriodStatus = "open" | "closed";

export interface FinancePeriod {
  id: number;
  label: string;
  status: FinancePeriodStatus;
  opened_at: string;
}

export type FinanceEntryKind = "income" | "expense";
export type FinanceEntryScope = "shared" | "personal";
export type FinanceEntryStatus = "pending" | "confirmed";
export type FinanceDetailMode = "none" | "top_down" | "bottom_up";

export interface FinanceEntryDetail {
  id: number;
  entry_id: number;
  label: string;
  amount: number;
}

export interface FinanceTag {
  id: number;
  name: string;
  color: string;
}

export interface FinanceEntry {
  id: number;
  period_id: number;
  kind: FinanceEntryKind;
  scope: FinanceEntryScope;
  owner_id: string;
  label: string;
  amount: number | null;
  status: FinanceEntryStatus;
  paid_at: string | null;
  detail_mode: FinanceDetailMode;
  created_at: string;
  details: FinanceEntryDetail[];
  tags: FinanceTag[];
}

export interface FinancePersonSummary {
  owner_id: string;
  income: number;
  expense: number;
  balance: number;
}

export interface FinancePeriodSummary {
  shared_total: number;
  contributions: Record<string, number>;
  people: FinancePersonSummary[];
}

export interface FinancePeriodDetail extends FinancePeriod {
  entries: FinanceEntry[];
  summary: FinancePeriodSummary;
}

export interface CreateFinanceEntryInput {
  period_id: number;
  kind: FinanceEntryKind;
  scope: FinanceEntryScope;
  owner_id: string;
  label: string;
  amount: number | null;
  tags?: string[];
}

export interface FinanceEntryDetailInput {
  label: string;
  amount: number;
}

export interface UpdateFinanceEntryInput {
  label?: string;
  owner_id?: string;
  amount?: number;
  detail_mode?: FinanceDetailMode;
  details?: FinanceEntryDetailInput[];
  tags?: string[];
}
