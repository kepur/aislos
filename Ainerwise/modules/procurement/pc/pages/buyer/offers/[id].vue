<template>
  <div class="space-y-6">
    <div class="flex items-center space-x-4 mb-2">
      <UButton :to="backTo" color="gray" variant="ghost" icon="i-heroicons-arrow-left" size="sm" />
      <div class="min-w-0">
        <h1 class="text-2xl font-bold text-slate-900 truncate">
          {{ offer ? `Offer from ${supplierLabel}` : 'Offer Detail' }}
        </h1>
        <p class="text-sm text-slate-500 mt-1">
          <span v-if="offer">Request {{ shortId(offer.intent_id) }}</span>
          <span v-if="offer?.catalog_item_id"> · Item {{ shortId(offer.catalog_item_id) }}</span>
        </p>
      </div>
    </div>

    <UCard v-if="loading" class="bg-white">
      <div class="flex justify-center py-12">
        <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 animate-spin text-slate-400" />
      </div>
    </UCard>

    <UCard v-else-if="loadError || !offer" class="bg-white">
      <div class="py-12 text-center">
        <h2 class="text-lg font-semibold text-slate-900">Offer not available</h2>
        <p class="mt-2 text-sm text-slate-500">{{ loadError || 'The offer could not be loaded from AinerWise Core.' }}</p>
        <UButton to="/buyer/requests" class="mt-5" color="indigo" variant="soft" icon="i-heroicons-arrow-left">
          Back to requests
        </UButton>
      </div>
    </UCard>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <UCard>
          <template #header>
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-lg font-medium text-slate-900">Quote Breakdown</h3>
              <UBadge :color="offerStatusColor(offer.status)" variant="subtle">{{ offer.status }}</UBadge>
            </div>
          </template>

          <div class="space-y-4">
            <div class="flex justify-between items-center py-2 border-b border-slate-100">
              <span class="text-slate-600">Unit Price ({{ offer.qty_available }} {{ offer.unit || 'units' }})</span>
              <span class="font-medium text-slate-900">{{ formatMinor(offer.unit_price_minor, offer.currency) }}</span>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-slate-100">
              <span class="text-slate-600">Subtotal</span>
              <span class="font-medium text-slate-900">{{ formatMinor(subtotalMinor, offer.currency) }}</span>
            </div>
            <div class="flex justify-between items-center py-2 border-b border-slate-100">
              <span class="text-slate-600">Delivery Fee</span>
              <span class="font-medium text-slate-900">{{ formatMinor(offer.delivery_fee_minor || 0, offer.currency) }}</span>
            </div>
            <div class="flex justify-between items-center py-3 bg-indigo-50 px-4 rounded-lg border border-indigo-100">
              <span class="font-bold text-indigo-900">Offer Total</span>
              <span class="text-xl font-bold text-indigo-700">{{ formatMinor(offer.total_price_minor, offer.currency) }}</span>
            </div>
          </div>

          <div class="mt-6 pt-6 border-t border-slate-200">
            <h4 class="text-sm font-semibold text-slate-900 mb-2">Supplier Notes</h4>
            <p class="text-sm text-slate-600 bg-slate-50 p-4 rounded-md border border-slate-200">
              {{ offer.message || 'No supplier notes provided.' }}
            </p>
          </div>
        </UCard>

        <UCard>
          <template #header>
            <h3 class="text-lg font-medium text-slate-900">Terms & Logistics</h3>
          </template>
          <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Estimated Arrival</dt>
              <dd class="mt-1 text-sm font-medium text-slate-900">{{ offer.eta_date ? formatDate(offer.eta_date) : 'Not specified' }}</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Stock Status</dt>
              <dd class="mt-1"><UBadge :color="stockColor(offer.stock_confidence)" variant="subtle">{{ offer.stock_confidence || 'UNKNOWN' }}</UBadge></dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Warranty</dt>
              <dd class="mt-1 text-sm text-slate-900">{{ offer.warranty || 'Not specified' }}</dd>
            </div>
            <div>
              <dt class="text-xs font-semibold text-slate-500 uppercase">Offer ID</dt>
              <dd class="mt-1 font-mono text-xs text-slate-600">{{ offer.id }}</dd>
            </div>
          </dl>
        </UCard>
      </div>

      <div class="space-y-6">
        <UCard>
          <div class="text-center">
            <UAvatar :text="supplierInitial" size="3xl" class="mx-auto" />
            <h3 class="mt-4 text-lg font-bold text-slate-900 flex justify-center items-center">
              {{ supplierLabel }}
              <UIcon name="i-heroicons-shield-check" class="w-5 h-5 text-green-500 ml-1" />
            </h3>
            <div class="text-sm text-slate-500 mt-1">Company {{ shortId(offer.company_id) }}</div>
            <div v-if="offer.catalog_item_id" class="text-sm text-slate-500 mt-1">Catalog item {{ shortId(offer.catalog_item_id) }}</div>
          </div>

          <div class="mt-6 space-y-3">
            <UButton
              block
              color="indigo"
              variant="solid"
              size="xl"
              class="font-bold shadow-md"
              :loading="awarding"
              :disabled="offer.status === 'AWARDED'"
              @click="award"
            >
              {{ offer.status === 'AWARDED' ? 'Awarded' : 'Award Order' }}
            </UButton>
            <UButton block color="gray" variant="outline" icon="i-heroicons-table-cells" :to="backTo">
              Compare Offers
            </UButton>
          </div>
        </UCard>

        <div class="bg-blue-50 border border-blue-100 rounded-lg p-4 flex items-start">
          <UIcon name="i-heroicons-shield-check" class="w-6 h-6 text-blue-600 mr-3 flex-shrink-0" />
          <div>
            <h4 class="text-sm font-bold text-blue-900">Milestone Payments</h4>
            <p class="text-xs text-blue-800 mt-1">
              If you award this offer, you'll agree a milestone plan for {{ formatMinor(offer.total_price_minor, offer.currency) }} and pay the supplier directly — confirming each milestone as work is delivered. The platform keeps the records, not your funds.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Offer } from '~/types'

definePageMeta({
  layout: 'buyer',
  middleware: ['buyer']
})

const route = useRoute()
const api = useApi()
const offerId = route.params.id as string

const offer = ref<Offer | null>(null)
const loading = ref(true)
const awarding = ref(false)
const loadError = ref('')

const backTo = computed(() => offer.value?.intent_id ? `/buyer/requests/${offer.value.intent_id}/offers` : '/buyer/requests')
const supplierLabel = computed(() => offer.value?.company_name || `Supplier ${shortId(offer.value?.company_id)}`)
const supplierInitial = computed(() => supplierLabel.value.slice(0, 1).toUpperCase())
const subtotalMinor = computed(() => {
  if (!offer.value) return 0
  return Math.max(0, Number(offer.value.total_price_minor || 0) - Number(offer.value.delivery_fee_minor || 0))
})

async function loadOffer() {
  loading.value = true
  loadError.value = ''
  const { data, error } = await api.getOffer(offerId)
  if (data) {
    offer.value = data as Offer
  } else {
    offer.value = null
    loadError.value = extractErrorMessage(error, 'Offer request failed.')
  }
  loading.value = false
}

async function award() {
  if (!offer.value) return
  if (!window.confirm(`Award this offer for ${formatMinor(offer.value.total_price_minor, offer.value.currency)}?`)) return
  awarding.value = true
  const { data, error } = await api.awardOffer(offer.value.id)
  awarding.value = false
  if (error) {
    useToast().add({ title: 'Could not award offer', description: extractErrorMessage(error, 'Award failed.'), color: 'red' })
    return
  }
  useToast().add({ title: 'Offer awarded', description: 'Order created and supplier notified.', color: 'green' })
  const orderId = (data as any)?.id
  navigateTo(orderId ? `/buyer/orders/${orderId}` : '/buyer/orders')
}

function shortId(value?: string) {
  return value ? `#${String(value).slice(0, 8)}` : '—'
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

function extractErrorMessage(error: any, fallback: string) {
  return error?.detail || error?.data?.detail || error?.message || fallback
}

onMounted(loadOffer)
</script>
