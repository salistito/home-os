import { api } from "./client";
import type { UserRef } from "../types";

export const usersApi = {
  list: () => api.get<UserRef[]>("/users"),
};
