import { auth } from "../lib/auth";
import type { ApiError } from "../types";


const API_URL = import.meta.env.VITE_API_URL?.replace(/\/$/, "");
const API_BASE = API_URL ? `${API_URL}/api` : "/api";

export class ApiRequestError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = "ApiRequestError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  const token = auth.getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401) {
      auth.logout();
    }
    const err = (data ?? {}) as Partial<ApiError>;
    throw new ApiRequestError(
      err.error ?? "unknown",
      err.message ?? "Ocurrió un error inesperado.",
    );
  }

  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "DELETE",
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    }),
};
