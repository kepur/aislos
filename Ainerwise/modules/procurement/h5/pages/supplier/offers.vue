<template>
  <div>
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center sticky top-0 z-40 pt-safe">
      <h1 class="font-bold text-slate-900 text-lg">{{ $t("supplier.my_offers") }}</h1>
    </div>

    <!-- Filter -->
    <div class="bg-white border-b border-slate-100 px-4 flex gap-1 overflow-x-auto no-scrollbar">
      <button type="button"
        v-for="tab in filterTabs"
        :key="tab.value"
        class="flex-shrink-0 py-3 px-3 text-sm font-medium border-b-2 transition-colors"
        :class="activeFilter === tab.value ? 'border-primary-600 text-primary-700' : 'border-transparent text-slate-500'"
        @click="activeFilter = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="p-4">
      <div v-if="offerStore.loading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="card"><div class="shimmer h-24 rounded"></div></div>
      </div>

      <div v-else-if="filteredOffers.length === 0" class="empty-state">
        <svg class="w-16 h-16 text-slate-200 mb-3" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
          <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z" />
        </svg>
        <p class="text-slate-500 font-medium">{{ $t("pages.no_offers_yet") }}</p>
        <NuxtLink to="/supplier/pings">
          <button type="button" class="mt-4 btn-primary py-2.5 px-6 w-auto text-sm">{{ $t("pages.view_pings") }}</button>
        </NuxtLink>
      </div>

      <div v-else class="space-y-3">
        <div v-for="offer in filteredOffers" :key="offer.id" class="card">
          <div class="flex justify-between items-start mb-2">
            <p class="font-bold text-slate-900 text-base">{{ formatPrice(offer.total_price_minor, offer.currency) }}</p>
            <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="getOfferBadgeClass(offer.status)">
              {{ getOfferStatusLabel(offer.status) }}
            </span>
          </div>
          <p class="text-xs text-slate-500 mb-2">{{ offer.qty_available }} available · {{ offer.tier }}</p>
          <p v-if="offer.message" class="text-xs text-slate-600 italic mb-3 line-clamp-2">"{{ offer.message }}"</p>
          <div class="flex justify-between items-center">
            <span class="text-xs text-slate-400">{{ formatRelativeTime(offer.created_at) }}</span>
            <button type="button"
              v-if="['SUBMITTED', 'VIEWED', 'SHORTLISTED'].includes(offer.status)"
              class="text-xs text-red-500 font-medium px-3 py-1 rounded-lg border border-red-200 active:bg-red-50"
              @click="withdrawOffer(offer.id)"
            >
              Withdraw
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showConfirmDialog, showToast } from "vant";

definePageMeta({ layout: "supplier", middleware: ["supplier"] });
useHead({ title: "My Offers" });

const offerStore = useOfferStore();
const { formatPrice, formatRelativeTime, getOfferStatusLabel } = useApiUtils();

const activeFilter = ref("ALL");
const filterTabs = [
  { label: "All", value: "ALL" },
  { label: "Active", value: "ACTIVE" },
  { label: "Awarded", value: "AWARDED" },
  { label: "Rejected", value: "REJECTED" },
];

const filteredOffers = computed(() => {
  if (activeFilter.value === "ALL") return offerStore.myOffers;
  if (activeFilter.value === "ACTIVE") {
    return offerStore.myOffers.filter((o) =>
      ["SUBMITTED", "VIEWED", "SHORTLISTED"].includes(o.status)
    );
  }
  return offerStore.myOffers.filter((o) => o.status === activeFilter.value);
});

function getOfferBadgeClass(status: string) {
  const map: Record<string, string> = {
    SUBMITTED: "badge-primary",
    VIEWED: "badge-primary",
    SHORTLISTED: "badge-warning",
    AWARDED: "badge-success",
    REJECTED: "badge-gray",
    WITHDRAWN: "badge-gray",
    EXPIRED: "badge-danger",
  };
  return map[status] || "badge-gray";
}

async function withdrawOffer(offerId: string) {
  await showConfirmDialog({ title: "Withdraw offer?", message: "This cannot be undone." });
  await offerStore.withdrawOffer(offerId);
  showToast({ type: "success", message: "Offer withdrawn" });
  await offerStore.fetchMyOffers();
}

onMounted(() => offerStore.fetchMyOffers());
</script>
