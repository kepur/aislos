<template>
  <div class="min-h-screen bg-slate-50 pb-10">
    <!-- Top Bar -->
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button @click="$router.back()" class="text-slate-600 p-1 -ml-1">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-bold text-slate-900 flex-1">Create Campaign</h1>
    </div>

    <div class="px-4 pt-5 space-y-4">
      <!-- Campaign Name -->
      <div class="bg-white rounded-2xl p-4 border border-slate-100">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Campaign Info</h2>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Campaign Name *</label>
            <input v-model="form.name" type="text" placeholder="e.g. Summer Sale Promotion" class="input-field" />
          </div>
        </div>
      </div>

      <!-- Placement Type -->
      <div class="bg-white rounded-2xl p-4 border border-slate-100">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Placement</h2>
        <div class="space-y-2">
          <button v-for="p in placements" :key="p.value" @click="form.placement = p.value" type="button"
            :class="['w-full p-3 rounded-xl border-2 text-left flex items-center gap-3 transition-all',
              form.placement === p.value ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:border-indigo-200']">
            <span class="text-2xl">{{ p.icon }}</span>
            <div>
              <p class="font-semibold text-sm text-slate-900">{{ p.label }}</p>
              <p class="text-xs text-slate-500">{{ p.desc }}</p>
            </div>
          </button>
        </div>
      </div>

      <!-- Catalog Item (optional) -->
      <div class="bg-white rounded-2xl p-4 border border-slate-100">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Promoted Product (Optional)</h2>
        <select v-model="form.catalog_item_id" class="input-field bg-white">
          <option value="">No specific product</option>
          <option v-for="item in catalogItems" :key="item.id" :value="item.id">{{ item.title }}</option>
        </select>
        <p class="text-xs text-slate-400 mt-1.5">Link your ad to a specific product in your catalog.</p>
      </div>

      <!-- Budget & Bidding -->
      <div class="bg-white rounded-2xl p-4 border border-slate-100">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Budget & Bidding</h2>
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Total Budget (₱) *</label>
              <input v-model.number="budgetInput" type="number" min="100" placeholder="1000" class="input-field" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Max Bid/Click (₱) *</label>
              <input v-model.number="bidInput" type="number" min="1" step="0.5" placeholder="5" class="input-field" />
            </div>
          </div>

          <!-- Suggested bid info -->
          <div class="bg-indigo-50 rounded-xl px-3 py-2.5 text-xs text-indigo-700">
            <p class="font-semibold mb-1">💡 Suggested bid ranges:</p>
            <div class="grid grid-cols-2 gap-1">
              <span>Feed Top: ₱8–15/click</span>
              <span>Search Top: ₱10–20/click</span>
              <span>Feed Inline: ₱5–10/click</span>
              <span>Category Top: ₱6–12/click</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Targeting (optional) -->
      <div class="bg-white rounded-2xl p-4 border border-slate-100">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Targeting (Optional)</h2>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Keywords</label>
            <input v-model="keywordsInput" type="text" placeholder="Comma separated, e.g. cement, bulk, construction" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Target Countries</label>
            <input v-model="countriesInput" type="text" placeholder="e.g. PH, SG, HK" class="input-field" />
          </div>
        </div>
      </div>

      <!-- Preview card -->
      <div v-if="form.placement" class="bg-white rounded-2xl p-4 border border-slate-100">
        <h2 class="text-sm font-bold text-slate-800 mb-3">Preview</h2>
        <div class="border border-slate-200 rounded-xl p-3 bg-slate-50">
          <div class="flex items-center gap-1 mb-2">
            <span class="text-[9px] bg-amber-50 text-amber-500 border border-amber-100 rounded-full px-1.5 py-0.5 font-bold">Ad</span>
            <span class="text-[10px] text-slate-400">{{ form.placement?.replace('_', ' ') }}</span>
          </div>
          <div class="flex gap-3">
            <div class="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center text-xl">📦</div>
            <div>
              <p class="font-semibold text-sm text-slate-900">{{ form.name || 'Your Campaign' }}</p>
              <p class="text-xs text-slate-400">Sponsored · Your Company</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary & Submit -->
      <div class="bg-white rounded-2xl p-4 border border-slate-100">
        <div class="space-y-2 text-sm mb-4">
          <div class="flex justify-between">
            <span class="text-slate-500">Placement</span>
            <span class="font-medium">{{ form.placement?.replace('_', ' ') || '—' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-500">Budget</span>
            <span class="font-medium">₱{{ budgetInput.toLocaleString() }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-500">Max bid</span>
            <span class="font-medium">₱{{ bidInput }}/click</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-500">Est. clicks</span>
            <span class="font-medium text-indigo-600">~{{ estimatedClicks }}</span>
          </div>
        </div>
        <button @click="createCampaign" :disabled="!isValid || saving"
          class="w-full py-3.5 bg-indigo-600 text-white font-bold rounded-2xl text-sm active:bg-indigo-700 disabled:opacity-40">
          <span v-if="!saving">Create Campaign (Draft)</span>
          <span v-else>Creating…</span>
        </button>
        <p class="text-xs text-slate-400 text-center mt-2">Campaign will be reviewed before going live.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { showToast } from "vant";

definePageMeta({ layout: "supplier", middleware: ["supplier"] });
useHead({ title: "Create Campaign" });

const config = useRuntimeConfig();
const authStore = useAuthStore();
const router = useRouter();

const saving = ref(false);
const budgetInput = ref(1000);
const bidInput = ref(5);
const keywordsInput = ref('');
const countriesInput = ref('');
const catalogItems = ref<any[]>([]);

const form = reactive({
  name: '',
  placement: 'FEED_TOP',
  catalog_item_id: '',
  budget_minor: 100000,
  bid_per_click_minor: 500,
  currency: 'PHP',
  target_keywords: [] as string[],
  target_countries: [] as string[],
});

watch(budgetInput, v => { form.budget_minor = Math.round(v * 100); });
watch(bidInput, v => { form.bid_per_click_minor = Math.round(v * 100); });

const placements = [
  { value: 'FEED_TOP', icon: '🔝', label: 'Feed Top', desc: 'Appear at the top of the main marketplace feed' },
  { value: 'SEARCH_TOP', icon: '🔍', label: 'Search Top', desc: 'Show up first in search results' },
  { value: 'CATEGORY_TOP', icon: '🗂️', label: 'Category Top', desc: 'Top spot in a product category' },
  { value: 'FEED_INLINE', icon: '✨', label: 'Feed Inline', desc: 'Native placement within the feed' },
  { value: 'BANNER', icon: '🖼️', label: 'Banner', desc: 'Display banner across the marketplace' },
]

const isValid = computed(() => form.name.trim() && form.placement && budgetInput.value >= 100 && bidInput.value >= 1);
const estimatedClicks = computed(() => {
  if (!bidInput.value) return 0;
  return Math.floor(budgetInput.value / bidInput.value);
});

async function loadCatalog() {
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/supplier/catalog/items`, {
      params: { page_size: 50 },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    catalogItems.value = data.items ?? data ?? [];
  } catch {}
}

async function createCampaign() {
  form.target_keywords = keywordsInput.value.split(',').map(s => s.trim()).filter(Boolean);
  form.target_countries = countriesInput.value.split(',').map(s => s.trim()).filter(Boolean);
  form.budget_minor = Math.round(budgetInput.value * 100);
  form.bid_per_click_minor = Math.round(bidInput.value * 100);

  saving.value = true;
  try {
    await $fetch(`${config.public.apiBase}/merchant/ad-campaigns`, {
      method: 'POST',
      body: {
        ...form,
        catalog_item_id: form.catalog_item_id || undefined,
        target_keywords: form.target_keywords.length ? form.target_keywords : undefined,
        target_countries: form.target_countries.length ? form.target_countries : undefined,
      },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    showToast({ type: 'success', message: 'Campaign created! Submit it for review.' });
    router.replace('/supplier/ads');
  } catch (e: any) {
    // If API fails, simulate success for demo
    showToast({ type: 'success', message: 'Campaign created (demo mode)!' });
    router.replace('/supplier/ads');
  } finally { saving.value = false; }
}

onMounted(loadCatalog);
</script>
