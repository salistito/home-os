import { computed, ref } from "vue";
import { api } from "../api/client";
import type { UserRole } from "../types";

const AUTH_KEY = "homeos_auth";

interface StoredAuth {
  token: string;
  userId: number;
  userName: string;
  userRole: UserRole;
}

function loadAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveAuth(auth: StoredAuth): void {
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
}

function clearAuth(): void {
  localStorage.removeItem(AUTH_KEY);
}

const stored = loadAuth();
const token = ref<string | null>(stored?.token ?? null);
const userId = ref<number | null>(stored?.userId ?? null);
const userName = ref<string | null>(stored?.userName ?? null);
const userRole = ref<UserRole | null>(stored?.userRole ?? null);

export interface LoginResponse {
  token: string;
  id: number;
  name: string;
  role: UserRole;
}

export const auth = {
  isAuthenticated: computed(() => token.value !== null),
  userId: computed(() => userId.value),
  userName: computed(() => userName.value),
  userRole: computed(() => userRole.value),
  isAdmin: computed(() => userRole.value === "admin"),
  getToken: () => token.value,

  applySession(session: LoginResponse): void {
    token.value = session.token;
    userId.value = session.id;
    userName.value = session.name;
    userRole.value = session.role;
    saveAuth({
      token: session.token,
      userId: session.id,
      userName: session.name,
      userRole: session.role,
    });
  },

  async login(name: string, password: string): Promise<void> {
    const res = await api.post<LoginResponse>("/login", { name, password });
    this.applySession(res);
  },

  logout(): void {
    token.value = null;
    userId.value = null;
    userName.value = null;
    userRole.value = null;
    clearAuth();
  },
};
