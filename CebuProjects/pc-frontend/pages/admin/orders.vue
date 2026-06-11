<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">Orders & Escrow Operations</h1>
    </div>

    <UCard>
      <div class="flex items-center justify-between mb-4">
        <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search orders by ID..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <div class="flex space-x-2">
          <USelect :options="['All Statuses', 'Funded', 'In Transit', 'Delivered', 'Disputed']" />
          <UButton color="gray" variant="ghost" icon="i-heroicons-arrow-path" />
        </div>
      </div>

      <UTable :columns="columns" :rows="orders">
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #escrow-data="{ row }">
          <div class="flex items-center">
            <UIcon name="i-heroicons-lock-closed" class="w-4 h-4 text-green-500 mr-1" />
            <span class="font-medium text-slate-900">{{ row.escrow }}</span>
          </div>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-document-text">View Ledger</UButton>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'admin'
})

const columns = [
  { key: 'id', label: 'Order ID' },
  { key: 'buyer', label: 'Buyer Org' },
  { key: 'supplier', label: 'Supplier Org' },
  { key: 'escrow', label: 'Escrow Amount' },
  { key: 'status', label: 'Status' },
  { key: 'date', label: 'Created' },
  { key: 'actions', label: 'Actions' }
]

const orders = [
  { id: 'ORD-82910', buyer: 'John Doe Construction', supplier: 'Global Build Supply Co.', escrow: '$2,150.00', status: 'In Transit', date: '2023-10-26' },
  { id: 'ORD-82911', buyer: 'Tech Startup XYZ', supplier: 'TechWholesale Inc', escrow: '$8,500.00', status: 'Delivered', date: '2023-10-20' }
]

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    'Funded': 'blue',
    'In Transit': 'yellow',
    'Delivered': 'green',
    'Disputed': 'red'
  }
  return map[status] || 'gray'
}
</script>
