import { api } from "./client";
import type {
  AddMemoryInput,
  CreateCoupleInput,
  CreateEventInput,
  CreateMilestoneInput,
  DateCouple,
  DateEvent,
  DateMemory,
  DateMilestone,
  UpdateCoupleInput,
  UpdateEventInput,
} from "../types";

export const datesApi = {
  listCouples: (includeArchived = false) =>
    api.get<DateCouple[]>(
      `/dates/couples${includeArchived ? "?include_archived=true" : ""}`,
    ),
  createCouple: (input: CreateCoupleInput) => api.post<DateCouple>("/dates/couples", input),
  updateCouple: (id: number, input: UpdateCoupleInput) =>
    api.patch<DateCouple>(`/dates/couples/${id}`, input),
  deleteCouple: (id: number) => api.delete(`/dates/couples/${id}`),

  listMilestones: (coupleId: number) =>
    api.get<DateMilestone[]>(`/dates/couples/${coupleId}/milestones`),
  createMilestone: (coupleId: number, input: CreateMilestoneInput) =>
    api.post<DateMilestone>(`/dates/couples/${coupleId}/milestones`, input),
  deleteMilestone: (id: number) => api.delete(`/dates/milestones/${id}`),

  listEvents: (params: { couple_id?: number; from_date?: string; to_date?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.couple_id !== undefined) query.set("couple_id", String(params.couple_id));
    if (params.from_date) query.set("from_date", params.from_date);
    if (params.to_date) query.set("to_date", params.to_date);
    const qs = query.toString();
    return api.get<DateEvent[]>(`/dates/events${qs ? `?${qs}` : ""}`);
  },
  createEvent: (input: CreateEventInput) => api.post<DateEvent>("/dates/events", input),
  getEvent: (id: number) => api.get<DateEvent>(`/dates/events/${id}`),
  updateEvent: (id: number, input: UpdateEventInput) =>
    api.patch<DateEvent>(`/dates/events/${id}`, input),
  completeEvent: (id: number) => api.post<DateEvent>(`/dates/events/${id}/complete`, {}),
  deleteEvent: (id: number) => api.delete(`/dates/events/${id}`),

  listMemories: (eventId: number) => api.get<DateMemory[]>(`/dates/events/${eventId}/memories`),
  addMemory: (eventId: number, input: AddMemoryInput) =>
    api.post<DateMemory>(`/dates/events/${eventId}/memories`, input),
  deleteMemory: (id: number) => api.delete(`/dates/memories/${id}`),
};