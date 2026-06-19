<template>
  <div>
    <!-- Top Bar -->
    <header class="bg-white border-b border-slate-100 px-4 flex items-center justify-between sticky top-0 z-40" style="height: 56px; padding-top: var(--safe-area-top)">
      <div>
        <p class="text-xs text-slate-500">Good {{ greeting }},</p>
        <p class="font-bold text-slate-900 text-base leading-none">{{ authStore.displayName.split(" ")[0] }}</p>
      </div>
      <div class="flex items-center gap-3">
        <NuxtLink to="/notifications" class="relative">
          <svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span v-if="notifStore.unreadCount > 0" class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold">
            {{ notifStore.unreadCount > 9 ? "9+" : notifStore.unreadCount }}
          </span>
        </NuxtLink>
        <NuxtLink to="/buyer/profile">
          <div class="relative w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
            <span class="text-primary-700 font-bold text-sm">{{ initial }}</span>
            <span
              v-if="trustProfile"
              class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-white text-[9px] leading-none flex items-center justify-center"
              :title="tierLabel(trustProfile.trust_tier)"
            >👑</span>
          </div>
        </NuxtLink>
      </div>
    </header>

    <div class="space-y-5 pb-4">
      <!-- Quick Action -->
      <div class="mx-4 mt-4">
        <div class="rounded-2xl bg-primary-600 p-5 text-white shadow-card">
          <div class="space-y-2">
            <h2 class="text-xl font-bold leading-tight">{{ $t("buyer.post_request") }}</h2>
            <p class="text-primary-100 text-sm leading-relaxed">{{ $t("pages.post_request_subtitle") }}</p>
          </div>
          <NuxtLink to="/buyer/post-request" class="block mt-4">
            <button type="button" class="w-full bg-white text-primary-700 font-semibold px-5 py-3 rounded-xl text-sm active:bg-primary-50 transition-colors">
              + Post Request
            </button>
          </NuxtLink>
        </div>
      </div>

      <!-- AI Project Forge Entry -->
      <div class="mx-4">
        <NuxtLink to="/buyer/projects" class="block rounded-2xl bg-gradient-to-r from-purple-600 to-pink-600 p-4 text-white shadow-card active:opacity-90 transition-opacity">
          <div class="flex items-center gap-3">
            <span class="text-2xl">🤖</span>
            <div class="flex-1">
              <p class="text-xs font-semibold uppercase tracking-wider opacity-80">AI Project Forge</p>
              <p class="text-sm font-bold mt-0.5">Let AI build your procurement list →</p>
            </div>
          </div>
        </NuxtLink>
      </div>

      <!-- Stats Row -->
      <div class="grid grid-cols-3 gap-3 px-4">
        <div v-for="stat in stats" :key="stat.label" class="card text-center py-3">
          <div class="text-xl font-extrabold text-primary-700">{{ stat.value }}</div>
          <div class="text-[11px] text-slate-500 font-medium mt-0.5">{{ stat.label }}</div>
        </div>
      </div>

      <section v-if="trustProfile" class="px-4">
        <div class="card">
          <div class="flex items-center justify-between mb-3">
            <div>
              <p class="text-xs text-slate-500 font-semibold uppercase tracking-wide">{{ $t("pages.buyer_trust") }}</p>
              <p class="text-2xl font-extrabold text-slate-900">{{ trustProfile.trust_score }}</p>
            </div>
            <span class="px-2.5 py-1 rounded-full text-xs font-bold" :class="tierClass(trustProfile.trust_tier)">
              {{ tierLabel(trustProfile.trust_tier) }}
            </span>
          </div>
          <div class="grid grid-cols-3 gap-2 text-center">
            <div class="bg-slate-50 rounded-xl p-2">
              <p class="text-[10px] text-slate-400">{{ $t("trust.deal_rate") }}</p>
              <p class="font-bold text-slate-800">{{ trustProfile.deal_completion_rate }}%</p>
            </div>
            <div class="bg-slate-50 rounded-xl p-2">
              <p class="text-[10px] text-slate-400">{{ $t("trust.profile_completion") }}</p>
              <p class="font-bold text-slate-800">{{ trustProfile.profile_completion_rate }}%</p>
            </div>
            <div class="bg-slate-50 rounded-xl p-2">
              <p class="text-[10px] text-slate-400">{{ $t("trust.deposit") }}</p>
              <p class="font-bold text-slate-800">{{ formatDeposit(trustProfile.deposit_amount_minor, trustProfile.deposit_currency) }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Active Requests -->
      <section class="px-4">
        <div class="flex justify-between items-center mb-3">
          <h3 class="font-bold text-slate-900">{{ $t("pages.active_requests") }}</h3>
          <NuxtLink to="/buyer/requests" class="text-sm text-primary-600 font-medium">{{ $t("pages.see_all") }}</NuxtLink>
        </div>

        <div v-if="intentStore.loading" class="space-y-3">
          <div v-for="n in 2" :key="n" class="card">
            <div class="shimmer h-4 w-3/4 rounded mb-2"></div>
            <div class="shimmer h-3 w-1/2 rounded"></div>
          </div>
        </div>

        <div v-else-if="activeIntents.length === 0" class="empty-state">
          <svg class="w-16 h-16 text-slate-300 mb-3" fill="none" stroke="currentColor" stroke-width="1" viewBox="0 0 24 24">
            <rect x="5" y="2" width="14" height="20" rx="2" />
            <path d="M9 7h6M9 11h6M9 15h4" />
          </svg>
          <p class="text-slate-500 text-sm font-medium">{{ $t("pages.no_active_requests") }}</p>
          <p class="text-slate-400 text-xs mt-1">{{ $t("pages.post_first_request_hint") }}</p>
        </div>

        <div v-else class="card-stack">
          <NuxtLink
            v-for="intent in activeIntents.slice(0, 3)"
            :key="intent.id"
            :to="`/buyer/requests/${intent.id}`"
          >
            <div class="card">
              <div class="flex justify-between items-start mb-2">
                <h4 class="font-semibold text-slate-800 text-sm flex-1 pr-2 line-clamp-1">{{ intent.title }}</h4>
                <span :class="getIntentBadgeClass(intent.status)" class="text-[11px] px-2 py-0.5 rounded-full font-medium flex-shrink-0">
                  {{ getIntentStatusLabel(intent.status) }}
                </span>
              </div>
              <div class="flex items-center gap-3 text-xs text-slate-500">
                <span>{{ intent.qty }} {{ intent.unit }}</span>
                <span v-if="intent.budget_max_minor">• Budget: {{ formatPrice(intent.budget_max_minor, intent.currency) }}</span>
              </div>
            </div>
          </NuxtLink>
        </div>
      </section>

      <!-- Recent Orders -->
      <section class="px-4">
        <div class="flex justify-between items-center mb-3">
          <h3 class="font-bold text-slate-900">{{ $t("pages.recent_orders") }}</h3>
          <NuxtLink to="/buyer/orders" class="text-sm text-primary-600 font-medium">{{ $t("pages.see_all") }}</NuxtLink>
        </div>

        <div v-if="orderStore.orders.length === 0" class="card py-6 text-center">
          <p class="text-slate-400 text-sm">{{ $t("pages.no_orders_yet") }}</p>
        </div>

        <div v-else class="card-stack">
          <NuxtLink
            v-for="order in orderStore.orders.slice(0, 2)"
            :key="order.id"
            :to="`/buyer/orders/${order.id}`"
          >
            <div class="card flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-slate-800 text-sm truncate">Order #{{ order.id.slice(0, 8) }}</p>
                <p class="text-xs text-slate-500">{{ formatPrice(order.total_amount_minor, order.currency) }} · {{ formatDate(order.created_at) }}</p>
              </div>
              <span class="text-xs px-2 py-1 rounded-full font-medium" :class="getOrderBadgeClass(order.status)">
                {{ getOrderStatusLabel(order.status) }}
              </span>
            </div>
          </NuxtLink>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TrustMe, TrustProfile, TrustTier } from "~/types";
import { useI18n } from "vue-i18n";

definePageMeta({ layout: "buyer", middleware: ["buyer"] });
useHead({ title: "Home" });

const authStore = useAuthStore();
const intentStore = useIntentStore();
const orderStore = useOrderStore();
const notifStore = useNotificationStore();
const config = useRuntimeConfig();
const trustProfile = ref<TrustProfile | null>(null);
const { t } = useI18n({ useScope: "global" });

const { formatPrice, formatDate, getIntentStatusLabel, getOrderStatusLabel } = useApiUtils();

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  return "evening";
});

const initial = computed(() => authStore.displayName.charAt(0).toUpperCase());

const activeIntents = computed(() =>
  intentStore.intents.filter((i) => ["ACTIVE", "AWARDED"].includes(i.status))
);

const stats = computed(() => [
  { label: "Requests", value: intentStore.intents.length },
  { label: "Active", value: activeIntents.value.length },
  { label: "Orders", value: orderStore.orders.length },
]);

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

function getOrderBadgeClass(status: string) {
  const map: Record<string, string> = {
    PAID_IN_ESCROW: "badge-warning",
    IN_PROGRESS: "badge-primary",
    DELIVERED: "badge-success",
    ACCEPTED: "badge-success",
    DISPUTED: "badge-danger",
    REFUNDED: "badge-gray",
    PAYOUT_RELEASED: "badge-success",
    CANCELED: "badge-gray",
  };
  return map[status] || "badge-gray";
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

function tierClass(tier: TrustTier) {
  return {
    BRONZE: "bg-amber-100 text-amber-700",
    SILVER: "bg-slate-100 text-slate-700",
    GOLD: "bg-yellow-100 text-yellow-700",
    PLATINUM: "bg-primary-100 text-primary-700",
    DIAMOND: "bg-green-100 text-green-700",
  }[tier] || "bg-slate-100 text-slate-700";
}

function formatDeposit(minor: number, currency = "PHP") {
  if (!minor) return "0";
  const amount = minor / 100;
  if (currency === "USDT") {
    return `${amount.toLocaleString("en-PH", { notation: "compact", maximumFractionDigits: 1 })} USDT`;
  }
  try {
    return new Intl.NumberFormat("en-PH", {
      style: "currency",
      currency,
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(amount);
  } catch {
    return `${amount.toLocaleString("en-PH", { notation: "compact", maximumFractionDigits: 1 })} ${currency}`;
  }
}

onMounted(async () => {
  await Promise.all([
    intentStore.fetchMyIntents(),
    orderStore.fetchMyOrders(),
    notifStore.fetchNotifications(),
  ]);
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
