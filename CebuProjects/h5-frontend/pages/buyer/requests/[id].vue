<template>
  <div class="min-h-screen bg-slate-50 flex flex-col pb-6">
    <!-- Top Bar -->
    <div class="bg-white border-b border-slate-100 px-4 h-14 flex items-center gap-3 sticky top-0 z-40 pt-safe">
      <button type="button" class="text-slate-600 p-1 -ml-1" @click="$router.back()">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h1 class="font-semibold text-slate-900 flex-1 truncate">{{ $t("pages.request_detail") }}</h1>
      <NuxtLink v-if="offers.length > 1" :to="`/buyer/compare?intent_id=${id}`"
        class="text-xs bg-primary-600 text-white px-3 py-1.5 rounded-lg font-semibold">
        Compare
      </NuxtLink>
    </div>

    <!-- Success Banner -->
    <div v-if="posted" class="mx-4 mt-4 bg-green-50 border border-green-200 rounded-xl p-4 flex items-start gap-3">
      <svg class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
      </svg>
      <div>
        <p class="font-semibold text-green-800 text-sm">Request Posted!</p>
        <p class="text-green-700 text-xs mt-0.5">Verified suppliers in your area are being notified now.</p>
      </div>
    </div>

    <div v-if="loading" class="p-4 space-y-3">
      <div class="card"><div class="shimmer h-6 w-3/4 rounded mb-2"></div><div class="shimmer h-4 w-full rounded"></div></div>
      <div class="card"><div class="shimmer h-20 rounded"></div></div>
    </div>

    <template v-else-if="intent">
      <!-- Intent Info Card -->
      <div class="card mx-4 mt-4">
        <div class="flex justify-between items-start mb-3">
          <h2 class="font-bold text-slate-900 text-base flex-1 pr-2">{{ intent.title }}</h2>
          <span class="text-[11px] px-2 py-0.5 rounded-full font-medium flex-shrink-0" :class="getIntentBadgeClass(intent.status)">
            {{ getIntentStatusLabel(intent.status) }}
          </span>
        </div>
        <p v-if="intent.notes" class="text-sm text-slate-600 mb-3 leading-relaxed">{{ intent.notes }}</p>
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p class="text-xs text-slate-400 font-medium">Quantity</p>
            <p class="font-semibold text-slate-800">{{ intent.qty }} {{ intent.unit }}</p>
          </div>
          <div v-if="intent.budget_max_minor">
            <p class="text-xs text-slate-400 font-medium">Budget</p>
            <p class="font-semibold text-slate-800">{{ formatPrice(intent.budget_max_minor, intent.currency) }}</p>
          </div>
          <div v-if="intent.delivery_window_end">
            <p class="text-xs text-slate-400 font-medium">Deadline</p>
            <p class="font-semibold text-slate-800">{{ formatDate(intent.delivery_window_end) }}</p>
          </div>
          <div>
            <p class="text-xs text-slate-400 font-medium">Posted</p>
            <p class="font-semibold text-slate-800">{{ formatRelativeTime(intent.created_at) }}</p>
          </div>
          <div v-if="intent.city">
            <p class="text-xs text-slate-400 font-medium">Delivery Area</p>
            <p class="font-semibold text-slate-800">📍 {{ intent.city }}{{ intent.country ? ', ' + intent.country : '' }}</p>
          </div>
          <div v-if="intent.radius_km">
            <p class="text-xs text-slate-400 font-medium">Search Radius</p>
            <p class="font-semibold text-slate-800">{{ intent.radius_km }} km</p>
          </div>
        </div>
      </div>

      <!-- ── AI Ranked Supplier Candidates ── -->
      <section class="px-4 mt-5">
        <div class="flex items-center justify-between mb-3">
          <div>
            <h3 class="font-bold text-slate-900">🎯 Matched Suppliers</h3>
            <p class="text-xs text-slate-400 mt-0.5">AI-ranked by your criteria</p>
          </div>
          <!-- Sort selector -->
          <select v-model="candidateSort" @change="fetchCandidates"
            class="text-xs border border-slate-200 rounded-lg px-2 py-1.5 bg-white text-slate-600 outline-none">
            <option value="comprehensive">Comprehensive</option>
            <option value="cost">Best Price</option>
            <option value="trust">Most Trusted</option>
            <option value="distance">Nearest</option>
            <option value="delivery">Fastest ETA</option>
          </select>
        </div>

        <!-- Loading candidates -->
        <div v-if="candidatesLoading" class="space-y-2">
          <div v-for="n in 3" :key="n" class="card flex gap-3">
            <div class="shimmer w-8 h-8 rounded-full flex-shrink-0"></div>
            <div class="flex-1">
              <div class="shimmer h-3 w-3/4 rounded mb-2"></div>
              <div class="shimmer h-3 w-1/2 rounded"></div>
            </div>
          </div>
        </div>

        <!-- No candidates -->
        <div v-else-if="candidates.length === 0" class="card text-center py-6">
          <div class="text-3xl mb-2">🔍</div>
          <p class="text-sm text-slate-500">No matched suppliers yet for this category.</p>
          <p class="text-xs text-slate-400 mt-1">They will appear as suppliers add matching products.</p>
        </div>

        <!-- Candidates list -->
        <div v-else class="space-y-2">
          <div v-for="(c, idx) in candidates" :key="c.catalog_item_id ?? idx"
            class="card flex items-start gap-3 cursor-pointer active:bg-indigo-50"
            role="button"
            tabindex="0"
            @click="openCandidate(c)"
            @keyup.enter="openCandidate(c)">
            <!-- Rank medal -->
            <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
              :class="idx === 0 ? 'bg-amber-400 text-white' : idx === 1 ? 'bg-slate-300 text-slate-700' : idx === 2 ? 'bg-orange-200 text-orange-800' : 'bg-slate-100 text-slate-500'">
              {{ idx + 1 }}
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-1">
                <div class="min-w-0">
                  <p class="font-semibold text-slate-900 text-sm truncate">{{ c.company_name }}</p>
                  <p class="text-xs text-slate-500 truncate">{{ c.catalog_item_title }}</p>
                </div>
                <div class="text-right flex-shrink-0">
                  <p class="text-sm font-bold text-indigo-600">{{ c.ranking_score }}pts</p>
                </div>
              </div>

              <!-- Score breakdown chips -->
              <div class="flex flex-wrap gap-1.5 mt-2">
                <span v-if="c.price_score" class="text-[10px] bg-green-50 text-green-700 px-1.5 py-0.5 rounded-full">
                  💰 Price {{ Math.round(c.price_score) }}
                </span>
                <span v-if="c.trust_score || c.score_breakdown?.trust_score" class="text-[10px] bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded-full">
                  ⭐ Trust {{ Math.round(c.trust_score || c.score_breakdown?.trust_score || 0) }}
                </span>
                <span v-if="candidateDistance(c) != null" class="text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded-full">
                  📍 {{ candidateDistance(c) }}km
                </span>
                <span v-if="c.stock_score || c.score_breakdown?.has_stock" class="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-full">
                  📦 Stock ok
                </span>
                <span v-if="c.score_breakdown?.bound_catalog_item" class="text-[10px] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full">
                  Bound
                </span>
              </div>

              <!-- Price row -->
              <div v-if="c.unit_price_minor" class="mt-2 flex items-center gap-2">
                <span class="text-sm font-bold text-slate-900">{{ formatPrice(c.unit_price_minor, c.currency ?? 'PHP') }}</span>
                <span class="text-xs text-slate-400">/ {{ c.unit }}</span>
                <span v-if="c.eta_days" class="text-xs text-slate-400">· ETA {{ c.eta_days }}d</span>
              </div>

              <div class="mt-3 flex gap-2">
                <button type="button" class="flex-1 rounded-xl border border-slate-200 py-2 text-xs font-semibold text-slate-700"
                  @click.stop="openCandidate(c)">
                  Details
                </button>
                <button type="button" class="flex-1 rounded-xl bg-primary-600 py-2 text-xs font-semibold text-white"
                  @click.stop="bindCandidate(c)">
                  Bind
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div v-if="selectedCandidate" class="fixed inset-0 z-50 bg-slate-900/40 flex items-end" @click.self="selectedCandidate = null">
        <div class="w-full rounded-t-3xl bg-white p-5 shadow-2xl max-h-[82vh] overflow-y-auto">
          <div class="mx-auto mb-4 h-1 w-12 rounded-full bg-slate-200"></div>
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-primary-600">Matched supplier</p>
              <h3 class="mt-1 text-lg font-bold text-slate-900">{{ selectedCandidate.company_name }}</h3>
              <p class="mt-1 text-sm text-slate-500">{{ selectedCandidate.catalog_item_title }}</p>
            </div>
            <button type="button" class="rounded-full bg-slate-100 px-3 py-1 text-slate-500" @click="selectedCandidate = null">Close</button>
          </div>

          <div class="mt-4 rounded-2xl bg-indigo-50 p-3 text-sm text-indigo-800">
            {{ selectedCandidate.why_recommended || "Matching category and buyer criteria." }}
          </div>

          <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div class="rounded-2xl bg-slate-50 p-3">
              <p class="text-xs text-slate-400">Rank score</p>
              <p class="mt-1 font-bold text-slate-900">{{ selectedCandidate.ranking_score }} pts</p>
            </div>
            <div class="rounded-2xl bg-slate-50 p-3">
              <p class="text-xs text-slate-400">Price</p>
              <p class="mt-1 font-bold text-slate-900">{{ formatPrice(selectedCandidate.unit_price_minor || selectedCandidate.score_breakdown?.price_minor || 0, selectedCandidate.currency || intent.currency) }}</p>
            </div>
            <div class="rounded-2xl bg-slate-50 p-3">
              <p class="text-xs text-slate-400">Distance</p>
              <p class="mt-1 font-bold text-slate-900">{{ candidateDistance(selectedCandidate) ?? "N/A" }} km</p>
            </div>
            <div class="rounded-2xl bg-slate-50 p-3">
              <p class="text-xs text-slate-400">Deal rate</p>
              <p class="mt-1 font-bold text-slate-900">{{ Math.round((selectedCandidate.score_breakdown?.deal_completion_rate || 0) * 100) }}%</p>
            </div>
          </div>

          <div class="mt-4 grid grid-cols-2 gap-2">
            <NuxtLink :to="`/marketplace/${selectedCandidate.catalog_item_id}`" class="rounded-xl border border-slate-200 py-3 text-center text-sm font-semibold text-slate-700">
              View item
            </NuxtLink>
            <button type="button" class="rounded-xl bg-primary-600 py-3 text-sm font-semibold text-white" @click="bindCandidate(selectedCandidate)">
              Bind supplier
            </button>
          </div>
        </div>
      </div>

      <!-- ── Offers Received ── -->
      <section class="px-4 mt-6">
        <div class="flex justify-between items-center mb-3">
          <h3 class="font-bold text-slate-900">
            Offers <span class="text-primary-600">({{ displayOffers.length }})</span>
          </h3>
          <NuxtLink v-if="displayOffers.length > 1" :to="`/buyer/compare?intent_id=${intent.id}`"
            class="text-sm text-primary-600 font-medium">Compare All</NuxtLink>
        </div>

        <div v-if="offersLoading" class="space-y-3">
          <div v-for="n in 2" :key="n" class="card"><div class="shimmer h-20 rounded"></div></div>
        </div>

        <div v-else-if="displayOffers.length === 0" class="card text-center py-8">
          <div class="text-4xl mb-2">⏳</div>
          <p class="text-slate-500 text-sm font-medium">{{ $t("pages.waiting_for_offers") }}</p>
          <p class="text-slate-400 text-xs mt-1">{{ $t("pages.suppliers_being_notified") }}</p>
        </div>

        <div v-else class="space-y-3">
          <div v-for="offer in displayOffers" :key="offer.id"
            class="card border transition-colors"
            :class="offer.status === 'AWARDED' ? 'border-green-300 bg-green-50' : 'border-transparent'">
            <!-- Award ribbon -->
            <div v-if="offer.status === 'AWARDED'" class="text-xs text-green-700 font-bold mb-2 flex items-center gap-1">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
              Awarded Offer
            </div>

            <div class="flex justify-between items-start mb-2">
              <div>
                <p class="font-bold text-slate-900 text-base">{{ formatPrice(offer.total_price_minor, offer.currency) }}</p>
                <p class="text-xs text-slate-500">{{ formatPrice(offer.unit_price_minor, offer.currency) }} / {{ intent.unit }}</p>
              </div>
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="getOfferBadgeClass(offer.status)">
                {{ getOfferStatusLabel(offer.status) }}
              </span>
            </div>
            <div class="flex items-center gap-3 text-xs text-slate-500 mb-3 flex-wrap">
              <span>📦 {{ offer.qty_available }} available</span>
              <span v-if="offer.eta_date">· 🚚 ETA {{ formatDate(offer.eta_date) }}</span>
              <span v-if="offer.company_name" class="font-medium text-slate-700">· {{ offer.company_name }}</span>
            </div>
            <p v-if="offer.message" class="text-xs text-slate-600 italic mb-3 bg-slate-50 rounded-lg px-3 py-2">"{{ offer.message }}"</p>

            <div class="flex gap-2">
              <button type="button"
                v-if="intent.status === 'ACTIVE' && offer.status !== 'AWARDED'"
                class="flex-1 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-semibold active:bg-primary-700"
                @click="awardOffer(offer.id)"
              >
                Award This Offer
              </button>
              <button type="button"
                v-if="offer.status === 'AWARDED'"
                class="flex-1 py-2.5 bg-green-600 text-white rounded-xl text-sm font-semibold cursor-default" disabled>
                ✓ Awarded
              </button>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { showConfirmDialog, showToast } from "vant";
import { demoSupplierCandidatesForIntent, isDemoToken } from "~/utils/demoData";

definePageMeta({ layout: "default", middleware: ["buyer"] });
useHead({ title: "Request Detail" });

const route = useRoute();
const router = useRouter();
const config = useRuntimeConfig();
const intentStore = useIntentStore();
const authStore = useAuthStore();
const { formatPrice, formatDate, formatRelativeTime, getIntentStatusLabel, getOfferStatusLabel } = useApiUtils();

const id = route.params.id as string;
const posted = route.query.posted === "1";
const loading = ref(true);
const offersLoading = ref(false);
const candidatesLoading = ref(false);
const candidateSort = ref("comprehensive");
const candidates = ref<any[]>([]);
const selectedCandidate = ref<any | null>(null);

const intent = computed(() => intentStore.currentIntent);
const offers = computed(() => intentStore.offers);

// Mock offers for demo when API returns empty
const MOCK_OFFERS = [
  { id: 'mo1', total_price_minor: 24500000, unit_price_minor: 49000, currency: 'PHP', qty_available: 600, eta_date: new Date(Date.now()+86400000*3).toISOString().split('T')[0], status: 'SUBMITTED', message: 'Ready for immediate delivery. Price includes delivery to Cebu City.', company_name: 'Cebu Building Supply Co.' },
  { id: 'mo2', total_price_minor: 22000000, unit_price_minor: 44000, currency: 'PHP', qty_available: 500, eta_date: new Date(Date.now()+86400000*5).toISOString().split('T')[0], status: 'SUBMITTED', message: 'Bulk discount available for 700+ bags. Contact for pricing.', company_name: 'Southern Materials Corp.' },
  { id: 'mo3', total_price_minor: 26000000, unit_price_minor: 52000, currency: 'PHP', qty_available: 1000, eta_date: new Date(Date.now()+86400000*2).toISOString().split('T')[0], status: 'AWARDED', message: 'Premium cement, ISO certified. Fastest delivery.', company_name: 'PhilCem Distributors Inc.' },
]

// Mock candidates for demo
const MOCK_CANDIDATES = [
  { catalog_item_id: 'mc1', company_name: 'Cebu Building Supply Co.', catalog_item_title: 'Portland Cement Type I – OPC', ranking_score: 94.5, price_score: 88, trust_score: 92, distance_km: 3.2, stock_score: 90, unit_price_minor: 4900000, currency: 'PHP', unit: 'bag', eta_days: 2 },
  { catalog_item_id: 'mc2', company_name: 'Southern Materials Corp.', catalog_item_title: 'Holcim Cement – 40kg', ranking_score: 87.2, price_score: 95, trust_score: 78, distance_km: 8.5, stock_score: 85, unit_price_minor: 4400000, currency: 'PHP', unit: 'bag', eta_days: 4 },
  { catalog_item_id: 'mc3', company_name: 'PhilCem Distributors Inc.', catalog_item_title: 'Lafarge Premium Cement', ranking_score: 82.1, price_score: 72, trust_score: 96, distance_km: 12.1, stock_score: 95, unit_price_minor: 5200000, currency: 'PHP', unit: 'bag', eta_days: 1 },
  { catalog_item_id: 'mc4', company_name: 'Visayas Construction Hub', catalog_item_title: 'Republic Cement – OPC Type', ranking_score: 75.8, price_score: 80, trust_score: 70, distance_km: 15.3, stock_score: 75, unit_price_minor: 4700000, currency: 'PHP', unit: 'bag', eta_days: 3 },
]

const displayOffers = computed(() => {
  const real = offers.value
  if (real.length > 0) return real
  return id.startsWith('m') ? MOCK_OFFERS as any[] : []
})

async function fetchCandidates() {
  const demoEnabled = authStore.isDemoMode && (isDemoToken(authStore.accessToken) || id.startsWith("demo-"));
  if (demoEnabled) {
    const demoRows = demoSupplierCandidatesForIntent(id)
    candidates.value = sortMockCandidates(demoRows.length ? demoRows : MOCK_CANDIDATES)
    return
  }
  candidatesLoading.value = true
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/intents/${id}/supplier-candidates`, {
      params: { sort: candidateSort.value, limit: 8 },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    candidates.value = data.candidates ?? []
  } catch {
    candidates.value = []
  } finally {
    candidatesLoading.value = false
  }
}

function sortMockCandidates(list: any[]) {
  const copy = [...list]
  switch (candidateSort.value) {
    case 'cost': return copy.sort((a, b) => a.unit_price_minor - b.unit_price_minor)
    case 'trust': return copy.sort((a, b) => (b.trust_score || b.score_breakdown?.trust_score || 0) - (a.trust_score || a.score_breakdown?.trust_score || 0))
    case 'distance': return copy.sort((a, b) => (candidateDistance(a) ?? 9999) - (candidateDistance(b) ?? 9999))
    case 'delivery': return copy.sort((a, b) => a.eta_days - b.eta_days)
    default: return copy.sort((a, b) => b.ranking_score - a.ranking_score)
  }
}

function candidateDistance(candidate: any) {
  return candidate?.distance_km ?? candidate?.score_breakdown?.distance_km ?? null
}

function openCandidate(candidate: any) {
  selectedCandidate.value = candidate
}

async function bindCandidate(candidate: any) {
  try {
    const demoEnabled = authStore.isDemoMode && (isDemoToken(authStore.accessToken) || id.startsWith("demo-"));
    if (demoEnabled) {
      candidates.value = candidates.value.map((row) => ({
        ...row,
        score_breakdown: {
          ...(row.score_breakdown || {}),
          bound_catalog_item: row.catalog_item_id === candidate.catalog_item_id,
          bound_supplier: row.company_id === candidate.company_id,
        },
      }))
      selectedCandidate.value = candidates.value.find((row) => row.catalog_item_id === candidate.catalog_item_id) || candidate
      showToast({ type: "success", message: "Supplier bound for demo request." })
      return
    }
    const data = await $fetch<any>(`${config.public.apiBase}/intents/${id}/supplier-candidates/${candidate.catalog_item_id}/bind`, {
      method: "POST",
      body: { note: "Buyer selected from matched suppliers panel" },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    await fetchCandidates()
    selectedCandidate.value = data.candidate
    showToast({ type: "success", message: "Supplier bound to request." })
  } catch (e: any) {
    showToast({ type: "fail", message: e?.data?.detail || "Bind failed" })
  }
}

function getIntentBadgeClass(status: string) {
  const map: Record<string, string> = { DRAFT: "badge-gray", ACTIVE: "badge-primary", AWARDED: "badge-success", CLOSED: "badge-gray", CANCELED: "badge-gray", EXPIRED: "badge-danger" };
  return map[status] || "badge-gray";
}

function getOfferBadgeClass(status: string) {
  const map: Record<string, string> = { SUBMITTED: "badge-primary", VIEWED: "badge-primary", SHORTLISTED: "badge-warning", AWARDED: "badge-success", REJECTED: "badge-gray", WITHDRAWN: "badge-gray", EXPIRED: "badge-danger" };
  return map[status] || "badge-gray";
}

async function awardOffer(offerId: string) {
  try {
    await showConfirmDialog({ title: "Award this offer?", message: "This will create an order and notify the supplier." });
    await intentStore.awardOffer(offerId);
    showToast({ type: "success", message: "Offer awarded! Order created." });
    await intentStore.fetchIntent(id);
    await intentStore.fetchOffers(id);
    router.push("/buyer/orders");
  } catch { /* user cancelled */ }
}

onMounted(async () => {
  if (!authStore.systemMode) {
    await authStore.fetchSystemMode();
  }
  // Fetch intent
  if (!id.startsWith('m')) {
    await intentStore.fetchIntent(id);
  }
  loading.value = false;

  // Fetch offers
  if (!id.startsWith('m')) {
    offersLoading.value = true;
    await intentStore.fetchOffers(id);
    offersLoading.value = false;
  }

  // Fetch ranked candidates
  await fetchCandidates();
});
</script>
