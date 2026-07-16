import { api } from "./client";
import { auth } from "../lib/auth";
import type { CreateReminderInput, Reminder, UpdateReminderInput } from "../types";

export const remindersApi = {
  create: (input: CreateReminderInput) =>
    api.post<Reminder>("/reminders", { ...input, user_id: auth.userId.value }),
  list: () => api.get<Reminder[]>(`/reminders?user_id=${auth.userId.value}`),
  update: (id: number, input: UpdateReminderInput) =>
    api.patch<Reminder>(`/reminders/${id}`, { ...input, user_id: auth.userId.value }),
  remove: (id: number) =>
    api.delete(`/reminders/${id}`, { user_id: auth.userId.value }),
};
