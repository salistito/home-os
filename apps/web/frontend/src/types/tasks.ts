import type { UserRef } from "./common";

export interface Task {
  id: number;
  name: string;
  points: number;
  frequency_days: number | null;
  next_due_date: string | null;
}

export interface CreateTaskInput {
  name: string;
  points: number;
  frequency_days?: number | null;
  next_due_date?: string | null;
}

export type UpdateTaskInput = Partial<{
  name: string;
  points: number;
  frequency_days: number | null;
  next_due_date: string | null;
}>;

export interface ScoreEntry {
  user_id: string;
  name: string;
  points: number;
}

export interface ScoresResponse {
  month: string;
  ranking: ScoreEntry[];
}

export interface DailyTaskEntry {
  name: string;
  points: number;
}

export interface DailyScoresResponse {
  users: UserRef[];
  month: string;
  daily: Record<string, Record<string, number>>;
  tasks: Record<string, Record<string, DailyTaskEntry[]>>;
}

export interface TodayTask {
  task_id: number;
  name: string;
  points: number;
  done: boolean;
}

export interface TodayUser {
  id: string;
  name: string;
  tasks: TodayTask[];
}

export interface TodayBoard {
  date: string;
  users: TodayUser[];
}
