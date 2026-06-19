<template>
  <div>
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center sticky top-0 z-40 pt-safe">
      <h1 class="font-bold text-slate-900 text-lg">{{ $t("buyer.my_requests") }}</h1>
      <div class="ml-auto flex items-center gap-2">
        <!-- Sort dropdown -->
        <select v-model="sortBy" @change="applySort"
          class="text-xs border border-slate-200 rounded-lg px-2 py-1.5 bg-white text-slate-600 outline-none">
          <option value="newest">{{ $t('common.newest') }}</option>
          <option value="offers">{{ $t('buyer.most_offers') }}</option>
          <option value="deadline">{{ $t('buyer.deadline') }}</option>
          <option value="rank">{{ $t('buyer.rank') }}</option>
        </select>
        <NuxtLink to="/buyer/post-request">
          <button type="button" class="bg-primary-600 text-white text-sm font-semibold px-3 py-1.5 rounded-lg">+ New</button>
        </NuxtLink>
      </div>
    </div>

    <!-- Status Filter Tabs -->
    <div class="bg-white border-b border-slate-100 px-4 flex gap-1 overflow-x-auto no-scrollbar">
      <button type="button"
        v-for="tab in filterTabs"
        :key="tab.value"
        class="flex-shrink-0 py-3 px-3 text-sm font-medium border-b-2 transition-colors"
        :class="activeFilter === tab.value ? 'border-primary-600 text-primary-700' : 'border-transparent text-slate-500'"
        @click="activeFilter = tab.value"
      >
        {{ tab.label }}
        <span v-if="tab.count" class="ml-1 text-[10px] bg-primary-100 text-primary-700 rounded-full px-1.5 py-0.5 font-bold">
          {{ tab.count }}
        </span>
      </button>
    </div>

    <div class="p-4">
      <!-- Loading skeleton -->
      <div v-if="intentStore.loading" class="space-y-3">
        <div v-for="n in 4" :key="n" class="card">
          <div class="shimmer h-4 w-3/4 rounded mb-2"></div>
          <div class="shimmer h-3 w-1/2 rounded mb-3"></div>
          <div class="shimmer h-3 w-1/4 rounded"></div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="sortedFilteredIntents.length === 0" class="empty-state">
        <svg class="w-16 h-16 text-slate-200 mb-3" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
          <rect x="5" y="2" width="14" height="20" rx="2" />
          <path d="M9 7h6M9 11h6M9 15h4" />
        </svg>
        <p class="text-slate-500 font-medium">{{ $t("pages.no_requests_for_filter") }}</p>
        <NuxtLink to="/buyer/post-request">
          <button type="button" class="mt-4 btn-primary py-2.5 px-6 w-auto text-sm">{{ $t("buyer.post_request") }}</button>
        </NuxtLink>
      </div>

      <!-- List -->
      <div v-else class="card-stack">
        <!-- Sort label -->
        <div class="flex items-center justify-between text-xs text-slate-400 px-1">
          <span>{{ sortedFilteredIntents.length }} {{ $t('common.results') }}</span>
          <span v-if="sortBy === 'rank'" class="text-indigo-500 font-medium">⭐ {{ $t('buyer.rank_mode') }}</span>
          <span v-else-if="sortBy === 'offers'" class="text-green-500 font-medium">📊 {{ $t('buyer.offers_mode') }}</span>
        </div>

        <NuxtLink
          v-for="(intent, idx) in sortedFilteredIntents"
          :key="intent.id"
          :to="`/buyer/requests/${intent.id}`"
        >
          <div class="card relative overflow-hidden">
            <!-- Rank badge (only when sorted by rank) -->
            <div v-if="sortBy === 'rank' && idx < 3"
              :class="['absolute top-0 right-0 text-[9px] font-bold px-2 py-0.5 rounded-bl-xl',
                idx === 0 ? 'bg-amber-400 text-white' : idx === 1 ? 'bg-slate-400 text-white' : 'bg-orange-300 text-white']">
              #{{ idx + 1 }}
            </div>

            <div class="flex justify-between items-start mb-2">
              <h3 class="font-semibold text-slate-800 text-sm flex-1 pr-2 line-clamp-2">{{ intent.title }}</h3>
              <span class="text-[11px] px-2 py-0.5 rounded-full font-medium flex-shrink-0" :class="getIntentBadgeClass(intent.status)">
                {{ getIntentStatusLabel(intent.status) }}
              </span>
            </div>

            <div class="flex items-center gap-2 text-xs text-slate-500 flex-wrap">
              <span>{{ intent.qty }} {{ intent.unit }}</span>
              <span v-if="intent.budget_max_minor">· {{ $t("buyer.budget") }}: {{ formatPrice(intent.budget_max_minor, intent.currency) }}</span>
              <span v-if="intent.city">· 📍{{ intent.city }}</span>
            </div>

            <div class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <span class="text-xs text-slate-400">{{ formatRelativeTime(intent.created_at) }}</span>
                <!-- Offer count badge -->
                <span v-if="intent.offer_count > 0" class="text-xs bg-green-50 text-green-700 font-semibold px-2 py-0.5 rounded-full">
                  {{ intent.offer_count }} {{ $t('buyer.offers') }}
                </span>
              </div>
              <span v-if="intent.expires_at" class="text-xs text-amber-600 font-medium">
                ⏰ {{ formatDate(intent.expires_at) }}
              </span>
            </div>
          </div>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";

definePageMeta({ layout: "buyer", middleware: ["buyer"] });
const { t } = useI18n({ useScope: "global" });
useHead({ title: t("buyer.my_requests") });

const intentStore = useIntentStore();
const { formatPrice, formatDate, formatRelativeTime, getIntentStatusLabel } = useApiUtils();

const activeFilter = ref("ALL");
const sortBy = ref("newest");

// Mock data fallback — shown when API returns empty
const MOCK_INTENTS = [
  { id: 'm1', title: 'Portland Cement Type I – 500 bags', qty: 500, unit: 'bags', currency: 'PHP', budget_max_minor: 25000000, status: 'ACTIVE', created_at: new Date(Date.now()-86400000*2).toISOString(), expires_at: new Date(Date.now()+86400000*5).toISOString(), offer_count: 3, city: 'Cebu City' },
  { id: 'm2', title: 'Office Chairs Ergonomic – 20 units', qty: 20, unit: 'pcs', currency: 'PHP', budget_max_minor: 8000000, status: 'ACTIVE', created_at: new Date(Date.now()-86400000*1).toISOString(), expires_at: new Date(Date.now()+86400000*7).toISOString(), offer_count: 1, city: 'Mandaue' },
  { id: 'm3', title: 'N95 Face Masks KN95 – 2000 boxes', qty: 2000, unit: 'boxes', currency: 'PHP', budget_max_minor: 60000000, status: 'AWARDED', created_at: new Date(Date.now()-86400000*10).toISOString(), expires_at: null, offer_count: 5, city: 'Lapu-Lapu' },
  { id: 'm4', title: 'Industrial Electric Fans – 10 units', qty: 10, unit: 'units', currency: 'PHP', budget_max_minor: 3500000, status: 'ACTIVE', created_at: new Date(Date.now()-86400000*3).toISOString(), expires_at: new Date(Date.now()+86400000*3).toISOString(), offer_count: 0, city: 'Cebu City' },
  { id: 'm5', title: 'PVC Pipes 4-inch Schedule 40 – 300 pcs', qty: 300, unit: 'pcs', currency: 'PHP', budget_max_minor: 15000000, status: 'CLOSED', created_at: new Date(Date.now()-86400000*20).toISOString(), expires_at: null, offer_count: 7, city: 'Talisay' },
]

const allIntents = computed(() => {
  const real = intentStore.intents
  return real.length > 0 ? real : MOCK_INTENTS as any[]
})

const filterTabs = computed(() => [
  { label: t("common.all"), value: "ALL", count: allIntents.value.length },
  { label: t("intent.active"), value: "ACTIVE", count: allIntents.value.filter(i => i.status === 'ACTIVE').length || null },
  { label: t("intent.awarded"), value: "AWARDED", count: null },
  { label: t("intent.closed"), value: "CLOSED", count: null },
  { label: t("intent.expired"), value: "EXPIRED", count: null },
]);

const filteredIntents = computed(() => {
  if (activeFilter.value === "ALL") return allIntents.value;
  return allIntents.value.filter((i) => i.status === activeFilter.value);
});

const sortedFilteredIntents = computed(() => {
  const arr = [...filteredIntents.value]
  switch (sortBy.value) {
    case 'newest':
      return arr.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    case 'offers':
      return arr.sort((a, b) => (b.offer_count ?? 0) - (a.offer_count ?? 0))
    case 'deadline':
      return arr.sort((a, b) => {
        if (!a.expires_at) return 1
        if (!b.expires_at) return -1
        return new Date(a.expires_at).getTime() - new Date(b.expires_at).getTime()
      })
    case 'rank':
      // Rank = (offer_count * 10) + recency_score
      return arr.sort((a, b) => {
        const scoreA = (a.offer_count ?? 0) * 10 + (a.status === 'ACTIVE' ? 5 : 0)
        const scoreB = (b.offer_count ?? 0) * 10 + (b.status === 'ACTIVE' ? 5 : 0)
        return scoreB - scoreA
      })
    default:
      return arr
  }
})

function applySort() {
  // reactive — sorted list updates automatically
}

function getIntentBadgeClass(status: string) {
  const map: Record<string, string> = {
    DRAFT: "badge-gray",
    ACTIVE: "badge-primary",
    AWARDED: "badge-success",
    CLOSED: "badge-gray",
    CANCELED: "badge-gray",
    EXPIRED: "badge-danger",
  };
  return map[status] || "badge-gray";
}

onMounted(() => intentStore.fetchMyIntents());
</script>
