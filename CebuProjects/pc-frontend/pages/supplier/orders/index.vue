<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">Orders & Delivery</h1>
    </div>

    <UCard>
      <div class="flex items-center justify-between mb-4">
        <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search orders by ID..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <USelect :options="['All Statuses', 'Preparing', 'In Transit', 'Delivered']" />
      </div>

      <UTable :columns="columns" :rows="orders">
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #total-data="{ row }">
          <span class="font-medium text-slate-900">{{ row.total }}</span>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="indigo" variant="soft" :to="`/supplier/orders/${row.id}`">Manage Delivery</UButton>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'supplier'
})

const columns = [
  { key: 'id', label: 'Order ID' },
  { key: 'buyer', label: 'Buyer' },
  { key: 'item', label: 'Item Summary' },
  { key: 'date', label: 'Order Date' },
  { key: 'total', label: 'Total' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const orders = [
  { id: 1, buyer: 'John Doe Construction', item: '500 bags Portland Cement', date: '2023-10-26', total: '$2,150.00', status: 'In Transit' },
]

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    'Preparing': 'blue',
    'In Transit': 'yellow',
    'Delivered': 'green'
  }
  return map[status] || 'gray'
}
</script>
