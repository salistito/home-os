export type UserRole = "admin" | "member"

export interface UserRef {
  id: number;
  name: string;
  role: UserRole;
  deleted_at: string | null;
}

export interface ApiError {
  error: string;
  message: string;
}
