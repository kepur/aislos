<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">My Offers</h1>
      <UButton to="/supplier/inbox" color="indigo" variant="soft">View Pings</UButton>
    </div>

    <UCard>
      <div class="flex items-center justify-between mb-4">
        <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search offers..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <USelect :options="['All Statuses', 'Pending', 'Accepted', 'Rejected']" />
      </div>

      <UTable :columns="columns" :rows="offers">
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #amount-data="{ row }">
          <span class="font-medium text-slate-900">{{ row.amount }}</span>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-eye">View Details</UButton>
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
  { key: 'id', label: 'Offer ID' },
  { key: 'requestTitle', label: 'Request Title' },
  { key: 'buyer', label: 'Buyer' },
  { key: 'date', label: 'Submitted Date' },
  { key: 'amount', label: 'Quote Amount' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const offers = [
  { id: 'OFF-101', requestTitle: '500 bags Portland Cement', buyer: 'John Doe Construction', date: '2023-10-26', amount: '$2,150.00', status: 'Accepted' },
  { id: 'OFF-102', requestTitle: 'Marine Engine Parts', buyer: 'Oceanic Shipping', date: '2023-10-25', amount: '$1,400.00', status: 'Pending' },
  { id: 'OFF-103', requestTitle: 'Office Laptops (x10)', buyer: 'Tech Startup XYZ', date: '2023-10-22', amount: '$9,000.00', status: 'Rejected' }
]

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    'Pending': 'yellow',
    'Accepted': 'green',
    'Rejected': 'red'
  }
  return map[status] || 'gray'
}
</script>
