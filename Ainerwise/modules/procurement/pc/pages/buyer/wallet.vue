<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ t('wallet.title') }}</h1>
        <p class="text-slate-500 mt-1">{{ t('wallet.subtitle') }}</p>
      </div>
      <UButton color="indigo" :loading="loading" @click="loadLedger">{{ t('wallet.refresh') }}</UButton>
    </div>

    <UAlert
      color="blue"
      variant="subtle"
      icon="i-heroicons-information-circle"
      :title="t('wallet.directTitle')"
      :description="t('wallet.directDesc')"
    />
    <p class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500 shadow-sm">
      {{ t('wallet.currencyNote') }}
    </p>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
      <UCard class="bg-indigo-600 text-white">
        <p class="text-indigo-100 text-sm font-medium">{{ t('wallet.recordedPayments') }}</p>
        <p class="text-3xl font-bold mt-2">{{ money(recordedMinor, ledgerCurrency) }}</p>
        <p class="mt-4 text-xs text-indigo-100">{{ t('wallet.recordedDesc') }}</p>
      </UCard>

      <UCard class="bg-white">
        <p class="text-slate-500 text-sm font-medium">{{ t('wallet.settled') }}</p>
        <p class="text-3xl font-bold text-slate-900 mt-2">{{ money(settledMinor, ledgerCurrency) }}</p>
        <div class="mt-4 flex items-center text-xs text-green-600">
          <UIcon name="i-heroicons-check-badge" class="mr-1" />
          {{ t('wallet.settledDesc') }}
        </div>
      </UCard>

      <UCard class="bg-white">
        <p class="text-slate-500 text-sm font-medium">{{ t('wallet.awaiting') }}</p>
        <p class="text-3xl font-bold text-slate-900 mt-2">{{ awaitingCount }}</p>
        <div class="mt-4 flex items-center text-xs text-slate-500">
          <UIcon name="i-heroicons-clock" class="mr-1" />
          {{ t('wallet.awaitingDesc') }}
        </div>
      </UCard>
    </div>

    <UCard>
      <template #header>
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-medium text-slate-900">{{ t('wallet.orderRecords') }}</h3>
          <UBadge color="indigo" variant="subtle">{{ paymentRows.length }} {{ t('wallet.records') }}</UBadge>
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
          <h3 class="text-lg font-medium text-slate-900">{{ t('wallet.historical') }}</h3>
          <p class="text-xs text-slate-500 mt-1">{{ t('wallet.historicalDesc') }}</p>
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
const appStore = useAppStore()
const t = (key: string) => appStore.t(key)
const loading = ref(true)
const orders = ref<any[]>([])
const transactions = ref<WalletTransaction[]>([])

const paymentColumns = computed(() => [
  { key: 'order', label: t('wallet.column.order') },
  { key: 'date', label: t('wallet.column.date') },
  { key: 'amount', label: t('wallet.column.amount') },
  { key: 'status', label: t('wallet.column.status') },
  { key: 'reference', label: t('wallet.column.reference') },
])

const txColumns = computed(() => [
  { key: 'date', label: t('wallet.column.date') },
  { key: 'description', label: t('wallet.column.description') },
  { key: 'amount', label: t('wallet.column.amount') },
])

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  AWAITING_PAYMENT: { label: 'wallet.status.AWAITING_PAYMENT', color: 'orange' },
  PAID_IN_ESCROW: { label: 'wallet.status.PAID_IN_ESCROW', color: 'blue' },
  IN_PROGRESS: { label: 'wallet.status.IN_PROGRESS', color: 'indigo' },
  DELIVERED: { label: 'wallet.status.DELIVERED', color: 'teal' },
  ACCEPTED: { label: 'wallet.status.ACCEPTED', color: 'green' },
  PAYOUT_RELEASED: { label: 'wallet.status.PAYOUT_RELEASED', color: 'green' },
  DISPUTED: { label: 'wallet.status.DISPUTED', color: 'red' },
  CANCELED: { label: 'wallet.status.CANCELED', color: 'gray' },
  CREATED: { label: 'wallet.status.CREATED', color: 'gray' },
}

const ledgerCurrency = computed(() => String(appStore.currency || 'EUR').toUpperCase())

const ledgerOrders = computed(() =>
  orders.value.filter((order) => String(order.currency || ledgerCurrency.value).toUpperCase() === ledgerCurrency.value)
)

const paymentRows = computed(() =>
  ledgerOrders.value.map((order) => {
    const status = String(order.status || '').toUpperCase()
    const meta = STATUS_LABELS[status] || { label: status, color: 'gray' }
    return {
      id: order.id,
      date: order.created_at ? new Date(order.created_at).toLocaleDateString(dateLocale.value) : '—',
      amount: money(order.total_amount_minor || 0, order.currency),
      statusLabel: meta.label.startsWith('wallet.') ? t(meta.label) : meta.label,
      statusColor: meta.color,
      reference: order.escrow?.provider_reference || null,
    }
  })
)

const recordedMinor = computed(() => orders.value
  .filter((order) => String(order.currency || ledgerCurrency.value).toUpperCase() === ledgerCurrency.value)
  .filter((order) => ['PAID_IN_ESCROW', 'IN_PROGRESS', 'DELIVERED', 'ACCEPTED', 'PAYOUT_RELEASED'].includes(String(order.status || '').toUpperCase()))
  .reduce((sum, order) => sum + (order.total_amount_minor || 0), 0))

const settledMinor = computed(() => orders.value
  .filter((order) => String(order.currency || ledgerCurrency.value).toUpperCase() === ledgerCurrency.value)
  .filter((order) => ['ACCEPTED', 'PAYOUT_RELEASED'].includes(String(order.status || '').toUpperCase()))
  .reduce((sum, order) => sum + (order.total_amount_minor || 0), 0))

const awaitingCount = computed(() => orders.value
  .filter((order) => String(order.currency || ledgerCurrency.value).toUpperCase() === ledgerCurrency.value)
  .filter((order) => String(order.status || '').toUpperCase() === 'AWAITING_PAYMENT').length)

const transactionRows = computed(() =>
  transactions.value
  .filter((tx) => String(tx.currency || ledgerCurrency.value).toUpperCase() === ledgerCurrency.value)
  .map((tx) => ({
    id: tx.id,
    date: new Date(tx.created_at).toLocaleString(dateLocale.value),
    description: tx.note || tx.tx_type,
    amount: money(Math.abs(tx.amount_delta_minor), tx.currency),
    direction: tx.amount_delta_minor >= 0 ? 'credit' : 'debit',
  }))
)

const dateLocale = computed(() => {
  if (appStore.language === 'ZH') return 'zh-CN'
  if (appStore.language === 'SR') return 'sr-RS'
  return 'en'
})

function headers() {
  return { Authorization: `Bearer ${authStore.accessToken}` }
}

function money(minor: number, currency = 'EUR') {
  const value = (minor || 0) / 100
  try {
    return new Intl.NumberFormat(dateLocale.value, { style: 'currency', currency }).format(value)
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
