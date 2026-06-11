<template>
  <div>
    <!-- Top Bar -->
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center justify-between sticky top-0 z-40 pt-safe">
      <h1 class="font-bold text-slate-900 text-lg">Ad Campaigns</h1>
      <NuxtLink to="/supplier/ads/create">
        <button class="bg-indigo-600 text-white text-sm font-semibold px-3 py-1.5 rounded-lg">+ Create</button>
      </NuxtLink>
    </div>

    <!-- Stats summary -->
    <div class="grid grid-cols-3 gap-3 px-4 py-3">
      <div class="bg-white rounded-xl p-3 text-center border border-slate-100">
        <p class="text-xl font-extrabold text-green-600">{{ activeCampaigns }}</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Active</p>
      </div>
      <div class="bg-white rounded-xl p-3 text-center border border-slate-100">
        <p class="text-xl font-extrabold text-amber-500">{{ pendingCampaigns }}</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Pending</p>
      </div>
      <div class="bg-white rounded-xl p-3 text-center border border-slate-100">
        <p class="text-xl font-extrabold text-indigo-600">{{ totalClicks.toLocaleString() }}</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Total Clicks</p>
      </div>
    </div>

    <!-- Filter tabs -->
    <div class="bg-white border-b border-slate-100 px-4 flex gap-1 overflow-x-auto no-scrollbar">
      <button v-for="tab in statusTabs" :key="tab.value" @click="activeTab = tab.value"
        class="flex-shrink-0 py-3 px-3 text-sm font-medium border-b-2 transition-colors"
        :class="activeTab === tab.value ? 'border-indigo-600 text-indigo-700' : 'border-transparent text-slate-500'">
        {{ tab.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-4 space-y-3">
      <div v-for="n in 3" :key="n" class="bg-white rounded-2xl p-4 border border-slate-100">
        <div class="shimmer h-4 w-2/3 rounded mb-2"></div>
        <div class="shimmer h-3 w-1/2 rounded mb-3"></div>
        <div class="shimmer h-2 w-full rounded-full"></div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else-if="filteredCampaigns.length === 0" class="empty-state mt-8">
      <div class="text-5xl mb-3">📢</div>
      <p class="text-slate-500 font-medium">No campaigns yet</p>
      <p class="text-slate-400 text-xs mt-1">Promote your products to get more orders</p>
      <NuxtLink to="/supplier/ads/create">
        <button class="mt-4 btn-primary py-2.5 px-6 w-auto text-sm">Create Campaign</button>
      </NuxtLink>
    </div>

    <!-- Campaign cards -->
    <div v-else class="p-4 space-y-3">
      <div v-for="c in filteredCampaigns" :key="c.id" class="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <div class="p-4">
          <!-- Header row -->
          <div class="flex items-start justify-between gap-2 mb-3">
            <div class="flex items-center gap-2.5 flex-1 min-w-0">
              <div class="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center text-xl flex-shrink-0">
                {{ placementIcon(c.placement) }}
              </div>
              <div class="min-w-0">
                <h3 class="font-bold text-slate-900 text-sm truncate">{{ c.name || c.title || 'Campaign' }}</h3>
                <p class="text-xs text-slate-400">{{ c.placement?.replace('_', ' ') }}</p>
              </div>
            </div>
            <span :class="['text-[10px] px-2 py-0.5 rounded-full font-bold flex-shrink-0', statusClass(c.status)]">
              {{ c.status?.replace('_', ' ') }}
            </span>
          </div>

          <!-- Budget progress -->
          <div class="mb-3">
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="text-slate-500">Budget spent</span>
              <span class="font-semibold text-slate-800">{{ formatMinor(c.spent_minor, c.currency) }} / {{ formatMinor(c.budget_minor, c.currency) }}</span>
            </div>
            <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div class="h-full bg-indigo-500 rounded-full transition-all"
                :style="{ width: `${Math.min(100, (c.spent_minor / Math.max(c.budget_minor, 1)) * 100)}%` }"></div>
            </div>
          </div>

          <!-- Metrics row -->
          <div class="flex gap-4 text-xs text-slate-500">
            <span>👁 {{ (c.impressions ?? 0).toLocaleString() }}</span>
            <span>🖱️ {{ c.clicks ?? 0 }} clicks</span>
            <span>📊 {{ ((c.ctr ?? 0) * 100).toFixed(1) }}% CTR</span>
            <span>💰 {{ formatMinor(c.bid_per_click_minor, c.currency) }}/click</span>
          </div>

          <!-- Rejection reason -->
          <div v-if="c.rejection_reason" class="mt-2 text-xs text-red-500 bg-red-50 rounded-lg px-2.5 py-1.5">
            ⚠️ {{ c.rejection_reason }}
          </div>
        </div>

        <!-- Action buttons -->
        <div class="flex border-t border-slate-100">
          <button v-if="c.status === 'DRAFT'" @click="submitCampaign(c)"
            class="flex-1 py-2.5 text-xs font-semibold text-indigo-600 hover:bg-indigo-50 transition-colors">
            Submit for Review
          </button>
          <button v-if="c.status === 'ACTIVE'" @click="pauseCampaign(c)"
            class="flex-1 py-2.5 text-xs font-semibold text-amber-600 hover:bg-amber-50 transition-colors">
            ⏸ Pause
          </button>
          <div v-if="c.status === 'DRAFT' || c.status === 'ACTIVE'" class="w-px bg-slate-100"></div>
          <button @click="viewMetrics(c)"
            class="flex-1 py-2.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors">
            📊 Metrics
          </button>
        </div>
      </div>
    </div>

    <!-- Metrics bottom sheet -->
    <van-action-sheet v-model:show="showMetrics" title="Campaign Metrics">
      <div v-if="selectedCampaign" class="px-5 pt-2 pb-10 space-y-4">
        <div class="bg-indigo-50 rounded-2xl p-4">
          <h3 class="font-bold text-slate-900 mb-1">{{ selectedCampaign.name || 'Campaign' }}</h3>
          <span :class="['text-[11px] px-2 py-0.5 rounded-full font-bold', statusClass(selectedCampaign.status)]">
            {{ selectedCampaign.status?.replace('_', ' ') }}
          </span>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-white rounded-xl p-3 border border-slate-100 text-center">
            <p class="text-2xl font-extrabold text-slate-900">{{ (selectedCampaign.impressions ?? 0).toLocaleString() }}</p>
            <p class="text-xs text-slate-400 mt-1">Impressions</p>
          </div>
          <div class="bg-white rounded-xl p-3 border border-slate-100 text-center">
            <p class="text-2xl font-extrabold text-indigo-600">{{ selectedCampaign.clicks ?? 0 }}</p>
            <p class="text-xs text-slate-400 mt-1">Clicks</p>
          </div>
          <div class="bg-white rounded-xl p-3 border border-slate-100 text-center">
            <p class="text-2xl font-extrabold text-green-600">{{ ((selectedCampaign.ctr ?? 0) * 100).toFixed(2) }}%</p>
            <p class="text-xs text-slate-400 mt-1">CTR</p>
          </div>
          <div class="bg-white rounded-xl p-3 border border-slate-100 text-center">
            <p class="text-2xl font-extrabold text-amber-600">{{ selectedCampaign.conversions ?? 0 }}</p>
            <p class="text-xs text-slate-400 mt-1">Conversions</p>
          </div>
        </div>
        <div class="bg-white rounded-xl p-4 border border-slate-100">
          <div class="flex justify-between text-sm mb-2">
            <span class="text-slate-500">Budget</span>
            <span class="font-semibold">{{ formatMinor(selectedCampaign.budget_minor, selectedCampaign.currency) }}</span>
          </div>
          <div class="flex justify-between text-sm mb-2">
            <span class="text-slate-500">Spent</span>
            <span class="font-semibold text-red-500">{{ formatMinor(selectedCampaign.spent_minor, selectedCampaign.currency) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-slate-500">Remaining</span>
            <span class="font-semibold text-green-600">{{ formatMinor((selectedCampaign.budget_minor ?? 0) - (selectedCampaign.spent_minor ?? 0), selectedCampaign.currency) }}</span>
          </div>
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { showToast } from "vant";

definePageMeta({ layout: "supplier", middleware: ["supplier"] });
useHead({ title: "Ad Campaigns" });

const config = useRuntimeConfig();
const authStore = useAuthStore();
const loading = ref(false);
const campaigns = ref<any[]>([]);
const activeTab = ref('ALL');
const showMetrics = ref(false);
const selectedCampaign = ref<any>(null);

const statusTabs = [
  { label: 'All', value: 'ALL' },
  { label: 'Draft', value: 'DRAFT' },
  { label: 'Pending', value: 'PENDING_REVIEW' },
  { label: 'Active', value: 'ACTIVE' },
  { label: 'Paused', value: 'PAUSED' },
]

// Mock campaigns for demo
const MOCK_CAMPAIGNS = [
  { id: 'mc1', name: 'Cement Summer Sale', title: 'Cement Summer Sale', placement: 'FEED_TOP', status: 'ACTIVE', budget_minor: 500000, spent_minor: 182000, bid_per_click_minor: 5000, currency: 'PHP', impressions: 12400, clicks: 342, ctr: 0.0276, conversions: 28 },
  { id: 'mc2', name: 'Medical Supplies Promo', title: 'Medical Supplies Promo', placement: 'SEARCH_TOP', status: 'PENDING_REVIEW', budget_minor: 1000000, spent_minor: 0, bid_per_click_minor: 8000, currency: 'PHP', impressions: 0, clicks: 0, ctr: 0, conversions: 0 },
  { id: 'mc3', name: 'Safety Equipment Q4', title: 'Safety Equipment Q4', placement: 'CATEGORY_TOP', status: 'DRAFT', budget_minor: 300000, spent_minor: 0, bid_per_click_minor: 4000, currency: 'PHP', impressions: 0, clicks: 0, ctr: 0, conversions: 0 },
  { id: 'mc4', name: 'Office Furniture Blowout', title: 'Office Furniture Blowout', placement: 'FEED_INLINE', status: 'PAUSED', budget_minor: 750000, spent_minor: 612000, bid_per_click_minor: 6000, currency: 'PHP', impressions: 9800, clicks: 201, ctr: 0.0205, conversions: 15, rejection_reason: null },
]

const displayCampaigns = computed(() => campaigns.value.length > 0 ? campaigns.value : MOCK_CAMPAIGNS)
const filteredCampaigns = computed(() => {
  if (activeTab.value === 'ALL') return displayCampaigns.value
  return displayCampaigns.value.filter(c => c.status === activeTab.value)
})

const activeCampaigns = computed(() => displayCampaigns.value.filter(c => c.status === 'ACTIVE').length)
const pendingCampaigns = computed(() => displayCampaigns.value.filter(c => c.status === 'PENDING_REVIEW').length)
const totalClicks = computed(() => displayCampaigns.value.reduce((sum, c) => sum + (c.clicks ?? 0), 0))

async function loadCampaigns() {
  loading.value = true;
  try {
    const data = await $fetch<any[]>(`${config.public.apiBase}/merchant/ad-campaigns`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    campaigns.value = data ?? [];
  } catch { campaigns.value = []; } finally { loading.value = false; }
}

async function submitCampaign(c: any) {
  try {
    if (!c.id.startsWith('mc')) {
      const data = await $fetch<any>(`${config.public.apiBase}/merchant/ad-campaigns/${c.id}/submit`, {
        method: 'POST', headers: { Authorization: `Bearer ${authStore.accessToken}` },
      });
      c.status = data.status;
    } else {
      c.status = 'PENDING_REVIEW';
    }
    showToast({ type: 'success', message: 'Submitted for review!' });
  } catch (e: any) { showToast({ type: 'fail', message: e?.data?.detail ?? 'Failed' }); }
}

async function pauseCampaign(c: any) {
  try {
    if (!c.id.startsWith('mc')) {
      const data = await $fetch<any>(`${config.public.apiBase}/merchant/ad-campaigns/${c.id}/pause`, {
        method: 'POST', headers: { Authorization: `Bearer ${authStore.accessToken}` },
      });
      c.status = data.status;
    } else {
      c.status = 'PAUSED';
    }
    showToast({ type: 'success', message: 'Campaign paused' });
  } catch (e: any) { showToast({ type: 'fail', message: e?.data?.detail ?? 'Failed' }); }
}

function viewMetrics(c: any) {
  selectedCampaign.value = c;
  showMetrics.value = true;
}

function formatMinor(minor: number | null | undefined, currency = 'PHP') {
  if (!minor) return '₱0';
  return new Intl.NumberFormat('en-PH', { style: 'currency', currency: currency || 'PHP', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(minor / 100);
}

function placementIcon(p: string) {
  const m: Record<string, string> = { FEED_TOP: '🔝', FEED_INLINE: '✨', CATEGORY_TOP: '🗂️', SEARCH_TOP: '🔍', BANNER: '🖼️' };
  return m[p] ?? '📢';
}

function statusClass(s: string) {
  const m: Record<string, string> = { DRAFT: 'bg-slate-100 text-slate-600', PENDING_REVIEW: 'bg-amber-100 text-amber-700', ACTIVE: 'bg-green-100 text-green-700', PAUSED: 'bg-slate-100 text-slate-500', REJECTED: 'bg-red-100 text-red-600', EXPIRED: 'bg-slate-100 text-slate-400' };
  return m[s] ?? 'bg-slate-100 text-slate-500';
}

onMounted(loadCampaigns);
</script>
