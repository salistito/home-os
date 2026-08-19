import type { CookingSourceDetails } from "./food";
import type { UserRef } from "./users";

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

export type AssignmentSource = "task" | "cooking";

export interface TodayBoardTask {
  assignment_id: number;
  task_id: number;
  name: string;
  points: number;
  source: AssignmentSource;
  source_entity_id?: number | null;
  source_entity_details?: CookingSourceDetails | null;
  done: boolean;
}

export interface TodayBoardUser {
  id: number;
  name: string;
  tasks: TodayBoardTask[];
}

export interface TodayBoardResponse {
  date: string;
  users: TodayBoardUser[];
}

export interface MonthlyRankingEntry {
  user_id: number;
  name: string;
  points: number;
}

export interface MonthlyRankingResponse {
  month: string;
  ranking: MonthlyRankingEntry[];
}

export interface DailyBreakdownTaskEntry {
  name: string;
  points: number;
  source: AssignmentSource;
  source_entity_details?: CookingSourceDetails | null;
}

export interface DailyBreakdownResponse {
  users: UserRef[];
  month: string;
  daily: Record<string, Record<number, number>>;
  tasks: Record<string, Record<number, DailyBreakdownTaskEntry[]>>;
}
