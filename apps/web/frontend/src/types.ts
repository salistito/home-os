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

export interface UserRef {
  id: string;
  name: string;
}

export interface DailyScoresResponse {
  month: string;
  users: UserRef[];
  daily: Record<string, Record<string, number>>;
}

export interface ApiError {
  error: string;
  message: string;
}
