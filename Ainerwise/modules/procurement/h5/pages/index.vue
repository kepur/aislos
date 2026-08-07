<template>
  <div class="min-h-screen bg-slate-50 pb-20">
    <header class="sticky top-0 z-50 border-b border-slate-100 bg-white/95 backdrop-blur">
      <div class="flex h-14 items-center justify-between px-4 pt-safe">
        <div class="flex min-w-0 items-center gap-2">
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600">
            <span class="text-sm font-bold text-white">AW</span>
          </div>
          <span class="truncate text-lg font-bold text-primary-900">{{ appName }}</span>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600">
            {{ selectedRegion?.label || heroForm.country }}
          </button>
          <NuxtLink :to="localizedPath('/auth/login')">
            <button type="button" class="rounded-lg border border-primary-200 px-3 py-1.5 text-sm font-semibold text-primary-600 active:bg-primary-50">
              Sign in
            </button>
          </NuxtLink>
        </div>
      </div>
    </header>

    <section class="relative overflow-hidden bg-gradient-to-br from-primary-950 via-primary-900 to-primary-700 px-4 pb-8 pt-8 text-white">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute -right-24 -top-20 h-64 w-64 rounded-full bg-white"></div>
        <div class="absolute -bottom-20 -left-20 h-56 w-56 rounded-full bg-emerald-300"></div>
      </div>

      <div class="relative">
        <div class="mb-4 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1.5 text-xs font-semibold text-white/90">
          {{ homeCopy.badge }}
        </div>
        <h1 class="mb-3 text-3xl font-extrabold leading-tight">
          {{ homeCopy.title }}
        </h1>
        <p class="mb-6 text-sm leading-6 text-primary-100">
          {{ homeCopy.subtitle }}
        </p>

        <div class="mb-4 grid grid-cols-2 gap-2">
          <NuxtLink :to="localizedPath('/marketplace')" class="rounded-2xl border border-white/15 bg-white/15 px-3 py-3 text-center text-xs font-bold text-white backdrop-blur active:bg-white/25">
            {{ homeCopy.market }}
          </NuxtLink>
          <NuxtLink :to="localizedPath('/buyer/post-request')" class="rounded-2xl border border-white/15 bg-white/10 px-3 py-3 text-center text-xs font-bold text-white/90 backdrop-blur active:bg-white/20">
            {{ homeCopy.request }}
          </NuxtLink>
        </div>

        <NuxtLink
          :to="localizedPath('/buyer/post-request')"
          class="mb-4 block rounded-3xl border border-cyan-200/30 bg-cyan-300/15 p-4 text-white shadow-lg shadow-black/10 backdrop-blur active:bg-cyan-300/25"
        >
          <div class="flex items-center justify-between gap-4">
            <div>
              <p class="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-100">
                {{ homeCopy.aiKicker }}
              </p>
              <h2 class="mt-1 text-lg font-extrabold leading-tight">
                {{ homeCopy.aiTitle }}
              </h2>
              <p class="mt-1 text-xs leading-5 text-primary-100">
                {{ homeCopy.aiSubtitle }}
              </p>
            </div>
            <span class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-white text-xl font-black text-primary-700">→</span>
          </div>
        </NuxtLink>

        <form class="space-y-4 rounded-3xl bg-white p-4 text-slate-900 shadow-2xl" @submit.prevent="handleSearch">
          <div>
            <label class="mb-1.5 block text-sm font-semibold text-slate-700">{{ homeCopy.categoryLabel }}</label>
            <select v-model="heroForm.category" class="input-field bg-white">
              <option value="">{{ homeCopy.selectCategory }}</option>
              <option v-for="cat in categoryOptions" :key="cat.value" :value="cat.value">
                {{ cat.name }}{{ cat.item_count ? ` (${cat.item_count})` : "" }}
              </option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1.5 block text-sm font-semibold text-slate-700">{{ homeCopy.minBudget }}</label>
              <div class="relative">
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">{{ budgetCurrencySymbol }}</span>
                <input v-model="heroForm.budgetMin" type="number" min="0" placeholder="0" class="input-field pl-8" />
              </div>
            </div>
            <div>
              <label class="mb-1.5 block text-sm font-semibold text-slate-700">{{ homeCopy.maxBudget }}</label>
              <div class="relative">
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">{{ budgetCurrencySymbol }}</span>
                <input v-model="heroForm.budgetMax" type="number" min="0" :placeholder="homeCopy.maxPlaceholder" class="input-field pl-8" />
              </div>
            </div>
          </div>

          <div>
            <label class="mb-1.5 block text-sm font-semibold text-slate-700">{{ homeCopy.deliveryCountry }}</label>
            <select v-model="heroForm.country" class="input-field bg-white">
              <option v-for="region in regionOptions" :key="region.code" :value="region.code">
                {{ region.label }} ({{ region.code }})
              </option>
            </select>
            <p class="mt-1 text-xs text-slate-500">
              {{ homeCopy.settlement }}: {{ budgetCurrencyLabel }}. {{ homeCopy.localReference }}: {{ appStore.localCurrency }}.
            </p>
          </div>

          <div>
            <div class="mb-1.5 flex items-center justify-between gap-3">
              <label class="block text-sm font-semibold text-slate-700">{{ homeCopy.deliveryLocation }}</label>
              <button
                type="button"
                class="rounded-full border border-primary-100 bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700 disabled:opacity-60"
                :disabled="locationStatus === 'loading'"
                @click="detectBrowserLocation"
              >
                {{ locationStatus === "loading" ? homeCopy.detecting : homeCopy.useCurrent }}
              </button>
            </div>
            <input v-model="heroForm.location" type="text" :placeholder="homeCopy.locationPlaceholder" class="input-field" />
            <p v-if="locationMessage" class="mt-1 text-xs" :class="locationStatus === 'error' ? 'text-amber-600' : 'text-slate-500'">
              {{ locationMessage }}
            </p>
          </div>

          <div>
            <div class="mb-1.5 flex items-center justify-between">
              <label class="block text-sm font-semibold text-slate-700">{{ homeCopy.searchRadius }}</label>
              <span class="text-sm font-bold text-primary-600">{{ heroForm.radius }} km</span>
            </div>
            <input v-model="heroForm.radius" type="range" min="1" max="200" step="1" class="w-full accent-primary-600" />
            <div class="mt-1 flex justify-between text-xs text-slate-400">
              <span>1 km</span>
              <span>200 km</span>
            </div>
          </div>

          <button type="submit" class="btn-primary py-3.5 text-sm">
            {{ homeCopy.findSuppliers }}
          </button>
          <NuxtLink :to="localizedPath('/buyer/post-request')" class="block rounded-xl border border-slate-200 py-3 text-center text-sm font-semibold text-slate-700 active:bg-slate-50">
            {{ homeCopy.postDetailed }}
          </NuxtLink>
        </form>
      </div>
    </section>

    <section class="px-4 py-8">
      <h2 class="mb-1 text-xl font-bold text-slate-900">{{ homeCopy.worksTitle }}</h2>
      <p class="mb-6 text-sm text-slate-500">{{ homeCopy.worksSubtitle }}</p>

      <div class="space-y-4">
        <div v-for="stepItem in steps" :key="stepItem.num" class="flex gap-4 rounded-2xl bg-white p-4 shadow-card">
          <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full text-sm font-bold" :class="stepItem.color">
            {{ stepItem.num }}
          </div>
          <div>
            <h3 class="text-sm font-semibold text-slate-800">{{ stepItem.title }}</h3>
            <p class="mt-0.5 text-xs leading-relaxed text-slate-500">{{ stepItem.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="mx-4 mb-8 rounded-2xl border border-green-100 bg-gradient-to-br from-green-50 to-emerald-50 p-5">
      <h3 class="mb-2 text-sm font-bold text-green-900">{{ homeCopy.safeTitle }}</h3>
      <p class="text-xs leading-relaxed text-green-700">
        {{ homeCopy.safeText }}
      </p>
    </section>

    <MarketBottomBar />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { currencyMeta, currencyOptionLabel } from "~/utils/currencyPolicy";
import { inferLocationFromCoords, inferLocationFromTimezone, type LocationGuess } from "~/utils/geoPolicy";
import { useI18n } from "vue-i18n";
import { getLocalePrefixFromPath, withLocalePrefix } from "~/utils/localeRoutes";

definePageMeta({ layout: "default", middleware: [] });
useHead({ title: "AinerWise Market H5" });

type QuickCategory = {
  id?: string;
  name: string;
  value: string;
  item_count?: number;
};

const router = useRouter();
const route = useRoute();
const config = useRuntimeConfig();
const appStore = useAppStore();
const { locale } = useI18n({ useScope: "global" });
const appName = computed(() => String(config.public.appName || "AinerWise Market"));

const copyByLocale: Record<string, Record<string, string>> = {
  en: {
    badge: "AI market assistant",
    title: "AinerWise Market: buy products, source smart, save with new or used options.",
    subtitle: "Browse official recommendations, market products, enterprise recycled stock and personal second-hand offers in one place. Complex needs can still become AI procurement requests.",
    market: "Market",
    request: "AI Request",
    aiKicker: "AI project analysis",
    aiTitle: "Describe one project. AI turns it into categories, products and supplier RFQs.",
    aiSubtitle: "For villas, hotels, energy, security and smart building work that cannot be solved by one product.",
    categoriesTitle: "Popular categories",
    allCategories: "All",
    categoryLabel: "Category",
    selectCategory: "Select category",
    minBudget: "Min Budget",
    maxBudget: "Max Budget",
    maxPlaceholder: "Max",
    deliveryCountry: "Delivery Country",
    settlement: "Settlement",
    localReference: "Local reference",
    deliveryLocation: "Delivery Location",
    locationPlaceholder: "Enter city or area",
    useCurrent: "Use current",
    detecting: "Detecting...",
    searchRadius: "Search Radius",
    findSuppliers: "Find Suppliers",
    postDetailed: "Post a detailed request",
    worksTitle: "How AinerWise Market works",
    worksSubtitle: "Shop, compare, ask suppliers, or publish a structured request when the job is bigger.",
    safeTitle: "One market, shared Core data",
    safeText: "Official products, supplier listings, used offers, quotes and orders all feed the same AinerWise Core for analytics and follow-up.",
  },
  zh: {
    badge: "AI 市场助手",
    title: "AinerWise Market：买产品、AI 找货，新旧都能省。",
    subtitle: "官网推荐、市场商品、企业回收再售和个人二手都在同一个市场里。复杂需求仍可一键进入 AI 采购需求流程。",
    market: "市场商品",
    request: "AI 需求",
    aiKicker: "AI 项目分析",
    aiTitle: "一句话描述项目，AI 帮你拆分类、商品和供应商询价。",
    aiSubtitle: "别墅、酒店、能源、安防、智能建筑等复杂需求，不再只靠搜索单个商品。",
    categoriesTitle: "热门分类",
    allCategories: "全部分类",
    categoryLabel: "分类",
    selectCategory: "选择分类",
    minBudget: "最低预算",
    maxBudget: "最高预算",
    maxPlaceholder: "最高",
    deliveryCountry: "交付国家",
    settlement: "结算货币",
    localReference: "本地参考",
    deliveryLocation: "交付位置",
    locationPlaceholder: "输入城市或区域",
    useCurrent: "使用当前位置",
    detecting: "定位中...",
    searchRadius: "搜索半径",
    findSuppliers: "查找供应商",
    postDetailed: "发布 AI 项目需求",
    worksTitle: "AinerWise Market 如何工作",
    worksSubtitle: "可直接逛商品、比较供应商、询价；复杂项目发布结构化需求。",
    safeTitle: "独立市场，共用 Core 数据",
    safeText: "官网商品、供应商上架、二手商品、报价和订单都进入同一个 AinerWise Core，便于后台分析和后续服务。",
  },
  sr: {
    badge: "AI market asistent",
    title: "AinerWise Market: novi i polovni proizvodi uz AI nabavku.",
    subtitle: "Pregledajte preporučene proizvode, tržišne ponude, obnovljenu opremu i polovne artikle. Složen zahtev može postati AI nabavka.",
    market: "Market",
    request: "AI zahtev",
    aiKicker: "AI analiza projekta",
    aiTitle: "Opisite projekat. AI ga pretvara u kategorije, proizvode i RFQ.",
    aiSubtitle: "Za vile, hotele, energiju, bezbednost i pametne zgrade kada jedan proizvod nije dovoljan.",
    categoriesTitle: "Popularne kategorije",
    allCategories: "Sve",
    categoryLabel: "Kategorija",
    selectCategory: "Izaberite kategoriju",
    minBudget: "Min budzet",
    maxBudget: "Max budzet",
    maxPlaceholder: "Max",
    deliveryCountry: "Drzava isporuke",
    settlement: "Obracun",
    localReference: "Lokalna referenca",
    deliveryLocation: "Lokacija isporuke",
    locationPlaceholder: "Unesite grad ili zonu",
    useCurrent: "Trenutna",
    detecting: "Lociranje...",
    searchRadius: "Radius pretrage",
    findSuppliers: "Pronadji dobavljace",
    postDetailed: "Objavi AI zahtev",
    worksTitle: "Kako radi AinerWise Market",
    worksSubtitle: "Kupujte, poredite, tražite ponude ili objavite strukturisan zahtev.",
    safeTitle: "Jedan market, zajednički Core",
    safeText: "Novi i polovni proizvodi, upiti i narudžbine ostaju u istom AinerWise Core sistemu.",
  },
  pl: {
    badge: "Asystent AI marketu",
    title: "AinerWise Market: nowe i używane produkty z zakupami AI.",
    subtitle: "Przeglądaj rekomendacje, oferty rynku, sprzęt odnowiony i prywatne używane przedmioty. Większe potrzeby zamienisz w zapytanie AI.",
    market: "Market",
    request: "Zapytanie AI",
    aiKicker: "Analiza projektu AI",
    aiTitle: "Opisz projekt. AI zamieni go w kategorie, produkty i zapytania RFQ.",
    aiSubtitle: "Dla willi, hoteli, energii, bezpieczeństwa i smart building, gdy jeden produkt nie wystarcza.",
    categoriesTitle: "Popularne kategorie",
    allCategories: "Wszystkie",
    categoryLabel: "Kategoria",
    selectCategory: "Wybierz kategorię",
    minBudget: "Budżet min.",
    maxBudget: "Budżet max.",
    maxPlaceholder: "Max",
    deliveryCountry: "Kraj dostawy",
    settlement: "Rozliczenie",
    localReference: "Lokalnie",
    deliveryLocation: "Miejsce dostawy",
    locationPlaceholder: "Wpisz miasto lub obszar",
    useCurrent: "Użyj lokalizacji",
    detecting: "Wykrywanie...",
    searchRadius: "Promień",
    findSuppliers: "Znajdź dostawców",
    postDetailed: "Opublikuj zapytanie AI",
    worksTitle: "Jak działa AinerWise Market",
    worksSubtitle: "Kupuj, porównuj, pytaj dostawców albo opublikuj uporządkowane zapytanie.",
    safeTitle: "Jeden market, wspólne dane Core",
    safeText: "Nowe i używane produkty, zapytania i zamówienia trafiają do wspólnego AinerWise Core.",
  },
};

const homeCopy = computed(() => copyByLocale[locale.value] || copyByLocale.en);

const fallbackCategoriesByLocale: Record<string, string[]> = {
  en: ["Construction Materials", "IT / Electronics", "Energy / Solar", "Security", "Smart Living"],
  zh: ["建材施工", "IT / 电子", "能源 / 光伏", "安防监控", "智能家居"],
  sr: ["Gradjevinski materijal", "IT / Elektronika", "Energija / Solar", "Bezbednost", "Pametan dom"],
  pl: ["Materiały budowlane", "IT / Elektronika", "Energia / Solar", "Bezpieczeństwo", "Smart Living"],
};

const loadedCategories = ref<QuickCategory[]>([]);
const locationStatus = ref<"idle" | "loading" | "success" | "error">("idle");
const locationMessage = ref("");

const heroForm = reactive({
  category: "",
  budgetMin: "",
  budgetMax: "",
  location: "",
  country: "RS",
  radius: 25,
  latitude: null as number | null,
  longitude: null as number | null,
});

const fallbackCategories = computed<QuickCategory[]>(() => {
  const names = fallbackCategoriesByLocale[locale.value] || fallbackCategoriesByLocale.en;
  return names.map((name) => ({ name, value: `name:${name}` }));
});
const categoryOptions = computed(() => loadedCategories.value.length ? loadedCategories.value : fallbackCategories.value);
const regionOptions = computed(() => appStore.regionOptions.map((region) => ({
  code: String(region.code || "").toUpperCase().slice(0, 2),
  label: region.label || region.code,
})));
const selectedCategory = computed(() => categoryOptions.value.find((cat) => cat.value === heroForm.category) || null);
const selectedRegion = computed(() => regionOptions.value.find((region) => region.code === heroForm.country) || null);
const budgetCurrencySymbol = computed(() => currencyMeta(appStore.currency).symbol || appStore.currency);
const budgetCurrencyLabel = computed(() => currencyOptionLabel(appStore.currency));

const steps = computed(() => [
  { num: 1, title: homeCopy.value.categoryLabel, desc: homeCopy.value.worksSubtitle, color: "bg-primary-100 text-primary-700" },
  { num: 2, title: homeCopy.value.findSuppliers, desc: homeCopy.value.aiSubtitle, color: "bg-amber-100 text-amber-700" },
  { num: 3, title: homeCopy.value.postDetailed, desc: homeCopy.value.safeText, color: "bg-green-100 text-green-700" },
]);

watch(regionOptions, (options) => {
  if (!options.length) return;
  if (!options.some((region) => region.code === heroForm.country)) heroForm.country = options[0].code;
}, { immediate: true });

watch(() => appStore.regionCountry, (country) => {
  const normalized = String(country || "").toUpperCase().slice(0, 2);
  if (normalized && normalized !== heroForm.country) heroForm.country = normalized;
}, { immediate: true });

watch(() => heroForm.country, async (country) => {
  const normalized = String(country || "").toUpperCase().slice(0, 2);
  if (normalized && normalized !== appStore.regionCountry) await appStore.setRegionCountry(normalized);
});

onMounted(async () => {
  await appStore.fetchMarketLocalizationConfig();
  await appStore.fetchPaymentRegionConfig(appStore.regionCountry || heroForm.country || "RS");
  await loadCategoryOptions();
  applyTimezoneDefault();
});

async function loadCategoryOptions() {
  try {
    const filters = await $fetch<any>(`${config.public.apiBase}/marketplace/filters`);
    const categories = Array.isArray(filters?.categories) ? filters.categories : [];
    loadedCategories.value = categories
      .map((cat: any) => ({
        id: cat.id ? String(cat.id) : "",
        name: String(cat.name || cat.slug || "").trim(),
        value: cat.id ? String(cat.id) : `name:${String(cat.name || cat.slug || "").trim()}`,
        item_count: Number(cat.item_count || 0),
      }))
      .filter((cat: QuickCategory) => cat.name && cat.value);
  } catch {
    loadedCategories.value = [];
  }
}

function localizedPath(path: string) {
  const prefix = getLocalePrefixFromPath(route.path) || (import.meta.client ? localStorage.getItem("h5_locale_prefix") || "" : "");
  return prefix ? withLocalePrefix(path, prefix) : path;
}

function applyTimezoneDefault() {
  if (!import.meta.client) return;
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const guess = inferLocationFromTimezone(timeZone, regionOptions.value);
  if (guess) applyLocationGuess(guess, false);
}

function detectBrowserLocation() {
  if (!import.meta.client || !navigator.geolocation) {
    locationStatus.value = "error";
    locationMessage.value = "Browser location is not available. Choose country and city manually.";
    return;
  }

  locationStatus.value = "loading";
  locationMessage.value = "";
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const latitude = position.coords.latitude;
      const longitude = position.coords.longitude;
      heroForm.latitude = latitude;
      heroForm.longitude = longitude;
      const guess = inferLocationFromCoords(latitude, longitude, regionOptions.value);
      if (guess) {
        applyLocationGuess(guess, true);
        locationStatus.value = "success";
        locationMessage.value = `Detected ${guess.city || guess.countryName}. You can edit it before searching.`;
        return;
      }
      const fallbackGuess = inferLocationFromTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone, regionOptions.value);
      if (fallbackGuess) {
        applyLocationGuess(fallbackGuess, false);
        locationStatus.value = "success";
        locationMessage.value = "Country inferred from browser timezone. Please confirm the city.";
        return;
      }
      locationStatus.value = "error";
      locationMessage.value = "Coordinates are outside the currently open countries. Select a country manually.";
    },
    () => {
      locationStatus.value = "error";
      locationMessage.value = "Location permission was denied or timed out. Manual country and city still work.";
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
  );
}

function applyLocationGuess(guess: LocationGuess, overwriteCity: boolean) {
  if (guess.countryCode) heroForm.country = guess.countryCode;
  if (guess.city && (overwriteCity || !heroForm.location.trim())) heroForm.location = guess.city;
}

function handleSearch() {
  const q = new URLSearchParams();
  if (selectedCategory.value?.id) q.set("category_id", selectedCategory.value.id);
  if (selectedCategory.value?.name) q.set("category_name", selectedCategory.value.name);
  if (selectedCategory.value?.name && !selectedCategory.value?.id) q.set("keyword", selectedCategory.value.name);
  if (heroForm.budgetMin) q.set("budget_min_minor", String(Math.round(Number(heroForm.budgetMin) * 100)));
  if (heroForm.budgetMax) q.set("budget_max_minor", String(Math.round(Number(heroForm.budgetMax) * 100)));
  if (heroForm.budgetMin || heroForm.budgetMax) q.set("budget_currency", appStore.currency);
  if (heroForm.country) {
    q.set("country", heroForm.country);
    q.set("delivery_country", heroForm.country);
    if (selectedRegion.value?.label) q.set("delivery_country_name", selectedRegion.value.label);
  }
  if (heroForm.location.trim()) {
    q.set("city", heroForm.location.trim());
    q.set("delivery_city", heroForm.location.trim());
  }
  if (heroForm.radius !== 25) q.set("radius_km", String(heroForm.radius));
  if (heroForm.latitude != null && heroForm.longitude != null) {
    q.set("lat", String(heroForm.latitude));
    q.set("lng", String(heroForm.longitude));
  }
  const target = q.toString() ? `/marketplace?${q.toString()}` : "/marketplace";
  router.push(localizedPath(target));
}
</script>
