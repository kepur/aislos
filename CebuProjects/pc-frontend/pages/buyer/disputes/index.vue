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

      <UTable :columns="columns" :rows="disputes">
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #amount-data="{ row }">
          <span class="font-medium text-slate-900">{{ row.amount }}</span>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="indigo" variant="soft" icon="i-heroicons-eye">View Case</UButton>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
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

const disputes = [
  { caseId: 'CAS-4412', orderId: 'ORD-82800', supplier: 'Global Build Supply Co.', reason: 'Item Not as Described', amount: '$4,500.00', status: 'In Review', date: '2023-10-25' },
  { caseId: 'CAS-3901', orderId: 'ORD-81105', supplier: 'TechWholesale Inc', reason: 'Late Delivery', amount: '$1,200.00', status: 'Resolved', date: '2023-10-10' }
]

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
