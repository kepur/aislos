<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">My Orders</h1>
      <UButton icon="i-heroicons-arrow-path" color="gray" variant="ghost" :loading="loading" @click="load(true)">
        Refresh
      </UButton>
    </div>

    <UCard>
      <div class="flex items-center gap-3 mb-4 flex-wrap">
        <UInput
          v-model="keyword"
          icon="i-heroicons-magnifying-glass"
          placeholder="Search by order ID or supplier..."
          class="max-w-xs"
          @keyup.enter="load(true)"
        />
        <USelect
          v-model="statusFilter"
          :options="statusOptions"
          option-attribute="label"
          value-attribute="value"
          @change="load(true)"
        />
      </div>

      <UTable :columns="columns" :rows="orders" :loading="loading">
        <template #id-data="{ row }">
          <span class="font-mono text-xs text-slate-500">#{{ row.id.split('-')[0] }}</span>
        </template>
        <template #supplier-data="{ row }">
          <span class="font-medium text-slate-800">{{ row.supplier_company_name || '—' }}</span>
        </template>
        <template #total-data="{ row }">
          <span class="font-semibold text-slate-900">{{ formatMinor(row.total_amount_minor, row.currency) }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="statusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #created_at-data="{ row }">
          <span class="text-xs text-slate-400">{{ new Date(row.created_at).toLocaleDateString() }}</span>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="indigo" variant="soft" :to="`/buyer/orders/${row.id}`">
            View Details
          </UButton>
        </template>
      </UTable>

      <div class="flex items-center justify-between mt-4">
        <p class="text-sm text-slate-500">{{ total }} total orders</p>
        <div class="flex gap-2">
          <UButton size="sm" color="gray" variant="outline" :disabled="page <= 1" @click="page--; load(false)">← Prev</UButton>
          <UButton size="sm" color="gray" variant="outline" :disabled="!hasNext" @click="page++; load(false)">Next →</UButton>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer', middleware: ['buyer'] })

const authStore = useAuthStore()
const config = useRuntimeConfig()

const keyword = ref('')
const statusFilter = ref('')
const page = ref(1)
const loading = ref(false)
const orders = ref<any[]>([])
const total = ref(0)
const hasNext = ref(false)

const statusOptions = [
  { label: 'All Statuses', value: '' },
  { label: 'Awaiting Payment', value: 'AWAITING_PAYMENT' },
  { label: 'Paid in Escrow', value: 'PAID_IN_ESCROW' },
  { label: 'In Progress', value: 'IN_PROGRESS' },
  { label: 'Delivered', value: 'DELIVERED' },
  { label: 'Payout Released', value: 'PAYOUT_RELEASED' },
  { label: 'Disputed', value: 'DISPUTED' },
  { label: 'Canceled', value: 'CANCELED' },
]

const columns = [
  { key: 'id', label: 'Order ID' },
  { key: 'supplier', label: 'Supplier' },
  { key: 'total', label: 'Total (Escrow)' },
  { key: 'status', label: 'Status' },
  { key: 'created_at', label: 'Date' },
  { key: 'actions', label: 'Actions' },
]

function statusColor(s: string) {
  return {
    AWAITING_PAYMENT: 'orange',
    PAID_IN_ESCROW: 'blue',
    IN_PROGRESS: 'purple',
    DELIVERED: 'indigo',
    ACCEPTED: 'green',
    PAYOUT_RELEASED: 'green',
    DISPUTED: 'red',
    CANCELED: 'gray',
    REFUNDED: 'gray',
  }[s] || 'gray'
}

function formatMinor(minor: number, currency = 'PHP') {
  if (!minor) return '—'
  const amount = minor / 100
  try {
    return new Intl.NumberFormat('en-PH', { style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount)
  } catch {
    return `${amount.toLocaleString()} ${currency}`
  }
}

async function load(reset = false) {
  if (reset) { page.value = 1; orders.value = [] }
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: 20 }
    if (statusFilter.value) params.status = statusFilter.value
    const data = await $fetch<any>(`${config.public.apiBase}/orders/my`, {
      params,
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    orders.value = data.orders ?? data.items ?? data ?? []
    total.value = data.total ?? orders.value.length
    hasNext.value = data.has_next ?? false
  } catch (e: any) {
    console.error('Orders fetch error:', e)
    orders.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => load(true))
</script>
