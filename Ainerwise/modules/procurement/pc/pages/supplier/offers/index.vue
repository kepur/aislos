<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">My Offers</h1>
        <p class="mt-1 text-sm text-slate-500">Offers submitted by your supplier company.</p>
      </div>
      <div class="flex items-center gap-3">
        <UButton icon="i-heroicons-arrow-path" color="gray" variant="ghost" :loading="offerStore.loading" @click="loadOffers">
          Refresh
        </UButton>
        <UButton to="/supplier/inbox" color="indigo" variant="soft">View Pings</UButton>
      </div>
    </div>

    <UCard>
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <UInput
          v-model="keyword"
          icon="i-heroicons-magnifying-glass"
          placeholder="Search offer, intent, catalog, warranty..."
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

      <UTable :columns="columns" :rows="filteredOffers" :loading="offerStore.loading">
        <template #id-data="{ row }">
          <span class="font-mono text-xs text-slate-600">{{ shortId(row.id) }}</span>
        </template>
        <template #intent-data="{ row }">
          <div>
            <p class="font-mono text-xs text-indigo-600">{{ shortId(row.intent_id) }}</p>
            <p class="text-xs text-slate-400">Catalog {{ shortId(row.catalog_item_id) }}</p>
          </div>
        </template>
        <template #date-data="{ row }">
          <span class="text-xs text-slate-500">{{ formatDate(row.created_at) }}</span>
        </template>
        <template #amount-data="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ formatPrice(row.total_price_minor, row.currency) }}</p>
            <p class="text-xs text-slate-400">{{ row.qty_available }} available · {{ row.tier || 'CUSTOM' }}</p>
          </div>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex items-center gap-2">
            <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-eye" @click="selectedOffer = row">
              Details
            </UButton>
            <UButton
              v-if="canWithdraw(row.status)"
              size="xs"
              color="red"
              variant="soft"
              @click="withdrawOffer(row)"
            >
              Withdraw
            </UButton>
          </div>
        </template>
      </UTable>

      <div v-if="!offerStore.loading && filteredOffers.length === 0" class="mt-4 rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
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
          <dd class="font-medium text-slate-800">{{ formatPrice(selectedOffer.unit_price_minor, selectedOffer.currency) }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Delivery Fee</dt>
          <dd class="font-medium text-slate-800">{{ formatPrice(selectedOffer.delivery_fee_minor, selectedOffer.currency) }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Warranty</dt>
          <dd class="text-slate-800">{{ selectedOffer.warranty || 'N/A' }}</dd>
        </div>
      </dl>
      <p v-if="selectedOffer.message" class="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
        {{ selectedOffer.message }}
      </p>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import type { Offer } from '~/types'

definePageMeta({ layout: 'supplier' })

const offerStore = useOfferStore()
const toast = useToast()
const { formatPrice } = useApiUtils()

const keyword = ref('')
const statusFilter = ref('')
const error = ref('')
const selectedOffer = ref<Offer | null>(null)

const columns = [
  { key: 'id', label: 'Offer ID' },
  { key: 'intent', label: 'Intent / Catalog' },
  { key: 'date', label: 'Submitted Date' },
  { key: 'amount', label: 'Quote Amount' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const statusOptions = [
  { label: 'All Statuses', value: '' },
  { label: 'Submitted', value: 'SUBMITTED' },
  { label: 'Viewed', value: 'VIEWED' },
  { label: 'Shortlisted', value: 'SHORTLISTED' },
  { label: 'Awarded', value: 'AWARDED' },
  { label: 'Rejected', value: 'REJECTED' },
  { label: 'Withdrawn', value: 'WITHDRAWN' },
  { label: 'Expired', value: 'EXPIRED' },
]

const offers = computed(() => offerStore.myOffers)
const filteredOffers = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return offers.value.filter((offer) => {
    const matchesStatus = !statusFilter.value || offer.status === statusFilter.value
    const haystack = [
      offer.id,
      offer.intent_id,
      offer.catalog_item_id,
      offer.status,
      offer.currency,
      offer.tier,
      offer.warranty,
      offer.message,
    ].filter(Boolean).join(' ').toLowerCase()
    return matchesStatus && (!q || haystack.includes(q))
  })
})

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    DRAFT: 'gray',
    SUBMITTED: 'yellow',
    VIEWED: 'blue',
    SHORTLISTED: 'indigo',
    AWARDED: 'green',
    REJECTED: 'red',
    WITHDRAWN: 'gray',
    EXPIRED: 'red',
  }
  return map[status] || 'gray'
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

function canWithdraw(status: string) {
  return ['SUBMITTED', 'VIEWED', 'SHORTLISTED'].includes(status)
}

async function loadOffers() {
  error.value = ''
  try {
    await offerStore.fetchMyOffers()
    if (selectedOffer.value && !offerStore.myOffers.some((offer) => offer.id === selectedOffer.value?.id)) {
      selectedOffer.value = null
    }
  } catch (e: any) {
    selectedOffer.value = null
    const detail = e?.data?.detail || e?.message
    error.value = typeof detail === 'string' ? detail : 'Failed to load supplier offers.'
  }
}

async function withdrawOffer(row: Offer) {
  if (!canWithdraw(row.status)) return
  if (import.meta.client && !window.confirm(`Withdraw offer ${shortId(row.id)}?`)) return
  try {
    await offerStore.withdrawOffer(row.id)
    toast.add({ title: 'Offer withdrawn', color: 'green' })
    await loadOffers()
  } catch (e: any) {
    const detail = e?.data?.detail || e?.message
    toast.add({ title: typeof detail === 'string' ? detail : 'Failed to withdraw offer', color: 'red' })
  }
}

onMounted(loadOffers)
</script>
