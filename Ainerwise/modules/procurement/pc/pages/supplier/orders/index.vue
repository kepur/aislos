<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Orders & Delivery</h1>
        <p class="mt-1 text-sm text-slate-500">Orders awarded to your supplier company.</p>
      </div>
      <UButton icon="i-heroicons-arrow-path" color="gray" variant="ghost" :loading="orderStore.loading" @click="loadOrders">
        Refresh
      </UButton>
    </div>

    <UCard>
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <UInput
          v-model="keyword"
          icon="i-heroicons-magnifying-glass"
          placeholder="Search order, intent, offer, buyer..."
          class="max-w-sm"
        />
        <div class="flex items-center gap-3">
          <USelect
            v-model="statusFilter"
            :options="statusOptions"
            option-attribute="label"
            value-attribute="value"
            class="w-48"
          />
          <span class="text-sm text-slate-500">{{ filteredOrders.length }} / {{ orders.length }} orders</span>
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

      <UTable :columns="columns" :rows="filteredOrders" :loading="orderStore.loading">
        <template #id-data="{ row }">
          <span class="font-mono text-xs text-indigo-600">{{ shortId(row.id) }}</span>
        </template>
        <template #buyer-data="{ row }">
          <span class="font-mono text-xs text-slate-600">{{ shortId(row.buyer_id) }}</span>
        </template>
        <template #summary-data="{ row }">
          <div>
            <p class="font-mono text-xs text-slate-700">Intent {{ shortId(row.intent_id) }}</p>
            <p class="font-mono text-xs text-slate-400">Offer {{ shortId(row.offer_id) }}</p>
          </div>
        </template>
        <template #date-data="{ row }">
          <span class="text-xs text-slate-500">{{ formatDate(row.created_at) }}</span>
        </template>
        <template #total-data="{ row }">
          <span class="font-medium text-slate-900">{{ formatPrice(row.total_amount_minor, row.currency) }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="indigo" variant="soft" :to="`/supplier/orders/${row.id}`">Manage Delivery</UButton>
        </template>
      </UTable>

      <div v-if="!orderStore.loading && filteredOrders.length === 0" class="mt-4 rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
        No orders match the current filters.
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import type { Order } from '~/types'

definePageMeta({ layout: 'supplier' })

const orderStore = useOrderStore()
const { formatPrice } = useApiUtils()

const keyword = ref('')
const statusFilter = ref('')
const error = ref('')

const columns = [
  { key: 'id', label: 'Order ID' },
  { key: 'buyer', label: 'Buyer' },
  { key: 'summary', label: 'Intent / Offer' },
  { key: 'date', label: 'Order Date' },
  { key: 'total', label: 'Total' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const statusOptions = [
  { label: 'All Statuses', value: '' },
  { label: 'Created', value: 'CREATED' },
  { label: 'Awaiting Payment', value: 'AWAITING_PAYMENT' },
  { label: 'Paid in Escrow', value: 'PAID_IN_ESCROW' },
  { label: 'In Progress', value: 'IN_PROGRESS' },
  { label: 'Delivered', value: 'DELIVERED' },
  { label: 'Accepted', value: 'ACCEPTED' },
  { label: 'Payout Released', value: 'PAYOUT_RELEASED' },
  { label: 'Disputed', value: 'DISPUTED' },
  { label: 'Canceled', value: 'CANCELED' },
]

const orders = computed(() => orderStore.orders)
const filteredOrders = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return orders.value.filter((order: Order) => {
    const matchesStatus = !statusFilter.value || order.status === statusFilter.value
    const haystack = [
      order.id,
      order.intent_id,
      order.offer_id,
      order.buyer_id,
      order.company_id,
      order.status,
      order.currency,
    ].filter(Boolean).join(' ').toLowerCase()
    return matchesStatus && (!q || haystack.includes(q))
  })
})

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    CREATED: 'gray',
    AWAITING_PAYMENT: 'yellow',
    PAID_IN_ESCROW: 'indigo',
    IN_PROGRESS: 'blue',
    DELIVERED: 'green',
    ACCEPTED: 'green',
    PAYOUT_RELEASED: 'green',
    DISPUTED: 'red',
    CANCELED: 'gray',
    REFUNDED: 'gray',
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

async function loadOrders() {
  error.value = ''
  try {
    await orderStore.fetchMyOrders()
  } catch (e: any) {
    const detail = e?.data?.detail || e?.message
    error.value = typeof detail === 'string' ? detail : 'Failed to load supplier orders.'
  }
}

onMounted(loadOrders)
</script>
