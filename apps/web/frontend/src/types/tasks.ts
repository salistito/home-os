import type { UserRef } from "./common";

export interface Task {
  id: number;
  name: string;
  points: number;
  frequency_days: number | null;
  next_due_date: string | null;
}

export interface CreateTaskPayload {
  name: string;
  points: number;
  frequency_days?: number | null;
  next_due_date?: string | null;
}

export type UpdateTaskInputPayload = Partial<{
  name: string;
  points: number;
  frequency_days: number | null;
  next_due_date: string | null;
}>;

export interface MonthlyRankingEntry {
  user_id: string;
  name: string;
  points: number;
}

export interface MonthlyRankingResponse {
  month: string;
  ranking: MonthlyRankingEntry[];
}

interface DailyBreakdownTaskEntry {
  name: string;
  points: number;
}

export interface DailyBreakdownResponse {
  users: UserRef[];
  month: string;
  daily: Record<string, Record<string, number>>;
  tasks: Record<string, Record<string, DailyBreakdownTaskEntry[]>>;
}

interface TodayBoardTask {
  task_id: number;
  name: string;
  points: number;
  done: boolean;
}

export interface TodayBoardUser {
  id: string;
  name: string;
  tasks: TodayBoardTask[];
}

export interface TodayBoardResponse {
  date: string;
  users: TodayBoardUser[];
}
