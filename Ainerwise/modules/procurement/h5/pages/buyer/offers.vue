<template>
  <div>
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center sticky top-0 z-40 pt-safe">
      <h1 class="font-bold text-slate-900 text-lg">{{ $t("account.offers_received") }}</h1>
    </div>

    <div class="p-4">
      <div v-if="loading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="card"><div class="shimmer h-24 rounded"></div></div>
      </div>

      <div v-else-if="allOffers.length === 0" class="empty-state">
        <svg class="w-16 h-16 text-slate-200 mb-3" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
          <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z" />
        </svg>
        <p class="text-slate-500 font-medium">{{ $t("pages.no_offers_yet") }}</p>
        <p class="text-slate-400 text-xs mt-1">{{ $t("pages.post_request_to_receive_offers") }}</p>
        <NuxtLink to="/buyer/post-request">
          <button type="button" class="mt-4 btn-primary py-2.5 px-6 w-auto text-sm">{{ $t("buyer.post_request") }}</button>
        </NuxtLink>
      </div>

      <!-- Group by intent -->
      <div v-else class="space-y-5">
        <div v-for="group in groupedOffers" :key="group.intentId">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold text-slate-800 text-sm line-clamp-1 flex-1 pr-2">{{ group.intentTitle }}</h3>
            <NuxtLink v-if="group.offers.length > 1" :to="`/buyer/compare?intent_id=${group.intentId}`" class="text-xs text-primary-600 font-medium flex-shrink-0">
              Compare ({{ group.offers.length }})
            </NuxtLink>
          </div>

          <div class="space-y-2">
            <NuxtLink v-for="offer in group.offers" :key="offer.id" :to="`/buyer/requests/${group.intentId}`">
              <div class="card border" :class="offer.status === 'AWARDED' ? 'border-green-300' : 'border-transparent'">
                <div class="flex justify-between items-start">
                  <div>
                    <p class="font-bold text-slate-900 text-base">{{ formatPrice(offer.total_price_minor, offer.currency) }}</p>
                    <p class="text-xs text-slate-500 mt-0.5">{{ offer.qty_available }} available<span v-if="offer.eta_date"> · ETA {{ offer.eta_date }}</span></p>
                  </div>
                  <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="getOfferBadgeClass(offer.status)">
                    {{ getOfferStatusLabel(offer.status) }}
                  </span>
                </div>
              </div>
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Offer } from "~/types";
import { demoOffersForIntent, isDemoToken } from "~/utils/demoData";

definePageMeta({ layout: "buyer", middleware: ["buyer"] });
useHead({ title: "Offers" });

const intentStore = useIntentStore();
const { formatPrice, getOfferStatusLabel } = useApiUtils();
const config = useRuntimeConfig();
const authStore = useAuthStore();

const loading = ref(true);
const allOffers = ref<Offer[]>([]);

const groupedOffers = computed(() => {
  const groups: Record<string, { intentId: string; intentTitle: string; offers: Offer[] }> = {};
  for (const offer of allOffers.value) {
    if (!groups[offer.intent_id]) {
      const intent = intentStore.intents.find((i) => i.id === offer.intent_id);
      groups[offer.intent_id] = {
        intentId: offer.intent_id,
        intentTitle: intent?.title || `Request ${offer.intent_id.slice(0, 8)}`,
        offers: [],
      };
    }
    groups[offer.intent_id].offers.push(offer);
  }
  return Object.values(groups);
});

function getOfferBadgeClass(status: string) {
  const map: Record<string, string> = {
    SUBMITTED: "badge-primary",
    VIEWED: "badge-primary",
    SHORTLISTED: "badge-warning",
    AWARDED: "badge-success",
    REJECTED: "badge-gray",
    WITHDRAWN: "badge-gray",
  };
  return map[status] || "badge-gray";
}

onMounted(async () => {
  await intentStore.fetchMyIntents();
  // Fetch offers for all intents
  const offerPromises = intentStore.intents.map((intent) =>
    $fetch<Offer[]>(`${config.public.apiBase}/intents/${intent.id}/offers`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    }).catch(() => isDemoToken(authStore.accessToken) ? demoOffersForIntent(intent.id) : [] as Offer[])
  );
  const results = await Promise.all(offerPromises);
  allOffers.value = results.flat();
  loading.value = false;
});
</script>
