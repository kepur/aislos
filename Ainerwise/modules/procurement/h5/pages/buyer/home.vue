<template>
  <div>
    <!-- Top Bar -->
    <header class="bg-white border-b border-slate-100 px-4 flex items-center justify-between sticky top-0 z-40" style="height: 56px; padding-top: var(--safe-area-top)">
      <div>
        <p class="text-xs text-slate-500">{{ greeting }},</p>
        <p class="font-bold text-slate-900 text-base leading-none">{{ authStore.displayName.split(" ")[0] }}</p>
      </div>
      <div class="flex items-center gap-3">
        <NuxtLink :to="localizedPath('/notifications')" class="relative">
          <svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span v-if="notifStore.unreadCount > 0" class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center font-bold">
            {{ notifStore.unreadCount > 9 ? "9+" : notifStore.unreadCount }}
          </span>
        </NuxtLink>
        <NuxtLink :to="localizedPath('/buyer/profile')">
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
      <!-- Official AI Building Entry -->
      <section class="mx-4 mt-4">
        <NuxtLink
          :to="localizedPath('/')"
          class="flex items-center justify-between gap-3 rounded-2xl border border-emerald-100 bg-white p-4 shadow-card active:bg-emerald-50/60"
        >
          <div class="min-w-0">
            <p class="text-[10px] font-extrabold uppercase tracking-[0.16em] text-emerald-600">
              {{ homeCopy.officialKicker }}
            </p>
            <p class="mt-1 truncate text-sm font-bold text-slate-900">
              {{ homeCopy.officialTitle }}
            </p>
            <p class="mt-0.5 text-xs text-slate-500">
              {{ homeCopy.officialSubtitle }}
            </p>
          </div>
          <span class="flex h-9 w-9 flex-none items-center justify-center rounded-full bg-slate-950 text-white">→</span>
        </NuxtLink>
      </section>

      <!-- Quick Action -->
      <div class="mx-4">
        <div class="rounded-2xl bg-primary-600 p-5 text-white shadow-card">
          <div class="space-y-2">
            <h2 class="text-xl font-bold leading-tight">{{ $t("buyer.post_request") }}</h2>
            <p class="text-primary-100 text-sm leading-relaxed">{{ $t("pages.post_request_subtitle") }}</p>
          </div>
          <NuxtLink :to="localizedPath('/buyer/post-request?mode=market')" class="block mt-4">
            <button type="button" class="w-full bg-white text-primary-700 font-semibold px-5 py-3 rounded-xl text-sm active:bg-primary-50 transition-colors">
              {{ homeCopy.postButton }}
            </button>
          </NuxtLink>
        </div>
      </div>

      <!-- AI Project Forge Entry -->
      <div class="mx-4">
        <NuxtLink :to="localizedPath('/buyer/projects')" class="block rounded-2xl bg-gradient-to-r from-purple-600 to-pink-600 p-4 text-white shadow-card active:opacity-90 transition-opacity">
          <div class="flex items-center gap-3">
            <span class="flex h-10 w-10 flex-none items-center justify-center rounded-2xl bg-white/15 text-sm font-black ring-1 ring-white/20">AI</span>
            <div class="flex-1">
              <p class="text-xs font-semibold uppercase tracking-wider opacity-80">{{ homeCopy.forgeKicker }}</p>
              <p class="text-sm font-bold mt-0.5">{{ homeCopy.forgeTitle }} →</p>
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
          <NuxtLink :to="localizedPath('/buyer/requests')" class="text-sm text-primary-600 font-medium">{{ $t("pages.see_all") }}</NuxtLink>
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
            :to="localizedPath(`/buyer/requests/${intent.id}`)"
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
                <span v-if="intent.budget_max_minor">• {{ homeCopy.budget }}: {{ formatPrice(intent.budget_max_minor, intent.currency) }}</span>
              </div>
            </div>
          </NuxtLink>
        </div>
      </section>

      <!-- Recent Orders -->
      <section class="px-4">
        <div class="flex justify-between items-center mb-3">
          <h3 class="font-bold text-slate-900">{{ $t("pages.recent_orders") }}</h3>
          <NuxtLink :to="localizedPath('/buyer/orders')" class="text-sm text-primary-600 font-medium">{{ $t("pages.see_all") }}</NuxtLink>
        </div>

        <div v-if="orderStore.orders.length === 0" class="card py-6 text-center">
          <p class="text-slate-400 text-sm">{{ $t("pages.no_orders_yet") }}</p>
        </div>

        <div v-else class="card-stack">
          <NuxtLink
            v-for="order in orderStore.orders.slice(0, 2)"
            :key="order.id"
            :to="localizedPath(`/buyer/orders/${order.id}`)"
          >
            <div class="card flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-slate-800 text-sm truncate">{{ homeCopy.orderPrefix }} #{{ order.id.slice(0, 8) }}</p>
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
import { getLocalePrefixFromPath, withLocalePrefix } from "~/utils/localeRoutes";

definePageMeta({ layout: "buyer", middleware: ["buyer"] });

const authStore = useAuthStore();
const intentStore = useIntentStore();
const orderStore = useOrderStore();
const notifStore = useNotificationStore();
const config = useRuntimeConfig();
const route = useRoute();
const trustProfile = ref<TrustProfile | null>(null);
const { t, locale } = useI18n({ useScope: "global" });

const { formatPrice, formatDate, getIntentStatusLabel, getOrderStatusLabel } = useApiUtils();

const copyByLocale: Record<string, Record<string, string>> = {
  en: {
    pageTitle: "Home",
    goodMorning: "Good morning",
    goodAfternoon: "Good afternoon",
    goodEvening: "Good evening",
    officialKicker: "Official AI smart building",
    officialTitle: "KNX + AI building brain, solutions and product paths",
    officialSubtitle: "Open the official mobile site",
    postButton: "+ Post Request",
    forgeKicker: "AI Project Forge",
    forgeTitle: "Let AI build your procurement list",
    requests: "Requests",
    active: "Active",
    orders: "Orders",
    budget: "Budget",
    orderPrefix: "Order",
  },
  zh: {
    pageTitle: "首页",
    goodMorning: "早上好",
    goodAfternoon: "下午好",
    goodEvening: "晚上好",
    officialKicker: "官方 AI 智能建筑",
    officialTitle: "KNX + AI 建筑大脑、解决方案和产品路径",
    officialSubtitle: "打开手机官网",
    postButton: "+ 发布需求",
    forgeKicker: "AI 项目工坊",
    forgeTitle: "让 AI 生成采购清单",
    requests: "需求",
    active: "进行中",
    orders: "订单",
    budget: "预算",
    orderPrefix: "订单",
  },
  sr: {
    pageTitle: "Pocetna",
    goodMorning: "Dobro jutro",
    goodAfternoon: "Dobar dan",
    goodEvening: "Dobro vece",
    officialKicker: "Zvanicni AI smart building",
    officialTitle: "KNX + AI mozak zgrade, resenja i proizvodi",
    officialSubtitle: "Otvori mobilni zvanicni sajt",
    postButton: "+ Objavi zahtev",
    forgeKicker: "AI Project Forge",
    forgeTitle: "Neka AI napravi listu nabavke",
    requests: "Zahtevi",
    active: "Aktivno",
    orders: "Porudzbine",
    budget: "Budzet",
    orderPrefix: "Porudzbina",
  },
  pl: {
    pageTitle: "Start",
    goodMorning: "Dzien dobry",
    goodAfternoon: "Dzien dobry",
    goodEvening: "Dobry wieczor",
    officialKicker: "Oficjalny AI smart building",
    officialTitle: "KNX + AI brain, rozwiazania i produkty",
    officialSubtitle: "Otworz mobilna strone",
    postButton: "+ Dodaj zapytanie",
    forgeKicker: "AI Project Forge",
    forgeTitle: "Niech AI zbuduje liste zakupowa",
    requests: "Zapytania",
    active: "Aktywne",
    orders: "Zamowienia",
    budget: "Budzet",
    orderPrefix: "Zamowienie",
  },
};

const homeCopy = computed(() => copyByLocale[locale.value] || copyByLocale.en);

useHead(() => ({ title: homeCopy.value.pageTitle }));

function localizedPath(path: string) {
  const prefix =
    getLocalePrefixFromPath(route.path) ||
    (import.meta.client ? localStorage.getItem("h5_locale_prefix") || "" : "");
  return prefix ? withLocalePrefix(path, prefix) : path;
}

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return homeCopy.value.goodMorning;
  if (h < 17) return homeCopy.value.goodAfternoon;
  return homeCopy.value.goodEvening;
});

const initial = computed(() => authStore.displayName.charAt(0).toUpperCase());

const activeIntents = computed(() =>
  intentStore.intents.filter((i) => ["ACTIVE", "AWARDED"].includes(i.status))
);

const stats = computed(() => [
  { label: homeCopy.value.requests, value: intentStore.intents.length },
  { label: homeCopy.value.active, value: activeIntents.value.length },
  { label: homeCopy.value.orders, value: orderStore.orders.length },
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

function formatDeposit(minor: number, currency = "EUR") {
  return formatPrice(minor, currency);
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
