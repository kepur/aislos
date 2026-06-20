<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Platform Offers</h1>
        <p class="mt-1 text-sm text-slate-500">Live supplier offers from AinerWise Core.</p>
      </div>
      <UButton icon="i-heroicons-arrow-path" color="gray" variant="ghost" :loading="loading" @click="loadOffers">
        Refresh
      </UButton>
    </div>

    <UCard>
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <UInput
          v-model="keyword"
          icon="i-heroicons-magnifying-glass"
          placeholder="Search offer, intent, or company id..."
          class="max-w-sm"
        />
        <div class="flex items-center gap-3">
          <USelect
            v-model="statusFilter"
            :options="statusOptions"
            option-attribute="label"
            value-attribute="value"
            class="w-44"
          />
          <span class="text-sm text-slate-500">{{ filteredOffers.length }} / {{ offers.length }} offers</span>
        </div>
      </div>

      <UAlert
        v-if="error"
        color="red"
        variant="soft"
        icon="i-heroicons-exclamation-triangle"
        class="mb-4"
        :title="error"
      />

      <UTable :columns="columns" :rows="filteredOffers" :loading="loading">
        <template #id-data="{ row }">
          <span class="font-mono text-xs text-slate-600">{{ shortId(row.id) }}</span>
        </template>
        <template #supplier-data="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ shortId(row.company_id) }}</p>
            <p class="text-xs text-slate-400">Supplier company id</p>
          </div>
        </template>
        <template #intent_id-data="{ row }">
          <span class="font-mono text-xs text-indigo-600">{{ shortId(row.intent_id) }}</span>
        </template>
        <template #amount-data="{ row }">
          <span class="font-medium text-slate-900">{{ formatMinor(row.total_price_minor, row.currency) }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #date-data="{ row }">
          <span class="text-xs text-slate-500">{{ formatDate(row.created_at) }}</span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex items-center gap-2">
            <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-eye" @click="selectedOffer = row">
              Details
            </UButton>
            <UButton
              size="xs"
              color="red"
              variant="soft"
              :disabled="row.status === 'AWARDED'"
              @click="removeOffer(row)"
            >
              Remove
            </UButton>
          </div>
        </template>
      </UTable>

      <div v-if="!loading && filteredOffers.length === 0" class="mt-4 rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
        No offers match the current filters.
      </div>
    </UCard>

    <UCard v-if="selectedOffer">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-medium text-slate-900">Offer Details</h3>
          <UButton size="xs" color="gray" variant="ghost" @click="selectedOffer = null">Close</UButton>
        </div>
      </template>
      <dl class="grid grid-cols-1 gap-4 text-sm md:grid-cols-3">
        <div>
          <dt class="text-slate-400">Offer ID</dt>
          <dd class="font-mono text-slate-800">{{ selectedOffer.id }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Intent ID</dt>
          <dd class="font-mono text-slate-800">{{ selectedOffer.intent_id }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Catalog Item</dt>
          <dd class="font-mono text-slate-800">{{ selectedOffer.catalog_item_id || 'N/A' }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Unit Price</dt>
          <dd class="font-medium text-slate-800">{{ formatMinor(selectedOffer.unit_price_minor, selectedOffer.currency) }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Delivery Fee</dt>
          <dd class="font-medium text-slate-800">{{ formatMinor(selectedOffer.delivery_fee_minor, selectedOffer.currency) }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Warranty</dt>
          <dd class="text-slate-800">{{ selectedOffer.warranty || 'N/A' }}</dd>
        </div>
      </dl>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })

type OfferRow = {
  id: string
  intent_id: string
  company_id: string
  catalog_item_id?: string
  unit_price_minor: number
  delivery_fee_minor: number
  total_price_minor: number
  currency: string
  warranty?: string
  status: string
  created_at: string
}

const config = useRuntimeConfig()
const authStore = useAuthStore()
const toast = useToast()

const loading = ref(false)
const error = ref('')
const keyword = ref('')
const statusFilter = ref('')
const offers = ref<OfferRow[]>([])
const selectedOffer = ref<OfferRow | null>(null)

const columns = [
  { key: 'id', label: 'Offer ID' },
  { key: 'supplier', label: 'Supplier Org' },
  { key: 'intent_id', label: 'Intent ID' },
  { key: 'amount', label: 'Quote Amount' },
  { key: 'status', label: 'Status' },
  { key: 'date', label: 'Date' },
  { key: 'actions', label: 'Actions' }
]

const statusOptions = [
  { label: 'All Statuses', value: '' },
  { label: 'Submitted', value: 'SUBMITTED' },
  { label: 'Awarded', value: 'AWARDED' },
  { label: 'Rejected', value: 'REJECTED' },
  { label: 'Withdrawn', value: 'WITHDRAWN' },
  { label: 'Expired', value: 'EXPIRED' },
]

const filteredOffers = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return offers.value.filter((offer) => {
    const matchesStatus = !statusFilter.value || offer.status === statusFilter.value
    const haystack = [
      offer.id,
      offer.intent_id,
      offer.company_id,
      offer.catalog_item_id,
      offer.status,
      offer.currency,
      offer.warranty,
    ].filter(Boolean).join(' ').toLowerCase()
    return matchesStatus && (!q || haystack.includes(q))
  })
})

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    DRAFT: 'gray',
    SUBMITTED: 'yellow',
    AWARDED: 'green',
    REJECTED: 'red',
    WITHDRAWN: 'gray',
    EXPIRED: 'yellow',
    REMOVED: 'red',
  }
  return map[status] || 'gray'
}

function normalizeList(data: any): OfferRow[] {
  if (Array.isArray(data)) return data
  return data?.items || data?.offers || []
}

function shortId(value?: string) {
  return value ? String(value).slice(0, 8) : 'N/A'
}

function formatDate(value?: string) {
  if (!value) return 'N/A'
  try {
    return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
  } catch {
    return value
  }
}

function formatMinor(amountMinor: number, currency = 'PHP') {
  try {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(Number(amountMinor || 0) / 100)
  } catch {
    return `${(Number(amountMinor || 0) / 100).toLocaleString()} ${currency}`
  }
}

async function loadOffers() {
  loading.value = true
  error.value = ''
  try {
    const headers = { Authorization: `Bearer ${authStore.accessToken}` }
    const data = await $fetch<any>(`${config.public.apiBase}/admin/offers`, {
      params: { limit: 500 },
      headers,
    })
    offers.value = normalizeList(data)
    if (selectedOffer.value && !offers.value.some((offer) => offer.id === selectedOffer.value?.id)) {
      selectedOffer.value = null
    }
  } catch (e: any) {
    offers.value = []
    selectedOffer.value = null
    const detail = e?.data?.detail
    error.value = typeof detail === 'string' ? detail : 'Failed to load platform offers.'
  } finally {
    loading.value = false
  }
}

async function removeOffer(row: OfferRow) {
  if (row.status === 'AWARDED') return
  const reason = import.meta.client ? window.prompt(`Reason for removing offer ${shortId(row.id)}:`) : ''
  if (!reason) return
  try {
    await $fetch(`${config.public.apiBase}/admin/offers/${row.id}/remove`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
      body: { reason },
    })
    toast.add({ title: 'Offer removed', color: 'green' })
    await loadOffers()
  } catch (e: any) {
    const detail = e?.data?.detail
    toast.add({ title: typeof detail === 'string' ? detail : 'Failed to remove offer', color: 'red' })
  }
}

onMounted(loadOffers)
</script>
