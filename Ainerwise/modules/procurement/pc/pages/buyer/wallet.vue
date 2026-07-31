<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Payments Ledger</h1>
        <p class="text-slate-500 mt-1">A record trail of your order payments. AISLOS Market never holds your funds.</p>
      </div>
      <UButton color="indigo" :loading="loading" @click="loadLedger">Refresh</UButton>
    </div>

    <UAlert
      color="blue"
      variant="subtle"
      icon="i-heroicons-information-circle"
      title="Direct-payment mode"
      description="You pay suppliers directly per the milestone plan you agree together. This page keeps the paper trail — recorded payments, references, and settlement status."
    />

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
      <UCard class="bg-indigo-600 text-white">
        <p class="text-indigo-100 text-sm font-medium">Recorded Payments</p>
        <p class="text-3xl font-bold mt-2">{{ money(recordedMinor, ledgerCurrency) }}</p>
        <p class="mt-4 text-xs text-indigo-100">Direct payments you logged on orders</p>
      </UCard>

      <UCard class="bg-white">
        <p class="text-slate-500 text-sm font-medium">Settled</p>
        <p class="text-3xl font-bold text-slate-900 mt-2">{{ money(settledMinor, ledgerCurrency) }}</p>
        <div class="mt-4 flex items-center text-xs text-green-600">
          <UIcon name="i-heroicons-check-badge" class="mr-1" />
          Delivery confirmed & closed
        </div>
      </UCard>

      <UCard class="bg-white">
        <p class="text-slate-500 text-sm font-medium">Awaiting Payment Record</p>
        <p class="text-3xl font-bold text-slate-900 mt-2">{{ awaitingCount }}</p>
        <div class="mt-4 flex items-center text-xs text-slate-500">
          <UIcon name="i-heroicons-clock" class="mr-1" />
          Orders without a recorded payment
        </div>
      </UCard>
    </div>

    <UCard>
      <template #header>
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-medium text-slate-900">Order Payment Records</h3>
          <UBadge color="indigo" variant="subtle">{{ paymentRows.length }} records</UBadge>
        </div>
      </template>

      <UTable :columns="paymentColumns" :rows="paymentRows" :loading="loading">
        <template #order-data="{ row }">
          <NuxtLink :to="`/buyer/orders/${row.id}`" class="font-mono text-xs text-indigo-600 hover:underline">
            {{ String(row.id).slice(0, 8) }}
          </NuxtLink>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="row.statusColor" variant="subtle">{{ row.statusLabel }}</UBadge>
        </template>
        <template #reference-data="{ row }">
          <span class="font-mono text-xs text-slate-600">{{ row.reference || '—' }}</span>
        </template>
      </UTable>
    </UCard>

    <UCard v-if="transactions.length">
      <template #header>
        <div>
          <h3 class="text-lg font-medium text-slate-900">Historical Account Records</h3>
          <p class="text-xs text-slate-500 mt-1">Read-only history from the legacy balance system.</p>
        </div>
      </template>

      <UTable :columns="txColumns" :rows="transactionRows">
        <template #amount-data="{ row }">
          <span :class="row.direction === 'credit' ? 'text-green-600' : 'text-slate-900'" class="font-medium">
            {{ row.direction === 'credit' ? '+' : '-' }}{{ row.amount }}
          </span>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer', middleware: ['auth'] })

type WalletTransaction = {
  id: string
  tx_type: string
  amount_delta_minor: number
  currency: string
  note?: string
  created_at: string
}

const config = useRuntimeConfig()
const authStore = useAuthStore()
const loading = ref(true)
const orders = ref<any[]>([])
const transactions = ref<WalletTransaction[]>([])

const paymentColumns = [
  { key: 'order', label: 'Order' },
  { key: 'date', label: 'Date' },
  { key: 'amount', label: 'Amount' },
  { key: 'status', label: 'Status' },
  { key: 'reference', label: 'Reference' },
]

const txColumns = [
  { key: 'date', label: 'Date' },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount' },
]

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  AWAITING_PAYMENT: { label: 'Awaiting payment record', color: 'orange' },
  PAID_IN_ESCROW: { label: 'Payment recorded', color: 'blue' },
  IN_PROGRESS: { label: 'In progress', color: 'indigo' },
  DELIVERED: { label: 'Delivered', color: 'teal' },
  ACCEPTED: { label: 'Completed', color: 'green' },
  PAYOUT_RELEASED: { label: 'Settled', color: 'green' },
  DISPUTED: { label: 'Disputed', color: 'red' },
  CANCELED: { label: 'Cancelled', color: 'gray' },
  CREATED: { label: 'Created', color: 'gray' },
}

const paymentRows = computed(() =>
  orders.value.map((order) => {
    const status = String(order.status || '').toUpperCase()
    const meta = STATUS_LABELS[status] || { label: status, color: 'gray' }
    return {
      id: order.id,
      date: order.created_at ? new Date(order.created_at).toLocaleDateString() : '—',
      amount: money(order.total_amount_minor || 0, order.currency),
      statusLabel: meta.label,
      statusColor: meta.color,
      reference: order.escrow?.provider_reference || null,
    }
  })
)

const ledgerCurrency = computed(() => orders.value.find((order) => order.currency)?.currency || 'EUR')

const recordedMinor = computed(() => orders.value
  .filter((order) => ['PAID_IN_ESCROW', 'IN_PROGRESS', 'DELIVERED', 'ACCEPTED', 'PAYOUT_RELEASED'].includes(String(order.status || '').toUpperCase()))
  .reduce((sum, order) => sum + (order.total_amount_minor || 0), 0))

const settledMinor = computed(() => orders.value
  .filter((order) => ['ACCEPTED', 'PAYOUT_RELEASED'].includes(String(order.status || '').toUpperCase()))
  .reduce((sum, order) => sum + (order.total_amount_minor || 0), 0))

const awaitingCount = computed(() => orders.value
  .filter((order) => String(order.status || '').toUpperCase() === 'AWAITING_PAYMENT').length)

const transactionRows = computed(() =>
  transactions.value.map((tx) => ({
    id: tx.id,
    date: new Date(tx.created_at).toLocaleString(),
    description: tx.note || tx.tx_type,
    amount: money(Math.abs(tx.amount_delta_minor), tx.currency),
    direction: tx.amount_delta_minor >= 0 ? 'credit' : 'debit',
  }))
)

function headers() {
  return { Authorization: `Bearer ${authStore.accessToken}` }
}

function money(minor: number, currency = 'EUR') {
  const value = (minor || 0) / 100
  try {
    return new Intl.NumberFormat('en', { style: 'currency', currency }).format(value)
  } catch {
    return `${value.toFixed(2)} ${currency}`
  }
}

async function loadLedger() {
  loading.value = true
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/orders/my`, { headers: headers() })
    orders.value = data.orders ?? data.items ?? data ?? []
  } catch {
    orders.value = []
  }
  try {
    transactions.value = await $fetch<WalletTransaction[]>(`${config.public.apiBase}/wallets/transactions`, { headers: headers() })
  } catch {
    transactions.value = []
  }
  loading.value = false
}

onMounted(loadLedger)
</script>
