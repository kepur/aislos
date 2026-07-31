import { defineStore } from "pinia";
import type { User, UserRole } from "~/types";
import { demoUserForEmail, demoUserForToken, isDemoEmail, isDemoToken } from "~/utils/demoData";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  systemMode: { demo_mode: boolean; registration_enabled: boolean; app_name: string; intent_max_attachments: number } | null;
}

function coreRoleToLegacy(role?: string): UserRole {
  const value = (role || "").toLowerCase();
  if (value === "buyer" || value === "customer_user") return "BUYER";
  if (value === "vendor") return "SUPPLIER_ADMIN";
  if (value === "super_admin") return "SUPER_ADMIN";
  if (value === "admin") return "ADMIN";
  if (value === "finance") return "FINANCE_OFFICER";
  return (role || "BUYER").toUpperCase() as UserRole;
}

function legacyRoleToCore(role: UserRole): string {
  if (role === "BUYER") return "buyer";
  if (role === "SUPPLIER_ADMIN" || role === "SUPPLIER_AGENT") return "vendor";
  if (role === "SUPER_ADMIN") return "super_admin";
  if (role === "ADMIN" || role === "OPS_MANAGER") return "admin";
  return role.toLowerCase();
}

function normalizeUser(raw: any): User {
  return {
    ...raw,
    full_name: raw?.full_name || raw?.email || "User",
    role: coreRoleToLegacy(raw?.role),
    status: raw?.status || (raw?.is_active === false ? "INACTIVE" : "ACTIVE"),
    two_fa_enabled: Boolean(raw?.two_fa_enabled),
  };
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    systemMode: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.accessToken && !!state.user,
    isBuyer: (state) => state.user?.role === "BUYER",
    isSupplier: (state) =>
      state.user?.role === "SUPPLIER_ADMIN" || state.user?.role === "SUPPLIER_AGENT",
    isAdmin: (state) =>
      ["ADMIN", "SUPER_ADMIN", "OPS_MANAGER"].includes(state.user?.role ?? ""),
    userRole: (state): UserRole | null => state.user?.role ?? null,
    displayName: (state) => state.user?.full_name || state.user?.email || "User",
    isDemoMode: (state) => state.systemMode?.demo_mode ?? false,
    isRegistrationEnabled: (state) => state.systemMode?.registration_enabled ?? false,
    intentMaxAttachments: (state) => state.systemMode?.intent_max_attachments ?? 10,
  },

  actions: {
    async login(email: string, password: string) {
      const config = useRuntimeConfig();
      let data: { access_token: string; refresh_token: string };

      try {
        data = await $fetch<{ access_token: string; refresh_token: string }>(
          `${config.public.apiBase}/auth/login`,
          { method: "POST", body: { email, password } }
        );
      } catch (error) {
        const demoUser = demoUserForEmail(email);
        if (!this.systemMode?.demo_mode || !demoUser || password !== "123") {
          throw error;
        }
        data = {
          access_token: demoUser.role === "BUYER" ? "demo-buyer-token" : "demo-supplier-token",
          refresh_token: demoUser.role === "BUYER" ? "demo-buyer-refresh" : "demo-supplier-refresh",
        };
        this.user = demoUser;
      }

      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      this._persist();
      if (!isDemoToken(this.accessToken)) {
        await this.fetchMe();
      }
    },

    async register(payload: {
      email: string;
      password: string;
      full_name: string;
      role: UserRole;
      phone?: string;
    }) {
      const config = useRuntimeConfig();
      const data = await $fetch<{ access_token: string; refresh_token: string }>(
        `${config.public.apiBase}/auth/register`,
        {
          method: "POST",
          body: {
            ...payload,
            role: legacyRoleToCore(payload.role),
            company_type: payload.role === "BUYER" ? "buyer" : "vendor",
          },
        }
      );
      this.accessToken = data.access_token;
      this.refreshToken = data.refresh_token;
      this._persist();
      await this.fetchMe();
    },

    async fetchMe() {
      if (!this.accessToken) return;
      const config = useRuntimeConfig();
      if (isDemoToken(this.accessToken)) {
        if (this.systemMode?.demo_mode === false) {
          this.logout();
          return;
        }
        this.user = demoUserForToken(this.accessToken);
        return;
      }
      try {
        this.user = normalizeUser(await $fetch<User>(`${config.public.apiBase}/auth/me`, {
          headers: { Authorization: `Bearer ${this.accessToken}` },
        }));
      } catch {
        this.logout();
      }
    },

    async fetchSystemMode() {
      const config = useRuntimeConfig();
      try {
        this.systemMode = await $fetch(`${config.public.apiBase}/auth/system-mode`);
        if (!this.systemMode.demo_mode && isDemoToken(this.accessToken)) {
          this.logout();
        }
      } catch {
        this.systemMode = { demo_mode: false, registration_enabled: true, app_name: "AISLOS Market", intent_max_attachments: 10 };
      }
    },

    async logout() {
      this.user = null;
      this.accessToken = null;
      this.refreshToken = null;
      if (import.meta.client) {
        localStorage.removeItem("pp_access_token");
        localStorage.removeItem("pp_refresh_token");
        localStorage.removeItem("pp_demo_user");
        localStorage.removeItem("ainerwise_token");
        localStorage.removeItem("ainerwise_refresh");
      }
    },

    hydrate() {
      if (!import.meta.client) return;
      this.accessToken = localStorage.getItem("pp_access_token") || localStorage.getItem("ainerwise_token");
      this.refreshToken = localStorage.getItem("pp_refresh_token") || localStorage.getItem("ainerwise_refresh");
      if (isDemoToken(this.accessToken)) {
        if (this.systemMode?.demo_mode === false) {
          this.logout();
          return;
        }
        this.user = demoUserForToken(this.accessToken);
      }
    },

    _persist() {
      if (!import.meta.client) return;
      if (this.accessToken) localStorage.setItem("pp_access_token", this.accessToken);
      if (this.refreshToken) localStorage.setItem("pp_refresh_token", this.refreshToken);
      if (this.accessToken) localStorage.setItem("ainerwise_token", this.accessToken);
      if (this.refreshToken) localStorage.setItem("ainerwise_refresh", this.refreshToken);
      if (this.user && isDemoEmail(this.user.email)) {
        localStorage.setItem("pp_demo_user", JSON.stringify(this.user));
      }
    },
  },
});
