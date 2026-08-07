<template>
  <div class="min-h-screen bg-slate-50 pb-28">
    <header class="sticky top-0 z-40 border-b border-slate-100 bg-white/95 px-4 py-3 pt-safe backdrop-blur">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="text-[10px] font-bold uppercase tracking-[0.22em] text-emerald-600">AinerWise Market</p>
          <h1 class="text-xl font-extrabold text-slate-900">{{ t("secondhand.title") }}</h1>
        </div>
        <NuxtLink :to="localizedPath('/secondhand/sell')" class="rounded-full bg-emerald-600 px-4 py-2 text-xs font-bold text-white">
          {{ t("secondhand.sell") }}
        </NuxtLink>
      </div>
      <p class="mt-2 text-xs leading-5 text-slate-500">{{ t("secondhand.subtitle") }}</p>

      <div class="mt-3 flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
        <button
          v-for="option in originOptions"
          :key="option.value"
          type="button"
          class="flex-shrink-0 rounded-full border px-3 py-1.5 text-xs font-bold"
          :class="originFilter === option.value ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-500'"
          @click="originFilter = option.value; loadListings(true)"
        >
          {{ option.label }}
        </button>
      </div>

      <div class="mt-3 grid grid-cols-[1fr_110px] gap-2">
        <input
          v-model="keyword"
          type="search"
          :placeholder="t('market.search_placeholder')"
          class="rounded-2xl bg-slate-100 px-4 py-3 text-sm outline-none"
          @keyup.enter="loadListings(true)"
        />
        <select v-model="sort" class="rounded-2xl bg-slate-100 px-3 py-3 text-sm font-semibold text-slate-600 outline-none" @change="loadListings(true)">
          <option value="newest">{{ t("market.sort_new") }}</option>
          <option value="price_asc">{{ t("market.sort_price_asc") }}</option>
          <option value="price_desc">{{ t("market.sort_price_desc") }}</option>
          <option value="condition">{{ t("secondhand.condition") }}</option>
        </select>
      </div>
    </header>

    <main class="px-4 py-4">
      <div v-if="loading && !items.length" class="grid grid-cols-2 gap-3">
        <div v-for="i in 6" :key="i" class="animate-pulse rounded-3xl bg-white p-3">
          <div class="aspect-square rounded-2xl bg-slate-100"></div>
          <div class="mt-3 h-3 w-3/4 rounded bg-slate-100"></div>
          <div class="mt-2 h-3 w-1/2 rounded bg-slate-100"></div>
        </div>
      </div>

      <div v-else-if="error" class="rounded-3xl border border-red-100 bg-red-50 p-5 text-center">
        <p class="text-sm font-bold text-red-700">{{ t("market.could_not_load") }}</p>
        <p class="mt-1 text-xs text-red-500">{{ error }}</p>
        <button type="button" class="mt-4 rounded-2xl bg-red-600 px-4 py-2 text-xs font-bold text-white" @click="loadListings(true)">
          {{ t("common.retry") }}
        </button>
      </div>

      <div v-else-if="!items.length" class="rounded-3xl bg-white p-8 text-center shadow-card">
        <p class="text-sm font-bold text-slate-700">{{ t("secondhand.empty") }}</p>
        <NuxtLink :to="localizedPath('/marketplace')" class="mt-3 inline-flex rounded-full bg-slate-100 px-4 py-2 text-xs font-bold text-slate-600">
          {{ t("nav.market") }}
        </NuxtLink>
      </div>

      <div v-else class="grid grid-cols-2 gap-3">
        <NuxtLink
          v-for="item in items"
          :key="item.id"
          :to="localizedPath(`/secondhand/${item.id}`)"
          class="overflow-hidden rounded-3xl border border-slate-100 bg-white shadow-card active:scale-[0.98]"
        >
          <div class="aspect-square bg-slate-100">
            <img v-if="item.images?.[0]" :src="item.images[0]" :alt="item.title" class="h-full w-full object-cover" />
            <div v-else class="flex h-full w-full items-center justify-center bg-gradient-to-br from-emerald-50 to-slate-100 text-center text-xs font-bold text-emerald-700">
              2Hands
            </div>
          </div>
          <div class="p-3">
            <div class="mb-1 flex flex-wrap gap-1">
              <span class="rounded-full bg-emerald-50 px-2 py-0.5 text-[9px] font-bold text-emerald-700">{{ originLabel(item.listing_origin) }}</span>
              <span v-if="item.warranty_left_months" class="rounded-full bg-blue-50 px-2 py-0.5 text-[9px] font-bold text-blue-700">
                {{ item.warranty_left_months }}m
              </span>
            </div>
            <h2 class="line-clamp-2 text-xs font-bold leading-snug text-slate-900">{{ item.title }}</h2>
            <p class="mt-1 text-[10px] text-slate-400">{{ item.pickup_city || item.pickup_country || t("secondhand.pickup") }}</p>
            <p class="mt-2 text-sm font-extrabold text-slate-900">{{ formatMoneyMinor(item.price_minor, item.currency) }}</p>
          </div>
        </NuxtLink>
      </div>

      <div v-if="hasNext" class="py-6 text-center">
        <button type="button" :disabled="loading" class="rounded-full bg-white px-5 py-2 text-sm font-bold text-emerald-700 shadow-card disabled:opacity-50" @click="loadMore">
          {{ loading ? t("market.loading") : t("market.load_more") }}
        </button>
      </div>
    </main>

    <MarketBottomBar />
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { formatMoneyMinor } from "~/utils/currencyPolicy";
import { getLocalePrefixFromPath, withLocalePrefix } from "~/utils/localeRoutes";

definePageMeta({ layout: "default" });
useHead({ title: "2Hands" });

type SecondhandItem = {
  id: string;
  title: string;
  images: string[];
  price_minor: number;
  currency: string;
  listing_origin: string;
  warranty_left_months?: number | null;
  pickup_country?: string | null;
  pickup_city?: string | null;
};

const config = useRuntimeConfig();
const route = useRoute();
const { t } = useI18n({ useScope: "global" });

const items = ref<SecondhandItem[]>([]);
const page = ref(1);
const total = ref(0);
const hasNext = ref(false);
const loading = ref(false);
const error = ref("");
const keyword = ref("");
const sort = ref("newest");
const originFilter = ref("all");

const originOptions = computed(() => [
  { value: "all", label: t("secondhand.all") },
  { value: "personal_secondhand", label: t("secondhand.personal") },
  { value: "enterprise_recycled", label: t("secondhand.enterprise") },
]);

function localizedPath(path: string) {
  if (!import.meta.client) return path;
  const prefix = getLocalePrefixFromPath(route.path) || localStorage.getItem("h5_locale_prefix") || "";
  return prefix ? withLocalePrefix(path, prefix) : path;
}

function originLabel(origin?: string) {
  if (origin === "enterprise_recycled" || origin === "enterprise_refurbished") return t("secondhand.enterprise");
  return t("secondhand.personal");
}

async function loadListings(reset = false) {
  if (reset) {
    page.value = 1;
    items.value = [];
  }
  loading.value = true;
  error.value = "";
  try {
    const params: Record<string, string | number> = {
      page: page.value,
      page_size: 20,
      sort: sort.value,
    };
    if (keyword.value.trim()) params.keyword = keyword.value.trim();
    if (originFilter.value !== "all") params.listing_origin = originFilter.value;
    const data = await $fetch<any>(`${config.public.apiBase}/secondhand/listings`, { params });
    const loaded = Array.isArray(data?.items) ? data.items : [];
    if (reset) items.value = loaded;
    else items.value.push(...loaded);
    total.value = Number(data?.total || loaded.length);
    hasNext.value = Boolean(data?.has_next);
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || "Second-hand listings request failed.";
  } finally {
    loading.value = false;
  }
}

async function loadMore() {
  page.value += 1;
  await loadListings(false);
}

onMounted(() => {
  void loadListings(true);
});
</script>

<style scoped>
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
