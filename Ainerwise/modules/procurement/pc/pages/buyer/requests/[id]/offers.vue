<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between gap-4 mb-2">
      <div class="flex items-center space-x-4 min-w-0">
        <UButton :to="`/buyer/requests/${requestId}`" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" class="mb-1" />
        <div class="min-w-0">
          <div class="flex items-center space-x-3 min-w-0">
            <h1 class="text-2xl font-bold text-slate-900 truncate">{{ intent?.title || 'Compare Offers' }}</h1>
            <UBadge v-if="intent" :color="getIntentStatusColor(intent.status)" variant="subtle">{{ getIntentStatusLabel(intent.status) }}</UBadge>
          </div>
          <p class="text-sm text-slate-500 mt-1">
            Request ID: #{{ requestId.slice(0, 8) }}
            <span v-if="intent"> • {{ budgetLabel }} • {{ locationLabel }}</span>
          </p>
        </div>
      </div>

      <div class="text-right">
        <div class="text-3xl font-bold text-indigo-600">{{ offers.length }}</div>
        <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Offers Received</div>
      </div>
    </div>

    <UCard class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-4' } }">
      <div class="flex flex-wrap items-center gap-4">
        <div class="text-sm font-medium text-slate-700 mr-2 flex items-center">
          <UIcon name="i-heroicons-funnel" class="w-4 h-4 mr-1" /> Filters:
        </div>
        <USelect v-model="filters.sort" :options="sortOptions" size="sm" class="w-52" />
        <USelect v-model="filters.eta" :options="etaOptions" size="sm" class="w-36" />
        <label class="flex items-center gap-2 cursor-pointer select-none">
          <input v-model="filters.inStock" type="checkbox" class="w-4 h-4 rounded border-slate-300 accent-indigo-600 cursor-pointer" />
          <span class="text-sm text-slate-700">Firm Stock Only</span>
        </label>
      </div>
    </UCard>

    <UCard v-if="loading" class="bg-white">
      <div class="flex justify-center py-10">
        <UIcon name="i-heroicons-arrow-path" class="w-7 h-7 animate-spin text-slate-400" />
      </div>
    </UCard>

    <UCard v-else-if="offers.length === 0" class="bg-white">
      <div class="text-center py-12">
        <div class="text-4xl mb-3">⏳</div>
        <h3 class="font-semibold text-slate-900">No offers yet</h3>
        <p class="text-sm text-slate-500 mt-1">When suppliers submit quotes, PC and H5 will show the same backend data here.</p>
      </div>
    </UCard>

    <div v-else class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-x-auto">
      <UTable :columns="columns" :rows="filteredOffers" class="min-w-max">
        <template #supplier-data="{ row }">
          <div class="flex items-center space-x-3">
            <UAvatar :text="supplierInitial(row)" size="sm" />
            <div>
              <div class="font-semibold text-slate-900 flex items-center">
                {{ supplierLabel(row) }}
                <UIcon v-if="row.status === 'AWARDED'" name="i-heroicons-check-badge" class="w-4 h-4 text-green-500 ml-1" title="Awarded Offer" />
              </div>
              <div class="flex items-center text-xs text-slate-500 mt-1">
                <span>{{ shortId(row.company_id) }}</span>
                <span v-if="row.catalog_item_id" class="mx-1">•</span>
                <span v-if="row.catalog_item_id">Item {{ shortId(row.catalog_item_id) }}</span>
              </div>
            </div>
          </div>
        </template>

        <template #unitPrice-data="{ row }">
          <div class="text-sm font-medium text-slate-700">{{ formatMinor(row.unit_price_minor, row.currency) }}</div>
        </template>

        <template #deliveryFee-data="{ row }">
          <div class="text-sm font-medium text-slate-700">{{ formatMinor(row.delivery_fee_minor || 0, row.currency) }}</div>
        </template>

        <template #estimatedShipping-data="{ row }">
          <div class="text-sm font-medium text-primary-700">
            <span v-if="shippingLoadingMap[row.id]">Calculating...</span>
            <span v-else-if="shippingMap[row.id]">{{ formatMinor(shippingMap[row.id]!.total_shipping_minor, shippingMap[row.id]!.currency) }}</span>
            <span v-else>—</span>
          </div>
        </template>

        <template #totalCost-data="{ row }">
          <div class="text-lg font-bold text-indigo-700">{{ formatMinor(row.total_price_minor, row.currency) }}</div>
        </template>

        <template #landedWithShipping-data="{ row }">
          <div class="text-sm font-bold text-primary-800">
            {{ landedTotalLabel(row) }}
          </div>
          <div v-if="shippingMap[row.id]" class="text-[11px] text-primary-600 mt-0.5">
            ETA {{ shippingMap[row.id]!.estimated_days_min }}-{{ shippingMap[row.id]!.estimated_days_max }}d
          </div>
        </template>

        <template #eta-data="{ row }">
          <div class="text-sm font-medium text-slate-900">{{ row.eta_date ? formatDate(row.eta_date) : '—' }}</div>
        </template>

        <template #stock-data="{ row }">
          <UBadge :color="stockColor(row.stock_confidence)" variant="subtle" size="sm">
            {{ row.stock_confidence || 'UNKNOWN' }}
          </UBadge>
        </template>

        <template #warranty-data="{ row }">
          <div class="text-sm text-slate-600">{{ row.warranty || '—' }}</div>
        </template>

        <template #status-data="{ row }">
          <UBadge :color="offerStatusColor(row.status)" variant="subtle" size="sm">{{ row.status }}</UBadge>
        </template>

        <template #actions-data="{ row }">
          <div class="flex items-center space-x-2">
            <UButton size="sm" color="gray" variant="outline" :to="`/buyer/offers/${row.id}`">View</UButton>
            <UButton
              size="sm"
              color="green"
              variant="solid"
              class="font-bold"
              :disabled="intent?.status !== 'ACTIVE' || row.status === 'AWARDED'"
              @click="awardOffer(row)"
            >
              {{ row.status === 'AWARDED' ? 'Awarded' : 'Award' }}
            </UButton>
          </div>
        </template>
      </UTable>
    </div>

    <div v-if="offers.length > 0" class="bg-blue-50 border border-blue-100 rounded-lg p-4 flex items-start mt-6">
      <UIcon name="i-heroicons-light-bulb" class="w-6 h-6 text-blue-500 mr-3 flex-shrink-0 mt-0.5" />
      <div>
        <h4 class="text-sm font-bold text-blue-900">Price Intelligence</h4>
        <p class="text-sm text-blue-800 mt-1">
          Average supplier quote is <strong>{{ averageOfferLabel }}</strong>. Sort by landed cost, ETA, or stock to pick the best offer for this request.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Intent, Offer } from '~/types'

definePageMeta({
  layout: 'buyer'
})

type ShippingEstimate = {
  total_shipping_minor: number
  estimated_days_min: number
  estimated_days_max: number
  currency: string
}

const route = useRoute()
const api = useApi()
const requestId = route.params.id as string
const intent = ref<Intent | null>(null)
const offers = ref<Offer[]>([])
const loading = ref(true)
const shippingMap = ref<Record<string, ShippingEstimate | null>>({})
const shippingLoadingMap = ref<Record<string, boolean>>({})

const filters = ref({
  sort: 'Sort: Lowest Landed Cost',
  eta: 'ETA: Any',
  inStock: false
})

const sortOptions = ['Sort: Lowest Landed Cost', 'Sort: Lowest Offer', 'Sort: Fastest ETA', 'Sort: Firm Stock']
const etaOptions = ['ETA: Any', 'ETA: Today', 'ETA: 1-2 Days', 'ETA: This Week']

const columns = [
  { key: 'supplier', label: 'Supplier' },
  { key: 'unitPrice', label: 'Unit Price' },
  { key: 'deliveryFee', label: 'Delivery Fee' },
  { key: 'estimatedShipping', label: 'Estimated Shipping' },
  { key: 'totalCost', label: 'Offer Total', class: 'bg-indigo-50/30' },
  { key: 'landedWithShipping', label: 'Landed Total', class: 'bg-primary-50/30' },
  { key: 'eta', label: 'ETA' },
  { key: 'stock', label: 'Stock' },
  { key: 'warranty', label: 'Warranty' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const filteredOffers = computed(() => {
  let rows = [...offers.value]
  if (filters.value.inStock) {
    rows = rows.filter((offer) => offer.stock_confidence === 'FIRM')
  }
  if (filters.value.eta !== 'ETA: Any') {
    rows = rows.filter((offer) => {
      const days = etaDays(offer)
      if (days == null) return false
      if (filters.value.eta === 'ETA: Today') return days <= 0
      if (filters.value.eta === 'ETA: 1-2 Days') return days <= 2
      if (filters.value.eta === 'ETA: This Week') return days <= 7
      return true
    })
  }
  rows.sort((a, b) => {
    if (filters.value.sort === 'Sort: Lowest Offer') return a.total_price_minor - b.total_price_minor
    if (filters.value.sort === 'Sort: Fastest ETA') return (etaDays(a) ?? 9999) - (etaDays(b) ?? 9999)
    if (filters.value.sort === 'Sort: Firm Stock') return stockRank(b.stock_confidence) - stockRank(a.stock_confidence)
    return landedMinor(a) - landedMinor(b)
  })
  return rows
})

const budgetLabel = computed(() => {
  if (!intent.value) return ''
  if (intent.value.budget_min_minor || intent.value.budget_max_minor) {
    const min = intent.value.budget_min_minor ? formatMinor(intent.value.budget_min_minor, intent.value.currency) : 'Open'
    const max = intent.value.budget_max_minor ? formatMinor(intent.value.budget_max_minor, intent.value.currency) : 'Max'
    return `${min} - ${max}`
  }
  return 'Open budget'
})

const locationLabel = computed(() => {
  if (!intent.value) return ''
  return [intent.value.city, intent.value.country].filter(Boolean).join(', ') || 'No delivery area'
})

const averageOfferLabel = computed(() => {
  if (offers.value.length === 0) return '—'
  const total = offers.value.reduce((sum, offer) => sum + Number(offer.total_price_minor || 0), 0)
  return formatMinor(Math.round(total / offers.value.length), offers.value[0]?.currency || intent.value?.currency || 'PHP')
})

async function loadData() {
  loading.value = true
  const [intentResult, offersResult] = await Promise.all([
    api.getIntent(requestId),
    api.getOffersForIntent(requestId)
  ])

  if (intentResult.data) intent.value = intentResult.data as Intent
  else useToast().add({ title: 'Error fetching request details', color: 'red' })

  if (offersResult.data && Array.isArray(offersResult.data)) offers.value = offersResult.data as Offer[]
  else offers.value = []

  loading.value = false
  await Promise.all(offers.value.map((offer) => fetchEstimateForOffer(offer)))
}

function landedMinor(offer: Offer) {
  return Number(offer.total_price_minor || 0) + Number(shippingMap.value[offer.id]?.total_shipping_minor || 0)
}

function etaDays(offer: Offer) {
  if (!offer.eta_date) return null
  const eta = new Date(offer.eta_date).getTime()
  if (!Number.isFinite(eta)) return null
  return Math.ceil((eta - Date.now()) / 86400000)
}

function stockRank(stock?: string) {
  return { FIRM: 3, BACKORDER: 2, UNKNOWN: 1 }[stock || 'UNKNOWN'] || 0
}

function shortId(value?: string) {
  return value ? `#${String(value).slice(0, 8)}` : '—'
}

function supplierLabel(offer: Offer) {
  return offer.company_name || `Supplier ${shortId(offer.company_id)}`
}

function supplierInitial(offer: Offer) {
  return supplierLabel(offer).slice(0, 1).toUpperCase()
}

function getIntentStatusColor(status: string) {
  return {
    DRAFT: 'gray',
    ACTIVE: 'blue',
    AWARDED: 'green',
    CLOSED: 'gray',
    CANCELED: 'red',
    EXPIRED: 'red'
  }[status] || 'gray'
}

function offerStatusColor(status: string) {
  return {
    SUBMITTED: 'blue',
    VIEWED: 'blue',
    SHORTLISTED: 'yellow',
    AWARDED: 'green',
    REJECTED: 'gray',
    WITHDRAWN: 'gray',
    EXPIRED: 'red'
  }[status] || 'gray'
}

function stockColor(stock?: string) {
  return { FIRM: 'green', BACKORDER: 'yellow', UNKNOWN: 'gray' }[stock || 'UNKNOWN'] || 'gray'
}

function formatMinor(minor: number, currency = 'PHP') {
  const amount = Number(minor || 0) / 100
  if (currency === 'USDT') return `${amount.toLocaleString('en-PH', { maximumFractionDigits: 2 })} USDT`
  try {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(amount)
  } catch {
    return `${amount.toLocaleString('en-PH', { maximumFractionDigits: 2 })} ${currency}`
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-PH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

async function fetchEstimateForOffer(offer: Offer) {
  shippingLoadingMap.value[offer.id] = true
  try {
    const country = intent.value?.country || 'PH'
    const res = await useApiFetch()<{
      estimates: ShippingEstimate[]
    }>('/shipping/estimate', {
      method: 'POST',
      body: {
        origin_country: country,
        dest_country: country,
        weight_kg: resolveWeightKg(),
        declared_value_minor: offer.total_price_minor,
        currency: offer.currency || intent.value?.currency || 'PHP'
      }
    })
    shippingMap.value[offer.id] = res.estimates?.[0] || null
  } catch {
    shippingMap.value[offer.id] = null
  } finally {
    shippingLoadingMap.value[offer.id] = false
  }
}

function resolveWeightKg() {
  const attrs = (intent.value?.attrs_jsonb || {}) as Record<string, unknown>
  const unitWeight = Number(attrs.unit_weight_kg ?? attrs.weight_kg ?? 0)
  if (Number.isFinite(unitWeight) && unitWeight > 0) return unitWeight
  return Math.max(1, Math.min(Number(intent.value?.qty || 1), 20000))
}

function landedTotalLabel(offer: Offer) {
  return formatMinor(landedMinor(offer), shippingMap.value[offer.id]?.currency || offer.currency)
}

async function awardOffer(offer: Offer) {
  if (!window.confirm(`Award this offer for ${formatMinor(offer.total_price_minor, offer.currency)}? This will create an order and notify the supplier.`)) return
  const { error } = await api.awardOffer(offer.id)
  if (error) {
    useToast().add({ title: 'Could not award offer', description: String(error?.detail || error), color: 'red' })
    return
  }
  useToast().add({ title: 'Offer awarded', description: 'Order created and supplier notified.', color: 'green' })
  await loadData()
  navigateTo('/buyer/orders')
}

onMounted(loadData)
</script>
