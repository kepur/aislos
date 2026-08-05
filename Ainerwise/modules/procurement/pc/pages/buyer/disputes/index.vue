<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">Dispute Center</h1>
      <UButton to="/buyer/disputes/new" color="red" icon="i-heroicons-exclamation-triangle">Open New Dispute</UButton>
    </div>

    <UCard>
      <div class="flex items-center justify-between mb-4">
        <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search by Order ID..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <USelect :options="['All Statuses', 'Open', 'In Review', 'Resolved', 'Closed']" />
      </div>

      <UTable :columns="columns" :rows="disputes" :loading="loading">
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #amount-data="{ row }">
          <span class="font-medium text-slate-900">{{ row.amount }}</span>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="indigo" variant="soft" icon="i-heroicons-eye" :to="`/buyer/orders/${row.rawOrderId}`">View Order</UButton>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { formatMoneyMinor, localeForLanguage } from '~/utils/currencyPolicy'

definePageMeta({
  layout: 'buyer'
})

const columns = [
  { key: 'caseId', label: 'Case ID' },
  { key: 'orderId', label: 'Order ID' },
  { key: 'supplier', label: 'Supplier' },
  { key: 'reason', label: 'Reason' },
  { key: 'amount', label: 'Disputed Amount' },
  { key: 'status', label: 'Status' },
  { key: 'date', label: 'Opened Date' },
  { key: 'actions', label: 'Actions' }
]

const loading = ref(true)
const disputes = ref<any[]>([])
const { getDisputes } = useApi()
const appStore = useAppStore()

function fmtDate(value?: string) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString(localeForLanguage(appStore.language, appStore.currency), { year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(async () => {
  const { data, error } = await getDisputes()
  if (error) {
    disputes.value = []
  } else {
    disputes.value = ((data as any[]) || []).map((item) => ({
      caseId: `CAS-${String(item.id).slice(0, 8).toUpperCase()}`,
      orderId: `ORD-${String(item.order_id || item.commerce_order_id).slice(0, 8).toUpperCase()}`,
      rawOrderId: item.order_id || item.commerce_order_id,
      supplier: item.opened_by_role === 'SUPPLIER' ? 'Opened by supplier' : 'Supplier',
      reason: String(item.reason || item.reason_code || 'OTHER').replace(/_/g, ' '),
      amount: item.refund_amount_minor
        ? formatMoneyMinor(Number(item.refund_amount_minor), item.currency || appStore.currency || 'EUR', localeForLanguage(appStore.language, item.currency || appStore.currency))
        : '—',
      status: String(item.status || 'OPEN').replace(/_/g, ' '),
      date: fmtDate(item.created_at),
    }))
  }
  loading.value = false
})

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    'Open': 'yellow',
    'In Review': 'blue',
    'Resolved': 'green',
    'Closed': 'gray'
  }
  return map[status] || 'gray'
}
</script>
