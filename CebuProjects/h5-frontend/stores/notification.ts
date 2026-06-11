import { defineStore } from "pinia";
import type { Notification } from "~/types";
import { demoNotifications, isDemoToken } from "~/utils/demoData";

export const useNotificationStore = defineStore("notification", {
  state: () => ({
    notifications: [] as Notification[],
    unreadCount: 0,
    loading: false,
  }),

  actions: {
    async fetchNotifications() {
      const api = useApiFetch();
      this.loading = true;
      try {
        const data = await api<Notification[]>("/notifications/my");
        // normalise: map status to is_read for template convenience
        this.notifications = data.map((n) => ({ ...n, is_read: n.status === "READ" }));
        this.unreadCount = this.notifications.filter((n) => !n.is_read).length;
      } catch (error) {
        const authStore = useAuthStore();
        if (!authStore.isDemoMode || !isDemoToken(authStore.accessToken)) throw error;
        this.notifications = demoNotifications;
        this.unreadCount = demoNotifications.filter((n) => !n.is_read).length;
      } finally {
        this.loading = false;
      }
    },

    async markRead(id: string) {
      const api = useApiFetch();
      await api(`/notifications/${id}/read`, { method: "POST" });
      const n = this.notifications.find((n) => n.id === id);
      if (n && !n.is_read) {
        n.is_read = true;
        this.unreadCount = Math.max(0, this.unreadCount - 1);
      }
    },

    async markAllRead() {
      const api = useApiFetch();
      await api("/notifications/read-all", { method: "POST" });
      this.notifications.forEach((n) => (n.is_read = true));
      this.unreadCount = 0;
    },
  },
});
