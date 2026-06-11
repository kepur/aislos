import { defineStore } from "pinia";
import type { Order, Dispute } from "~/types";
import { demoOrders, isDemoToken } from "~/utils/demoData";

export const useOrderStore = defineStore("order", {
  state: () => ({
    orders: [] as Order[],
    currentOrder: null as Order | null,
    loading: false,
    total: 0,
  }),

  actions: {
    async fetchMyOrders(_page = 1) {
      const api = useApiFetch();
      this.loading = true;
      try {
        const data = await api<Order[]>("/orders/my");
        this.orders = data;
        this.total = data.length;
      } catch (error) {
        const authStore = useAuthStore();
        if (!authStore.isDemoMode || !isDemoToken(authStore.accessToken)) throw error;
        this.orders = demoOrders;
        this.total = demoOrders.length;
      } finally {
        this.loading = false;
      }
    },

    async fetchOrder(id: string) {
      const api = useApiFetch();
      try {
        this.currentOrder = await api<Order>(`/orders/${id}`);
      } catch (error) {
        const authStore = useAuthStore();
        if (!authStore.isDemoMode || !isDemoToken(authStore.accessToken)) throw error;
        this.currentOrder = demoOrders.find((order) => order.id === id) ?? null;
      }
      return this.currentOrder;
    },

    async acceptDelivery(orderId: string) {
      const api = useApiFetch();
      return api(`/orders/${orderId}/accept`, { method: "POST" });
    },

    async openDispute(orderId: string, reason: string) {
      const api = useApiFetch();
      return api<Dispute>(`/orders/${orderId}/dispute`, {
        method: "POST",
        body: { reason },
      });
    },

    async createDelivery(orderId: string, status: string, trackingNumber?: string, proofs: string[] = []) {
      const api = useApiFetch();
      return api(`/orders/${orderId}/delivery`, {
        method: "POST",
        body: { status, tracking_number: trackingNumber, proofs },
      });
    },
  },
});
