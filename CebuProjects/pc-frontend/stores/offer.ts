import { defineStore } from "pinia";
import type { Offer, Intent } from "~/types";

export const useOfferStore = defineStore("offer", {
  state: () => ({
    myOffers: [] as Offer[],
    pings: [] as Intent[],
    currentOffer: null as Offer | null,
    loading: false,
    total: 0,
  }),

  actions: {
    async fetchMyOffers(_page = 1) {
      const api = useApiFetch();
      this.loading = true;
      try {
        const data = await api<Offer[]>("/supplier/offers");
        this.myOffers = data;
        this.total = data.length;
      } finally {
        this.loading = false;
      }
    },

    async fetchPings(_page = 1) {
      const api = useApiFetch();
      this.loading = true;
      try {
        const data = await api<Intent[]>("/supplier/intents/matching");
        this.pings = data;
        this.total = data.length;
      } finally {
        this.loading = false;
      }
    },

    async submitOffer(intentId: string, payload: Record<string, unknown>) {
      const api = useApiFetch();
      const offer = await api<Offer>(`/intents/${intentId}/offers`, { method: "POST", body: payload });
      this.myOffers.unshift(offer);
      return offer;
    },

    async withdrawOffer(offerId: string) {
      const api = useApiFetch();
      return api(`/offers/${offerId}/withdraw`, { method: "POST" });
    },
  },
});
