import { computed, ref } from "vue";
import { api } from "../api/client";

const TOKEN_KEY = "homeos_token";
const USER_KEY = "homeos_user";

const token = ref<string | null>(localStorage.getItem(TOKEN_KEY));
const userId = ref<string | null>(localStorage.getItem(USER_KEY));

interface LoginResponse {
  token: string;
  user_id: string;
}

export const auth = {
  isAuthenticated: computed(() => token.value !== null),
  userId: computed(() => userId.value),
  getToken: () => token.value,

  async login(username: string, password: string): Promise<void> {
    const res = await api.post<LoginResponse>("/login", { username, password });
    token.value = res.token;
    userId.value = res.user_id;
    localStorage.setItem(TOKEN_KEY, res.token);
    localStorage.setItem(USER_KEY, res.user_id);
  },

  logout(): void {
    token.value = null;
    userId.value = null;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};
