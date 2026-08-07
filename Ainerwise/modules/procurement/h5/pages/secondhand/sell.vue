<template>
  <div class="min-h-screen bg-slate-50 pb-10">
    <header class="sticky top-0 z-40 flex h-14 items-center gap-3 border-b border-slate-100 bg-white/95 px-4 pt-safe backdrop-blur">
      <NuxtLink :to="localizedPath('/marketplace/sell')" class="text-sm font-bold text-emerald-700">
        {{ t("common.back") }}
      </NuxtLink>
      <h1 class="truncate text-base font-extrabold text-slate-900">{{ t("secondhand.sell") }}</h1>
    </header>

    <form class="space-y-4 px-4 py-4" @submit.prevent="submit">
      <section class="rounded-3xl bg-white p-4 shadow-card">
        <p class="text-xs font-bold uppercase tracking-[0.2em] text-emerald-600">{{ t("market.surface_secondhand") }}</p>
        <h2 class="mt-1 text-xl font-extrabold text-slate-900">{{ t("market.list_item") }}</h2>
        <p class="mt-2 text-xs leading-5 text-slate-500">
          Personal used items can be sold without warranty. Enterprise recycled or refurbished items must include warranty information.
        </p>
      </section>

      <section class="rounded-3xl bg-white p-4 shadow-card">
        <label class="mb-2 block text-sm font-bold text-slate-800">Listing type</label>
        <div class="grid grid-cols-2 gap-2">
          <button
            v-for="option in originOptions"
            :key="option.value"
            type="button"
            class="rounded-2xl border px-3 py-3 text-left text-xs font-bold"
            :class="form.listing_origin === option.value ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-slate-200 text-slate-500'"
            @click="form.listing_origin = option.value"
          >
            {{ option.label }}
          </button>
        </div>
      </section>

      <section class="space-y-3 rounded-3xl bg-white p-4 shadow-card">
        <div>
          <label class="mb-1 block text-sm font-bold text-slate-700">Title</label>
          <input v-model="form.title" class="input-field" required maxlength="255" placeholder="Used smart lock, inverter, CCTV kit..." />
        </div>
        <div>
          <label class="mb-1 block text-sm font-bold text-slate-700">Description</label>
          <textarea v-model="form.description" class="input-field resize-none" rows="3" placeholder="Condition, included parts, reason for selling..."></textarea>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-sm font-bold text-slate-700">Price</label>
            <input v-model.number="priceInput" class="input-field" type="number" min="0" step="0.01" required />
          </div>
          <div>
            <label class="mb-1 block text-sm font-bold text-slate-700">Currency</label>
            <select v-model="form.currency" class="input-field bg-white">
              <option v-for="currency in appStore.currencyOptions" :key="currency.code" :value="currency.code">{{ currency.code }}</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-sm font-bold text-slate-700">{{ t("secondhand.condition") }}</label>
            <select v-model="form.condition_grade" class="input-field bg-white">
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
              <option value="D">D</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-sm font-bold text-slate-700">{{ t("secondhand.warranty") }}</label>
            <input v-model.number="form.warranty_left_months" class="input-field" type="number" min="0" placeholder="Months" />
          </div>
        </div>
      </section>

      <section class="space-y-3 rounded-3xl bg-white p-4 shadow-card">
        <h3 class="text-sm font-extrabold text-slate-900">{{ t("secondhand.pickup") }}</h3>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-xs font-bold text-slate-600">Country</label>
            <select v-model="form.pickup_country" class="input-field bg-white">
              <option v-for="region in appStore.regionOptions" :key="region.code" :value="region.code">{{ region.label }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-bold text-slate-600">City</label>
            <input v-model="form.pickup_city" class="input-field" placeholder="Belgrade" />
          </div>
        </div>
        <input v-model="form.pickup_area" class="input-field" placeholder="Area, mall, district..." />
        <input v-model="form.contact_phone" class="input-field" placeholder="Phone kept private until disclosure" />
      </section>

      <section class="space-y-3 rounded-3xl bg-white p-4 shadow-card">
        <label class="block text-sm font-bold text-slate-700">Image URLs</label>
        <div v-for="(_image, index) in imageInputs" :key="index" class="flex gap-2">
          <input v-model="imageInputs[index]" class="input-field" type="url" placeholder="https://..." />
          <button type="button" class="rounded-xl border border-slate-200 px-3 text-xs font-bold text-slate-500" @click="imageInputs.splice(index, 1)">Remove</button>
        </div>
        <button type="button" class="rounded-xl bg-slate-100 px-3 py-2 text-xs font-bold text-slate-600" @click="imageInputs.push('')">
          Add image URL
        </button>
      </section>

      <button type="submit" class="btn-primary py-3.5" :disabled="saving">
        {{ saving ? t("common.loading") : t("common.submit") }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { showToast } from "vant";
import { useI18n } from "vue-i18n";
import { getLocalePrefixFromPath, withLocalePrefix } from "~/utils/localeRoutes";

definePageMeta({ layout: "default" });
useHead({ title: "List used item" });

const route = useRoute();
const router = useRouter();
const config = useRuntimeConfig();
const authStore = useAuthStore();
const appStore = useAppStore();
const { t } = useI18n({ useScope: "global" });

const priceInput = ref(0);
const saving = ref(false);
const imageInputs = ref<string[]>([""]);

const form = reactive({
  title: "",
  description: "",
  price_minor: 0,
  currency: appStore.currency || "EUR",
  condition_grade: "B",
  warranty_left_months: null as number | null,
  listing_origin: "personal_secondhand",
  fulfillment_mode: "SELLER_PICKUP",
  pickup_country: appStore.regionCountry || "RS",
  pickup_city: "",
  pickup_area: "",
  contact_phone: "",
});

const originOptions = computed(() => [
  { value: "personal_secondhand", label: t("secondhand.personal") },
  { value: "enterprise_recycled", label: t("secondhand.enterprise") },
]);

function localizedPath(path: string) {
  if (!import.meta.client) return path;
  const prefix = getLocalePrefixFromPath(route.path) || localStorage.getItem("h5_locale_prefix") || "";
  return prefix ? withLocalePrefix(path, prefix) : path;
}

async function submit() {
  if (!authStore.isLoggedIn) {
    router.push(localizedPath(`/auth/login?return_url=${encodeURIComponent(route.fullPath)}`));
    return;
  }
  form.price_minor = Math.round(Number(priceInput.value || 0) * 100);
  if (form.listing_origin.startsWith("enterprise_") && !form.warranty_left_months) {
    showToast({ type: "fail", message: "Enterprise recycled items need warranty months." });
    return;
  }
  saving.value = true;
  try {
    const created = await $fetch<any>(`${config.public.apiBase}/secondhand/listings`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
      body: {
        ...form,
        images: imageInputs.value.map((item) => item.trim()).filter(Boolean),
      },
    });
    showToast({ type: "success", message: "Listing published." });
    router.push(localizedPath(`/secondhand/${created.id}`));
  } catch (e: any) {
    showToast({ type: "fail", message: e?.data?.detail || "Publish failed" });
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  appStore.hydrate();
  await appStore.fetchMarketLocalizationConfig();
  await appStore.fetchPaymentRegionConfig(appStore.regionCountry || "RS");
  const requestedOrigin = String(route.query.listing_origin || "");
  if (["personal_secondhand", "enterprise_recycled"].includes(requestedOrigin)) form.listing_origin = requestedOrigin;
  form.currency = appStore.currency;
  form.pickup_country = appStore.regionCountry;
});
</script>
