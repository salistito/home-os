export type FinancePeriodStatus = "open" | "closed";
export type FinanceEntryKind = "income" | "expense";
export type FinanceEntryScope = "shared" | "personal" | "mixed";
export type FinanceEntryStatus = "pending" | "confirmed";
export type FinanceDetailMode = "none" | "top_down" | "bottom_up";

export interface FinancePeriod {
  id: number;
  label: string;
  status: FinancePeriodStatus;
  opened_at: string;
}

export interface FinanceTag {
  id: number;
  name: string;
  color: string;
}

export interface FinanceEntryDetail {
  id: number;
  entry_id: number;
  scope: FinanceEntryScope | null;
  label: string;
  amount: number;
  tags: FinanceTag[];
}

export interface FinanceEntry {
  id: number;
  period_id: number;
  kind: FinanceEntryKind;
  scope: FinanceEntryScope;
  owner_id: number;
  label: string;
  amount: number | null;
  shared_amount: number | null;
  status: FinanceEntryStatus;
  paid_at: string | null;
  detail_mode: FinanceDetailMode;
  created_at: string;
  details: FinanceEntryDetail[];
  tags: FinanceTag[];
}

export interface FinanceSharedItem {
  key: string;
  entry: FinanceEntry;
  label: string;
  amount: number;
  tags: FinanceTag[];
}

export interface FinancePersonSummary {
  owner_id: number;
  income: number;
  expense: number;
  balance: number;
}

export interface FinancePeriodSummary {
  shared_total: number;
  contributions: Record<number, number>;
  people: FinancePersonSummary[];
}

export interface FinancePeriodDetail extends FinancePeriod {
  entries: FinanceEntry[];
  summary: FinancePeriodSummary;
}

export interface FinanceEntryDetailInput {
  scope?: FinanceEntryScope | null;
  label: string;
  amount: number;
  tags?: string[];
}

export interface CreateFinanceEntryInput {
  period_id: number;
  kind: FinanceEntryKind;
  scope: FinanceEntryScope;
  owner_id: number;
  label: string;
  amount: number | null;
  detail_mode?: FinanceDetailMode;
  details?: FinanceEntryDetailInput[];
  tags?: string[];
}

export interface UpdateFinanceEntryInput {
  kind?: FinanceEntryKind;
  scope?: FinanceEntryScope; 
  owner_id?: number;
  label?: string;
  amount?: number;
  detail_mode?: FinanceDetailMode;
  details?: FinanceEntryDetailInput[];
  tags?: string[];
}

export interface FinanceEntryDeletePayload {
  id: number;
  itemLabel?: string;
}
