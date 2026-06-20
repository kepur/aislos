<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Pricing Intelligence & Analytics</h1>
        <p class="mt-1 text-sm text-slate-500">Live procurement pricing signals from AinerWise Core.</p>
      </div>
      <UButton icon="i-heroicons-arrow-path" color="gray" variant="ghost" :loading="loading" @click="loadData">
        Refresh
      </UButton>
    </div>

    <UAlert
      v-if="error"
      color="red"
      variant="soft"
      icon="i-heroicons-exclamation-triangle"
      :title="error"
    />

    <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
      <UCard v-for="metric in metrics" :key="metric.label">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ metric.label }}</p>
        <p class="mt-2 text-2xl font-extrabold text-slate-900">{{ metric.value }}</p>
        <p class="mt-1 text-xs text-slate-500">{{ metric.note }}</p>
      </UCard>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <UCard>
        <template #header>
          <h3 class="font-medium text-slate-900">Offer Status Price Distribution</h3>
        </template>
        <div v-if="loading" class="space-y-3">
          <USkeleton v-for="n in 4" :key="n" class="h-10 w-full" />
        </div>
        <div v-else-if="offerDistribution.length === 0" class="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
          No submitted offers yet.
        </div>
        <div v-else class="space-y-4">
          <div v-for="row in offerDistribution" :key="row.status">
            <div class="mb-1 flex items-center justify-between text-sm">
              <span class="font-medium text-slate-700">{{ row.status }}</span>
              <span class="text-slate-500">{{ row.count }} offers · {{ formatMinor(row.average_minor, row.currency) }} avg</span>
            </div>
            <div class="h-3 overflow-hidden rounded-full bg-slate-100">
              <div class="h-full rounded-full bg-indigo-500" :style="{ width: `${row.width}%` }"></div>
            </div>
          </div>
        </div>
      </UCard>

      <UCard>
        <template #header>
          <h3 class="font-medium text-slate-900">Request Volume By Status</h3>
        </template>
        <div v-if="loading" class="space-y-3">
          <USkeleton v-for="n in 4" :key="n" class="h-10 w-full" />
        </div>
        <div v-else-if="intentDistribution.length === 0" class="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
          No buyer requests yet.
        </div>
        <div v-else class="space-y-4">
          <div v-for="row in intentDistribution" :key="row.status">
            <div class="mb-1 flex items-center justify-between text-sm">
              <span class="font-medium text-slate-700">{{ row.status }}</span>
              <span class="text-slate-500">{{ row.count }} requests</span>
            </div>
            <div class="h-3 overflow-hidden rounded-full bg-slate-100">
              <div class="h-full rounded-full bg-emerald-500" :style="{ width: `${row.width}%` }"></div>
            </div>
          </div>
        </div>
      </UCard>
    </div>

    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-medium text-slate-900">Budget Variance Signals</h3>
          <span class="text-xs text-slate-400">Calculated from real offers vs buyer budget</span>
        </div>
      </template>
      <UTable :columns="columns" :rows="varianceRows" :loading="loading">
        <template #request-data="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ row.request }}</p>
            <p class="text-xs text-slate-400">Intent {{ row.intent_id }}</p>
          </div>
        </template>
        <template #budget-data="{ row }">
          <span class="font-medium text-slate-700">{{ row.budget }}</span>
        </template>
        <template #quote-data="{ row }">
          <span class="font-medium text-slate-700">{{ row.quote }}</span>
        </template>
        <template #variance-data="{ row }">
          <span :class="row.variance_minor > 0 ? 'text-red-600' : 'text-green-600'" class="font-medium">
            {{ row.variance }}
          </span>
        </template>
      </UTable>
      <div v-if="!loading && varianceRows.length === 0" class="mt-4 rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
        No budget variance signals yet.
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })

type OfferRow = {
  id: string
  intent_id: string
  total_price_minor: number
  currency: string
  status: string
}

type IntentRow = {
  id: string
  title: string
  budget_max_minor?: number
  currency: string
  status: string
}

const config = useRuntimeConfig()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref('')
const offers = ref<OfferRow[]>([])
const intents = ref<IntentRow[]>([])

const columns = [
  { key: 'request', label: 'Request' },
  { key: 'budget', label: 'Buyer Budget' },
  { key: 'quote', label: 'Offer Quote' },
  { key: 'variance', label: 'Variance' },
  { key: 'status', label: 'Offer Status' },
]

const intentMap = computed(() => new Map(intents.value.map((intent) => [String(intent.id), intent])))
const totalOfferMinor = computed(() => offers.value.reduce((sum, offer) => sum + Number(offer.total_price_minor || 0), 0))
const averageOfferMinor = computed(() => offers.value.length ? Math.round(totalOfferMinor.value / offers.value.length) : 0)
const awardedCount = computed(() => offers.value.filter((offer) => offer.status === 'AWARDED').length)
const defaultCurrency = computed(() => offers.value[0]?.currency || intents.value[0]?.currency || 'PHP')

const metrics = computed(() => [
  { label: 'Offers', value: String(offers.value.length), note: 'Submitted supplier offers' },
  { label: 'Buyer Requests', value: String(intents.value.length), note: 'Procurement intents in Core' },
  { label: 'Average Quote', value: averageOfferMinor.value ? formatMinor(averageOfferMinor.value, defaultCurrency.value) : 'N/A', note: 'Across loaded offers' },
  { label: 'Award Rate', value: offers.value.length ? `${Math.round((awardedCount.value / offers.value.length) * 100)}%` : 'N/A', note: `${awardedCount.value} awarded offers` },
])

const offerDistribution = computed(() => {
  const grouped = new Map<string, { count: number; total: number; currency: string }>()
  for (const offer of offers.value) {
    const key = offer.status || 'UNKNOWN'
    const row = grouped.get(key) || { count: 0, total: 0, currency: offer.currency || defaultCurrency.value }
    row.count += 1
    row.total += Number(offer.total_price_minor || 0)
    grouped.set(key, row)
  }
  const maxAverage = Math.max(1, ...Array.from(grouped.values()).map((row) => row.total / Math.max(1, row.count)))
  return Array.from(grouped.entries()).map(([status, row]) => {
    const average = Math.round(row.total / Math.max(1, row.count))
    return {
      status,
      count: row.count,
      currency: row.currency,
      average_minor: average,
      width: Math.max(6, Math.round((average / maxAverage) * 100)),
    }
  })
})

const intentDistribution = computed(() => {
  const grouped = new Map<string, number>()
  for (const intent of intents.value) {
    const key = intent.status || 'UNKNOWN'
    grouped.set(key, (grouped.get(key) || 0) + 1)
  }
  const maxCount = Math.max(1, ...grouped.values())
  return Array.from(grouped.entries()).map(([status, count]) => ({
    status,
    count,
    width: Math.max(6, Math.round((count / maxCount) * 100)),
  }))
})

const varianceRows = computed(() => {
  return offers.value
    .map((offer) => {
      const intent = intentMap.value.get(String(offer.intent_id))
      const budget = Number(intent?.budget_max_minor || 0)
      if (!intent || !budget) return null
      const quote = Number(offer.total_price_minor || 0)
      const variance = quote - budget
      const variancePct = budget ? Math.round((variance / budget) * 100) : 0
      return {
        request: intent.title,
        intent_id: String(intent.id).slice(0, 8),
        budget: formatMinor(budget, intent.currency || offer.currency),
        quote: formatMinor(quote, offer.currency),
        variance: `${variancePct > 0 ? '+' : ''}${variancePct}%`,
        variance_minor: variance,
        status: offer.status,
      }
    })
    .filter(Boolean)
    .sort((a: any, b: any) => Math.abs(b.variance_minor) - Math.abs(a.variance_minor))
    .slice(0, 20)
})

function normalizeList(data: any) {
  if (Array.isArray(data)) return data
  return data?.items || data?.offers || data?.intents || []
}

function formatMinor(amountMinor: number, currency = 'PHP') {
  try {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amountMinor / 100)
  } catch {
    return `${(amountMinor / 100).toLocaleString()} ${currency}`
  }
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const headers = { Authorization: `Bearer ${authStore.accessToken}` }
    const [offerData, intentData] = await Promise.all([
      $fetch<any>(`${config.public.apiBase}/admin/offers`, { params: { limit: 500 }, headers }),
      $fetch<any>(`${config.public.apiBase}/admin/intents`, { params: { limit: 500 }, headers }),
    ])
    offers.value = normalizeList(offerData)
    intents.value = normalizeList(intentData)
  } catch (e: any) {
    offers.value = []
    intents.value = []
    const detail = e?.data?.detail
    error.value = typeof detail === 'string' ? detail : 'Failed to load pricing intelligence.'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
