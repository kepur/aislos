<template>
  <div>
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center justify-between sticky top-0 z-40 pt-safe">
      <div>
        <h1 class="font-bold text-slate-900 text-lg">New Pings</h1>
        <p class="text-xs text-slate-500">Buyer requests matching your catalog</p>
      </div>
      <div class="flex items-center gap-2">
        <NuxtLink to="/notifications">
          <button type="button" class="relative p-1">
            <svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>
        </NuxtLink>
        <NuxtLink to="/supplier/profile">
          <div class="relative w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
            <span class="text-amber-700 font-bold text-sm">{{ authStore.displayName.charAt(0) }}</span>
            <span
              v-if="trustProfile"
              class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-white text-[9px] leading-none flex items-center justify-center"
              :title="tierLabel(trustProfile.trust_tier)"
            >👑</span>
          </div>
        </NuxtLink>
      </div>
    </div>

    <!-- Stats -->
    <div class="px-4 py-3 grid grid-cols-3 gap-3">
      <div class="card text-center py-3">
        <div class="text-xl font-extrabold text-amber-600">{{ offerStore.pings.length }}</div>
        <div class="text-[11px] text-slate-500 font-medium">New Pings</div>
      </div>
      <div class="card text-center py-3">
        <div class="text-xl font-extrabold text-primary-600">{{ offerStore.myOffers.length }}</div>
        <div class="text-[11px] text-slate-500 font-medium">My Offers</div>
      </div>
      <div class="card text-center py-3">
        <div class="text-xl font-extrabold text-green-600">{{ awardedCount }}</div>
        <div class="text-[11px] text-slate-500 font-medium">Awarded</div>
      </div>
    </div>

    <!-- Pings List -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <div class="p-4">
        <div v-if="offerStore.loading" class="space-y-3">
          <div v-for="n in 4" :key="n" class="card">
            <div class="shimmer h-5 w-3/4 rounded mb-2"></div>
            <div class="shimmer h-4 w-full rounded mb-2"></div>
            <div class="shimmer h-4 w-1/2 rounded"></div>
          </div>
        </div>

        <div v-else-if="offerStore.pings.length === 0" class="empty-state">
          <svg class="w-16 h-16 text-slate-200 mb-3" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0" />
          </svg>
          <p class="text-slate-500 font-medium">No new pings yet</p>
          <p class="text-slate-400 text-xs mt-1">Add more products to your catalog to get matched</p>
          <NuxtLink to="/supplier/catalog">
            <button type="button" class="mt-4 btn-primary py-2.5 px-6 w-auto text-sm">Update Catalog</button>
          </NuxtLink>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="ping in offerStore.pings"
            :key="ping.id"
            class="card"
          >
            <!-- Category Badge -->
            <div class="flex items-start justify-between mb-2">
              <span class="badge-primary text-xs">{{ ping.category_name || "General" }}</span>
              <span class="text-xs text-slate-400">{{ formatRelativeTime(ping.created_at) }}</span>
            </div>

            <h3 class="font-bold text-slate-900 text-sm mb-1">{{ ping.title }}</h3>
            <p v-if="ping.description" class="text-xs text-slate-500 mb-2 line-clamp-2">{{ ping.description }}</p>

            <div class="flex items-center gap-3 text-xs text-slate-600 mb-3">
              <span class="flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                {{ ping.quantity }} {{ ping.unit }}
              </span>
              <span v-if="ping.budget_minor" class="flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Budget: {{ formatPrice(ping.budget_minor, ping.currency) }}
              </span>
              <span v-if="ping.radius_km" class="flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                </svg>
                {{ ping.radius_km }}km
              </span>
            </div>

            <div class="flex gap-2">
              <NuxtLink :to="`/supplier/make-offer?intent_id=${ping.id}`" class="flex-1">
                <button type="button" class="w-full py-2.5 bg-primary-600 text-white rounded-xl text-sm font-semibold active:bg-primary-700">
                  Make Offer
                </button>
              </NuxtLink>
              <NuxtLink :to="`/supplier/pings/${ping.id}`">
                <button type="button" class="px-4 py-2.5 bg-slate-100 text-slate-700 rounded-xl text-sm font-medium active:bg-slate-200">
                  View
                </button>
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </van-pull-refresh>
  </div>
</template>

<script setup lang="ts">
import type { TrustMe, TrustProfile, TrustTier } from "~/types";
import { useI18n } from "vue-i18n";

definePageMeta({ layout: "supplier", middleware: ["supplier"] });
useHead({ title: "Pings" });

const authStore = useAuthStore();
const offerStore = useOfferStore();
const { formatPrice, formatRelativeTime } = useApiUtils();
const { t } = useI18n({ useScope: "global" });
const config = useRuntimeConfig();
const refreshing = ref(false);
const trustProfile = ref<TrustProfile | null>(null);

const awardedCount = computed(() =>
  offerStore.myOffers.filter((o) => o.status === "AWARDED").length
);

async function onRefresh() {
  await offerStore.fetchPings();
  refreshing.value = false;
}

function tierLabel(tier: TrustTier) {
  const map: Record<TrustTier, string> = {
    BRONZE: t("trust.tiers.bronze"),
    SILVER: t("trust.tiers.silver"),
    GOLD: t("trust.tiers.gold"),
    PLATINUM: t("trust.tiers.platinum"),
    DIAMOND: t("trust.tiers.diamond"),
  };
  return map[tier] || tier;
}

onMounted(async () => {
  await Promise.all([offerStore.fetchPings(), offerStore.fetchMyOffers()]);
  if (!authStore.accessToken) return;
  try {
    const trust = await $fetch<TrustMe>(`${config.public.apiBase}/trust/me`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    trustProfile.value = trust.user;
  } catch {
    trustProfile.value = null;
  }
});
</script>
