import { api } from "./client";
import type { CreateUserPayload, UpdateUserPayload, UserRef } from "../types";

export const usersApi = {
  list: () => api.get<UserRef[]>("/users"),
  create: (payload: CreateUserPayload) => api.post<UserRef>("/users", payload),
  update: (id: number, payload: UpdateUserPayload) => api.patch<UserRef>(`/users/${id}`, payload),
  delete: (id: number) => api.delete<UserRef>(`/users/${id}`),
};
