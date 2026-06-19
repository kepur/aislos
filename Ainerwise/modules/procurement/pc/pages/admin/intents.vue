<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">Buyer Intents (Requests)</h1>
    </div>

    <UCard>
      <div class="flex items-center justify-between mb-4">
        <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search intents..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <USelect :options="['All Statuses', 'Draft', 'Receiving Offers', 'Reviewing', 'Awarded']" />
      </div>

      <UTable :columns="columns" :rows="intents">
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-eye">View Timeline</UButton>
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
  { key: 'id', label: 'Intent ID' },
  { key: 'buyer', label: 'Buyer Org' },
  { key: 'title', label: 'Request Title' },
  { key: 'date', label: 'Posted Date' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const intents = [
  { id: 'INT-82910', buyer: 'John Doe Construction', title: '500 bags Portland Cement', date: '2023-10-25', status: 'Receiving Offers' },
  { id: 'INT-82911', buyer: 'Tech Startup XYZ', title: 'Office Laptops (x10)', date: '2023-10-24', status: 'Reviewing' },
]

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    'Draft': 'gray',
    'Receiving Offers': 'blue',
    'Reviewing': 'yellow',
    'Awarded': 'green'
  }
  return map[status] || 'gray'
}
</script>
