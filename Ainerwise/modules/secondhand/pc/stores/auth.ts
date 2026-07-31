import { defineStore } from "pinia";

interface AuthUser {
  id: string;
  email: string;
  full_name?: string | null;
  role?: string;
  company_id?: string | null;
}

const TOKEN_KEY = "2hands_token";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as AuthUser | null,
    accessToken: null as string | null,
    ready: false,
  }),

  getters: {
    isLoggedIn: (state) => Boolean(state.accessToken),
    // Selling needs a company profile; the API enforces this too.
    canSell: (state) => Boolean(state.accessToken && state.user?.company_id),
    displayName: (state) => state.user?.full_name || state.user?.email || "Account",
  },

  actions: {
    authHeaders() {
      return this.accessToken ? { Authorization: `Bearer ${this.accessToken}` } : {};
    },

    hydrate() {
      if (!import.meta.client) return;
      this.accessToken = localStorage.getItem(TOKEN_KEY);
      this.ready = true;
      if (this.accessToken && !this.user) this.fetchMe();
    },

    async login(email: string, password: string) {
      const config = useRuntimeConfig();
      const data = await $fetch<{ access_token: string }>(`${config.public.apiBase}/auth/login`, {
        method: "POST",
        body: { email, password },
      });
      this.accessToken = data.access_token;
      if (import.meta.client) localStorage.setItem(TOKEN_KEY, data.access_token);
      await this.fetchMe();
    },

    async fetchMe() {
      const config = useRuntimeConfig();
      try {
        this.user = await $fetch<AuthUser>(`${config.public.apiBase}/auth/me`, {
          headers: this.authHeaders(),
        });
      } catch {
        this.logout();
      }
    },

    logout() {
      this.user = null;
      this.accessToken = null;
      if (import.meta.client) localStorage.removeItem(TOKEN_KEY);
    },
  },
});
