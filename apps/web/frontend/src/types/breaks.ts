export interface BreakUser {
  id: number;
  name: string;
}

export interface BreakPeriod {
  id: number;
  label: string | null;
  start_date: string;
  end_date: string | null;
  created_at: string;
  user_ids: number[];
  modules: string[];
  users?: BreakUser[];
}

export interface BreakPeriodInfo {
  label: string | null;
  start_date: string;
  end_date: string | null;
  days: number | null;
  modules: string[];
}

export interface CreateBreakPeriodPayload {
  label?: string;
  start_date: string;
  end_date?: string | null;
  user_ids: number[];
  modules: string[];
}

export interface UpdateBreakPeriodPayload {
  label?: string | null;
  start_date?: string;
  end_date?: string | null;
  user_ids?: number[];
  modules?: string[];
}