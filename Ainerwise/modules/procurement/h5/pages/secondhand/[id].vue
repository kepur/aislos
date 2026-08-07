<template>
  <div class="min-h-screen bg-slate-50 pb-28">
    <header class="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-slate-100 bg-white/95 px-4 pt-safe backdrop-blur">
      <NuxtLink :to="localizedPath('/secondhand')" class="text-sm font-bold text-emerald-700">
        {{ t("common.back") }}
      </NuxtLink>
      <h1 class="truncate text-base font-extrabold text-slate-900">2Hands</h1>
    </header>

    <main class="px-4 py-4">
      <div v-if="loading" class="space-y-4">
        <div class="aspect-square animate-pulse rounded-3xl bg-slate-100"></div>
        <div class="h-6 w-3/4 animate-pulse rounded bg-slate-100"></div>
        <div class="h-20 animate-pulse rounded-3xl bg-slate-100"></div>
      </div>

      <div v-else-if="error" class="rounded-3xl border border-red-100 bg-red-50 p-5 text-center">
        <p class="text-sm font-bold text-red-700">{{ error }}</p>
        <button type="button" class="mt-4 rounded-2xl bg-red-600 px-4 py-2 text-xs font-bold text-white" @click="loadItem">
          {{ t("common.retry") }}
        </button>
      </div>

      <article v-else-if="item" class="space-y-4">
        <div class="overflow-hidden rounded-3xl bg-white shadow-card">
          <div class="aspect-square bg-slate-100">
            <img v-if="item.images?.[0]" :src="item.images[0]" :alt="item.title" class="h-full w-full object-cover" />
            <div v-else class="flex h-full w-full items-center justify-center bg-gradient-to-br from-emerald-50 to-slate-100 text-lg font-extrabold text-emerald-700">
              2Hands
            </div>
          </div>
          <div class="p-4">
            <div class="mb-2 flex flex-wrap gap-2">
              <span class="rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-bold text-emerald-700">{{ originLabel(item.listing_origin) }}</span>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold text-slate-600">{{ t("secondhand.condition") }} {{ item.condition_grade }}</span>
            </div>
            <h2 class="text-xl font-extrabold leading-snug text-slate-900">{{ item.title }}</h2>
            <p class="mt-2 text-2xl font-extrabold text-slate-950">{{ formatMoneyMinor(item.price_minor, item.currency) }}</p>
          </div>
        </div>

        <section class="rounded-3xl bg-white p-4 shadow-card">
          <h3 class="text-sm font-bold text-slate-900">{{ t("secondhand.warranty") }}</h3>
          <p class="mt-2 text-sm text-slate-600">
            <span v-if="item.warranty_left_months">{{ item.warranty_left_months }} months left</span>
            <span v-else>{{ t("secondhand.no_warranty") }}</span>
          </p>
          <p v-if="item.warranty_required && !item.warranty_left_months" class="mt-2 text-xs font-semibold text-red-600">
            Enterprise recycled listings must carry warranty information.
          </p>
        </section>

        <section class="rounded-3xl bg-white p-4 shadow-card">
          <h3 class="text-sm font-bold text-slate-900">{{ t("secondhand.pickup") }}</h3>
          <p class="mt-2 text-sm text-slate-600">
            {{ [item.pickup_area, item.pickup_city, item.pickup_country].filter(Boolean).join(", ") || "Pickup area not published" }}
          </p>
          <p class="mt-2 text-xs leading-5 text-slate-400">
            Exact address and phone are released only after the seller approves your request.
          </p>
        </section>

        <section class="rounded-3xl bg-white p-4 shadow-card">
          <h3 class="text-sm font-bold text-slate-900">Description</h3>
          <p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">{{ item.description || "No description." }}</p>
        </section>

        <button
          type="button"
          class="fixed bottom-16 left-4 right-4 z-40 rounded-2xl bg-emerald-600 py-3.5 text-sm font-extrabold text-white shadow-lg disabled:opacity-60"
          :disabled="requesting"
          @click="requestContact"
        >
          {{ requesting ? t("common.loading") : contactCta }}
        </button>
      </article>
    </main>

    <MarketBottomBar />
  </div>
</template>

<script setup lang="ts">
import { showToast } from "vant";
import { useI18n } from "vue-i18n";
import { formatMoneyMinor } from "~/utils/currencyPolicy";
import { getLocalePrefixFromPath, withLocalePrefix } from "~/utils/localeRoutes";

definePageMeta({ layout: "default" });
useHead({ title: "2Hands Item" });

type SecondhandDetail = {
  id: string;
  title: string;
  description?: string | null;
  images: string[];
  price_minor: number;
  currency: string;
  listing_origin: string;
  condition_grade: string;
  warranty_left_months?: number | null;
  warranty_required?: boolean;
  pickup_country?: string | null;
  pickup_city?: string | null;
  pickup_area?: string | null;
};

const route = useRoute();
const router = useRouter();
const config = useRuntimeConfig();
const authStore = useAuthStore();
const { t } = useI18n({ useScope: "global" });

const item = ref<SecondhandDetail | null>(null);
const loading = ref(true);
const requesting = ref(false);
const error = ref("");

const itemId = computed(() => String(route.params.id || ""));
const contactCta = computed(() => authStore.isLoggedIn ? "Request pickup details" : t("auth.sign_in"));

function localizedPath(path: string) {
  if (!import.meta.client) return path;
  const prefix = getLocalePrefixFromPath(route.path) || localStorage.getItem("h5_locale_prefix") || "";
  return prefix ? withLocalePrefix(path, prefix) : path;
}

function originLabel(origin?: string) {
  if (origin === "enterprise_recycled" || origin === "enterprise_refurbished") return t("secondhand.enterprise");
  return t("secondhand.personal");
}

async function loadItem() {
  loading.value = true;
  error.value = "";
  try {
    item.value = await $fetch<SecondhandDetail>(`${config.public.apiBase}/secondhand/listings/${itemId.value}`);
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || "Second-hand listing could not be loaded.";
  } finally {
    loading.value = false;
  }
}

async function requestContact() {
  if (!authStore.isLoggedIn) {
    router.push(localizedPath(`/auth/login?return_url=${encodeURIComponent(route.fullPath)}`));
    return;
  }
  requesting.value = true;
  try {
    await $fetch(`${config.public.apiBase}/secondhand/listings/${itemId.value}/disclosure-request`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
      body: { message: "Buyer requested pickup/contact details from AinerWise Market H5." },
    });
    showToast({ type: "success", message: "Request sent to seller." });
  } catch (e: any) {
    showToast({ type: "fail", message: e?.data?.detail || "Request failed" });
  } finally {
    requesting.value = false;
  }
}

onMounted(() => {
  void loadItem();
});
</script>
