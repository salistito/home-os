export type ReminderRecurrencePreset = "none" | "daily" | "weekly" | "monthly" | "yearly";

export type ReminderRecurrence = ReminderRecurrencePreset | string;

export interface Reminder {
  id: number;
  user_id: number;
  message: string;
  trigger_at: string;
  trigger_time: string | null;
  recurrence: ReminderRecurrence;
  created_at: string;
}

export interface CreateReminderInput {
  message: string;
  trigger_at: string;
  trigger_time?: string | null;
  recurrence?: ReminderRecurrence;
}

export type UpdateReminderInput = Partial<{
  message: string;
  trigger_at: string;
  trigger_time: string | null;
  recurrence: ReminderRecurrence;
}>;
