<template>
  <div class="space-y-6" v-if="intent">
    <div class="flex items-center space-x-4 mb-2">
      <UButton to="/buyer/requests" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
      <div>
        <div class="flex items-center space-x-3">
          <h1 class="text-2xl font-bold text-slate-900">{{ intent.title }}</h1>
          <UBadge :color="getStatusColor(intent.status)" variant="subtle">{{ intent.status }}</UBadge>
        </div>
        <p class="text-sm text-slate-500 mt-1">Request ID: #{{ intent.id.split('-')[0] }} • Posted: {{ new Date(intent.created_at).toLocaleDateString() }}</p>
      </div>
      <div class="ml-auto">
        <UButton color="indigo" variant="outline" :to="`/buyer/requests/${intent.id}/offers`" icon="i-heroicons-table-cells">View Offers</UButton>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Request Details -->
      <UCard class="md:col-span-2">
        <template #header>
          <h3 class="text-lg font-medium text-slate-900">Request Specifications</h3>
        </template>
        
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-6">
          <div>
            <dt class="text-sm font-medium text-slate-500">Category ID</dt>
            <dd class="mt-1 text-sm text-slate-900">{{ intent.category_id }}</dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-slate-500">Budget Range</dt>
            <dd class="mt-1 text-sm text-slate-900 font-semibold" v-if="intent.budget_min_minor || intent.budget_max_minor">
              {{ intent.currency }} {{ intent.budget_min_minor ? intent.budget_min_minor / 100 : 0 }} - {{ intent.budget_max_minor ? intent.budget_max_minor / 100 : 'Max' }}
            </dd>
            <dd class="mt-1 text-sm text-slate-900 font-semibold" v-else>Open</dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-slate-500">Quantity Required</dt>
            <dd class="mt-1 text-sm text-slate-900">{{ intent.qty }} {{ intent.unit }}</dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-slate-500">Delivery Window</dt>
            <dd class="mt-1 text-sm text-slate-900">
              <span v-if="intent.delivery_window_start || intent.delivery_window_end">
                {{ intent.delivery_window_start ? new Date(intent.delivery_window_start).toLocaleDateString() : 'Now' }} - {{ intent.delivery_window_end ? new Date(intent.delivery_window_end).toLocaleDateString() : 'Anytime' }}
              </span>
              <span v-else>Anytime</span>
            </dd>
          </div>
          <div class="sm:col-span-2">
            <dt class="text-sm font-medium text-slate-500">Detailed Description</dt>
            <dd class="mt-1 text-sm text-slate-900">{{ intent.notes || 'No description provided.' }}</dd>
          </div>
          <div class="sm:col-span-2" v-if="intent.attachments && intent.attachments.length">
            <dt class="text-sm font-medium text-slate-500 mb-2">Attachments</dt>
            <dd class="flex gap-2 flex-wrap">
              <div v-for="att in intent.attachments" :key="att" class="flex items-center p-3 border border-slate-200 rounded-md">
                <UIcon name="i-heroicons-document-text" class="w-6 h-6 text-indigo-500 mr-2" />
                <span class="text-sm font-medium text-slate-900">{{ att.split('/').pop() }}</span>
              </div>
            </dd>
          </div>
        </dl>
      </UCard>

      <!-- Logistics & Status -->
      <div class="space-y-6">
        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">Logistics</h3>
          </template>
          <div class="space-y-4">
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Delivery Area</dt>
              <dd class="mt-1 flex items-center text-sm text-slate-900">
                <UIcon name="i-heroicons-map-pin" class="w-4 h-4 mr-1 text-slate-400" />
                {{ intent.city ? intent.city + ', ' : '' }}{{ intent.country || 'N/A' }}
              </dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Search Radius</dt>
              <dd class="mt-1 text-sm text-slate-900">{{ intent.radius_km || 30 }} km</dd>
            </div>
            <div class="bg-indigo-50 p-3 rounded-md border border-indigo-100">
              <div class="text-xs text-indigo-800 font-semibold mb-1">Ping Reach</div>
              <div class="text-sm text-indigo-900">Sent to matching local suppliers.</div>
            </div>
          </div>
        </UCard>
      </div>
    </div>
  </div>

  <!-- Supplier Candidates Panel -->
  <div v-if="intent" class="mt-6">
    <UCard>
      <template #header>
        <div class="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">🎯 Matched Suppliers</h3>
            <p class="text-xs text-slate-500 mt-0.5">AI-ranked candidates based on your request</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs text-slate-500">Sort by:</span>
            <select v-model="candidateSort" @change="fetchCandidates" class="text-sm border border-slate-200 rounded-lg px-2 py-1.5">
              <option value="comprehensive">Comprehensive</option>
              <option value="cost">Best Price</option>
              <option value="trust">Most Trusted</option>
              <option value="distance">Nearest</option>
              <option value="delivery">Fastest Delivery</option>
            </select>
          </div>
        </div>
      </template>

      <div v-if="candidatesLoading" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 animate-spin text-slate-400" />
      </div>

      <div v-else-if="candidates.length === 0" class="text-center py-8 text-slate-400">
        <div class="text-3xl mb-2">🔍</div>
        <p class="text-sm">No matched suppliers yet for this request category.</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="(c, idx) in candidates"
          :key="c.catalog_item_id"
          class="flex items-start gap-4 p-4 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/30 transition-all cursor-pointer"
          role="button"
          tabindex="0"
          @click="openCandidate(c)"
          @keyup.enter="openCandidate(c)"
        >
          <!-- Rank badge -->
          <div
            class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
            :class="idx === 0 ? 'bg-amber-400 text-white' : idx === 1 ? 'bg-slate-300 text-slate-700' : 'bg-orange-200 text-orange-800'"
          >
            {{ idx + 1 }}
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-2">
              <div>
                <div class="flex items-center gap-2">
                  <p class="font-semibold text-slate-900 text-sm">{{ c.company_name }}</p>
                  <span
                    v-if="c.score_breakdown?.bound_catalog_item"
                    class="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-700"
                  >
                    Bound item
                  </span>
                  <span
                    v-else-if="c.score_breakdown?.bound_supplier"
                    class="rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-semibold text-violet-700"
                  >
                    Bound supplier
                  </span>
                </div>
                <p class="text-xs text-slate-500 truncate">{{ c.catalog_item_title }}</p>
              </div>
              <div class="text-right flex-shrink-0">
                <span class="text-sm font-bold text-indigo-600">{{ c.ranking_score }}pts</span>
              </div>
            </div>

            <!-- Why recommended -->
            <p class="mt-1.5 text-xs text-emerald-700 bg-emerald-50 rounded-lg px-2 py-1 inline-block">
              ✓ {{ c.why_recommended }}
            </p>

            <!-- Score breakdown chips -->
            <div class="mt-2 flex flex-wrap gap-1.5">
              <span v-if="c.score_breakdown.distance_km !== null" class="text-[10px] bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                📍 {{ c.score_breakdown.distance_km }}km
              </span>
              <span class="text-[10px] bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                ⭐ Trust {{ c.score_breakdown.trust_score }}
              </span>
              <span class="text-[10px] bg-slate-100 text-slate-600 rounded-full px-2 py-0.5">
                🤝 {{ Math.round(c.score_breakdown.deal_completion_rate * 100) }}% deal rate
              </span>
              <span v-if="c.score_breakdown.has_stock" class="text-[10px] bg-green-50 text-green-700 rounded-full px-2 py-0.5">
                ✅ In Stock ({{ c.score_breakdown.stock_qty }})
              </span>
              <span
                class="text-[10px] rounded-full px-2 py-0.5"
                :class="c.score_breakdown.verification_level === 'TRUSTED' ? 'bg-purple-50 text-purple-700' : c.score_breakdown.verification_level === 'BUSINESS' ? 'bg-blue-50 text-blue-700' : 'bg-slate-100 text-slate-500'"
              >
                🏷 {{ c.score_breakdown.verification_level }}
              </span>
            </div>
            <div v-if="c.unit_price_minor" class="mt-2 flex items-center gap-2 text-xs text-slate-500">
              <span class="text-sm font-bold text-slate-900">{{ formatCandidatePrice(c.unit_price_minor, c.currency || intent.currency) }}</span>
              <span>/ {{ c.unit || intent.unit }}</span>
              <span v-if="c.market_mode" class="rounded-full bg-slate-100 px-2 py-0.5 font-semibold text-slate-600">{{ c.market_mode }}</span>
              <span v-if="c.origin_country">{{ c.origin_country }}</span>
            </div>
          </div>

          <!-- Action -->
          <div class="flex flex-shrink-0 flex-col gap-2">
            <UButton size="xs" color="indigo" variant="solid" icon="i-heroicons-link" @click.stop="bindCandidate(c)">
              Bind
            </UButton>
            <UButton size="xs" color="indigo" variant="outline" icon="i-heroicons-eye" @click.stop="openCandidate(c)">
              Details
            </UButton>
            <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-shopping-bag" :to="`/marketplace/${c.catalog_item_id}`" @click.stop>
              Item
            </UButton>
            <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-table-cells" :to="`/buyer/requests/${intent.id}/offers`" @click.stop>
              Offers
            </UButton>
          </div>
        </div>
      </div>
    </UCard>
  </div>

  <div v-if="selectedCandidate" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-6" @click.self="selectedCandidate = null">
    <div class="w-full max-w-2xl rounded-2xl bg-white shadow-2xl">
      <div class="flex items-start justify-between border-b border-slate-100 p-6">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-indigo-600">Matched supplier detail</p>
          <h3 class="mt-1 text-xl font-bold text-slate-900">{{ selectedCandidate.company_name }}</h3>
          <p class="mt-1 text-sm text-slate-500">{{ selectedCandidate.catalog_item_title }}</p>
        </div>
        <UButton color="gray" variant="ghost" icon="i-heroicons-x-mark" @click="selectedCandidate = null" />
      </div>
      <div class="space-y-5 p-6">
        <div class="rounded-xl bg-indigo-50 px-4 py-3 text-sm font-medium text-indigo-800">
          {{ selectedCandidate.why_recommended || 'Matching category and buyer criteria.' }}
        </div>
        <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div class="rounded-xl border border-slate-100 p-3">
            <p class="text-xs text-slate-500">Rank score</p>
            <p class="mt-1 text-lg font-bold text-slate-900">{{ selectedCandidate.ranking_score }}pts</p>
          </div>
          <div class="rounded-xl border border-slate-100 p-3">
            <p class="text-xs text-slate-500">Price</p>
            <p class="mt-1 text-lg font-bold text-slate-900">{{ formatCandidatePrice(selectedCandidate.unit_price_minor || selectedCandidate.score_breakdown?.price_minor || 0, selectedCandidate.currency || intent.currency) }}</p>
          </div>
          <div class="rounded-xl border border-slate-100 p-3">
            <p class="text-xs text-slate-500">Distance</p>
            <p class="mt-1 text-lg font-bold text-slate-900">{{ selectedCandidate.score_breakdown?.distance_km ?? 'N/A' }}km</p>
          </div>
          <div class="rounded-xl border border-slate-100 p-3">
            <p class="text-xs text-slate-500">Deal rate</p>
            <p class="mt-1 text-lg font-bold text-slate-900">{{ Math.round((selectedCandidate.score_breakdown?.deal_completion_rate || 0) * 100) }}%</p>
          </div>
        </div>
        <div class="flex flex-wrap gap-2 text-xs">
          <span class="rounded-full bg-slate-100 px-3 py-1 text-slate-600">Category {{ selectedCandidate.score_breakdown?.category_match || 0 }}</span>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-slate-600">Trust {{ selectedCandidate.score_breakdown?.trust_score || 0 }}</span>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-slate-600">{{ selectedCandidate.score_breakdown?.verification_level || 'UNVERIFIED' }}</span>
          <span v-if="selectedCandidate.score_breakdown?.has_stock" class="rounded-full bg-green-50 px-3 py-1 text-green-700">In stock {{ selectedCandidate.score_breakdown?.stock_qty }}</span>
          <span v-if="selectedCandidate.score_breakdown?.bound_catalog_item" class="rounded-full bg-indigo-100 px-3 py-1 text-indigo-700">Bound item</span>
        </div>
        <div class="flex justify-end gap-3">
          <UButton color="gray" variant="outline" :to="`/marketplace/${selectedCandidate.catalog_item_id}`">View item</UButton>
          <UButton color="indigo" icon="i-heroicons-link" @click="bindCandidate(selectedCandidate)">Bind supplier</UButton>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="loading" class="flex justify-center p-12">
    <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 animate-spin text-slate-400" />
  </div>
</template>

<script setup lang="ts">
import { demoIntents, demoSupplierCandidatesForIntent, isDemoToken } from "~/utils/demoData";

definePageMeta({
  layout: 'buyer'
})

const route = useRoute()
const api = useApi()
const authStore = useAuthStore()
const config = useRuntimeConfig()
const id = route.params.id as string
const intent = ref<any>(null)
const loading = ref(true)

// Supplier candidates
const candidates = ref<any[]>([])
const candidatesLoading = ref(false)
const candidateSort = ref('comprehensive')
const selectedCandidate = ref<any | null>(null)

const fetchIntent = async () => {
  loading.value = true
  const { data, error } = await api.getIntent(id)
  if (data) {
    intent.value = data
    await fetchCandidates()
  } else if (authStore.isDemoMode && (isDemoToken(authStore.accessToken) || id.startsWith('demo-'))) {
    intent.value = demoIntents.find((row) => row.id === id) || null
    await fetchCandidates()
  } else {
    console.error(error)
    useToast().add({ title: 'Error fetching request details', color: 'red' })
  }
  loading.value = false
}

const fetchCandidates = async () => {
  if (!intent.value) return
  const demoEnabled = authStore.isDemoMode && (isDemoToken(authStore.accessToken) || id.startsWith('demo-'))
  if (demoEnabled) {
    candidates.value = sortDemoCandidates(demoSupplierCandidatesForIntent(id))
    return
  }
  candidatesLoading.value = true
  try {
    const data = await $fetch<any>(
      `${config.public.apiBase}/intents/${intent.value.id}/supplier-candidates?sort=${candidateSort.value}&limit=10`,
      { headers: { Authorization: `Bearer ${authStore.accessToken}` } }
    )
    candidates.value = data.candidates || []
  } catch {
    candidates.value = []
  } finally {
    candidatesLoading.value = false
  }
}

function sortDemoCandidates(list: any[]) {
  const copy = [...list]
  switch (candidateSort.value) {
    case 'cost': return copy.sort((a, b) => a.unit_price_minor - b.unit_price_minor)
    case 'trust': return copy.sort((a, b) => (b.trust_score || b.score_breakdown?.trust_score || 0) - (a.trust_score || a.score_breakdown?.trust_score || 0))
    case 'distance': return copy.sort((a, b) => (a.distance_km ?? a.score_breakdown?.distance_km ?? 9999) - (b.distance_km ?? b.score_breakdown?.distance_km ?? 9999))
    case 'delivery': return copy.sort((a, b) => (a.eta_days ?? 9999) - (b.eta_days ?? 9999))
    default: return copy.sort((a, b) => b.ranking_score - a.ranking_score)
  }
}

async function openCandidate(candidate: any) {
  selectedCandidate.value = candidate
  const demoEnabled = authStore.isDemoMode && (isDemoToken(authStore.accessToken) || id.startsWith('demo-'))
  if (demoEnabled) return
  try {
    selectedCandidate.value = await $fetch<any>(
      `${config.public.apiBase}/intents/${intent.value.id}/supplier-candidates/${candidate.catalog_item_id}?sort=${candidateSort.value}`,
      { headers: { Authorization: `Bearer ${authStore.accessToken}` } }
    )
  } catch {
    selectedCandidate.value = candidate
  }
}

async function bindCandidate(candidate: any) {
  try {
    const demoEnabled = authStore.isDemoMode && (isDemoToken(authStore.accessToken) || id.startsWith('demo-'))
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
      useToast().add({ title: 'Supplier bound for demo request', color: 'green' })
      return
    }
    const data = await $fetch<any>(
      `${config.public.apiBase}/intents/${intent.value.id}/supplier-candidates/${candidate.catalog_item_id}/bind`,
      {
        method: 'POST',
        body: { note: 'Buyer selected from matched suppliers panel' },
        headers: { Authorization: `Bearer ${authStore.accessToken}` },
      }
    )
    await fetchCandidates()
    selectedCandidate.value = data.candidate
    useToast().add({ title: 'Supplier bound to request', color: 'green' })
  } catch (e: any) {
    useToast().add({ title: e?.data?.detail || 'Bind failed', color: 'red' })
  }
}

onMounted(() => {
  fetchIntent()
})

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    'DRAFT': 'gray',
    'PUBLISHED': 'blue',
    'CLOSED': 'yellow',
    'COMPLETED': 'green',
    'CANCELLED': 'red'
  }
  return map[status] || 'gray'
}

function formatCandidatePrice(minor: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'PHP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(minor / 100)
}
</script>
