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

interface LoginResponse {
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

  async login(name: string, password: string): Promise<void> {
    const res = await api.post<LoginResponse>("/login", { name, password });
    token.value = res.token;
    userId.value = res.id;
    userName.value = res.name;
    userRole.value = res.role;
    saveAuth({
      token: res.token,
      userId: res.id,
      userName: res.name,
      userRole: res.role,
    });
  },

  logout(): void {
    token.value = null;
    userId.value = null;
    userName.value = null;
    userRole.value = null;
    clearAuth();
  },
};
