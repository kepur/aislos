import { defineStore } from "pinia";
import type { Intent, Offer, PaginatedResponse } from "~/types";
import { demoIntents, isDemoToken } from "~/utils/demoData";

function extractErrorMessage(error: unknown, fallback: string) {
  const err = error as { data?: { detail?: unknown }; message?: string };
  const detail = err?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (err?.message) return err.message;
  return fallback;
}

export const useIntentStore = defineStore("intent", {
  state: () => ({
    intents: [] as Intent[],
    currentIntent: null as Intent | null,
    offers: [] as Offer[],
    offerError: "",
    loading: false,
    total: 0,
  }),

  actions: {
    async fetchMyIntents(page = 1) {
      const api = useApiFetch();
      this.loading = true;
      try {
        const data = await api<PaginatedResponse<Intent> | Intent[]>(`/intents/my?page=${page}&page_size=20`);
        if (Array.isArray(data)) {
          this.intents = data;
          this.total = data.length;
        } else {
          this.intents = data.items;
          this.total = data.total;
        }
      } catch (error) {
        const authStore = useAuthStore();
        if (!authStore.isDemoMode || !isDemoToken(authStore.accessToken)) throw error;
        this.intents = demoIntents;
        this.total = demoIntents.length;
      } finally {
        this.loading = false;
      }
    },

    async fetchIntent(id: string) {
      const api = useApiFetch();
      try {
        this.currentIntent = await api<Intent>(`/intents/${id}`);
      } catch (error) {
        const authStore = useAuthStore();
        if (!authStore.isDemoMode || !isDemoToken(authStore.accessToken)) throw error;
        this.currentIntent = demoIntents.find((intent) => intent.id === id) ?? null;
      }
      return this.currentIntent;
    },

    async createIntent(payload: Record<string, unknown>) {
      const api = useApiFetch();
      let intent: Intent;
      try {
        intent = await api<Intent>("/intents", { method: "POST", body: payload });
      } catch (error) {
        const authStore = useAuthStore();
        if (!authStore.isDemoMode || !isDemoToken(authStore.accessToken)) throw error;
        intent = {
          id: `demo-intent-${Date.now()}`,
          buyer_id: authStore.user?.id || "demo-buyer",
          category_id: String(payload.category_id || "demo-category"),
          title: String(payload.title || "Demo Request"),
          notes: String(payload.notes || ""),
          qty: Number(payload.qty || 1),
          unit: String(payload.unit || "pcs"),
          currency: String(payload.currency || "PHP"),
          city: String(payload.city || "Cebu City"),
          radius_km: Number(payload.radius_km || 25),
          status: "ACTIVE",
          created_at: new Date().toISOString(),
          offer_count: 0,
        };
      }
      this.intents.unshift(intent);
      return intent;
    },

    async fetchOffers(intentId: string) {
      const api = useApiFetch();
      this.offerError = "";
      try {
        this.offers = await api<Offer[]>(`/intents/${intentId}/offers`);
      } catch (error) {
        this.offers = [];
        this.offerError = extractErrorMessage(error, "Unable to load offers for this request.");
      }
    },

    async awardOffer(offerId: string) {
      const api = useApiFetch();
      return api(`/offers/${offerId}/award`, { method: "POST" });
    },
  },
});
