export type UserRole = "admin" | "member"

export interface UserRef {
  id: number;
  name: string;
  role: UserRole;
  telegram_chat_id: string | null;
  deleted_at: string | null;
}

export interface CreateUserPayload {
  name: string;
  role: UserRole;
  telegram_chat_id?: string;
}

export interface UpdateUserPayload {
  name?: string;
  role?: UserRole;
  telegram_chat_id?: string;
  restore?: boolean;
}
