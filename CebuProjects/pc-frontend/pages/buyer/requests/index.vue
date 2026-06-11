<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">My Requests</h1>
      <UButton to="/post-request" color="indigo" icon="i-heroicons-plus">New Request</UButton>
    </div>

    <UCard>
      <div class="flex items-center justify-between mb-4">
        <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search requests..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <div class="flex items-center space-x-2">
          <USelect :options="['All Statuses', 'Draft', 'Receiving Offers', 'Reviewing', 'Awarded']" />
          <UButton color="gray" variant="ghost" icon="i-heroicons-funnel" />
        </div>
      </div>

      <UTable :columns="columns" :rows="requests" :loading="loading">
        <template #id-data="{ row }">
          <span class="text-xs text-gray-500">{{ row.id.slice(0, 8) }}</span>
        </template>
        <template #budget-data="{ row }">
          <span v-if="row.budget_min_minor || row.budget_max_minor">
            {{ row.currency }} {{ row.budget_min_minor ? row.budget_min_minor / 100 : 0 }} - {{ row.budget_max_minor ? row.budget_max_minor / 100 : 'Max' }}
          </span>
          <span v-else>Open</span>
        </template>
        <template #created_at-data="{ row }">
          {{ new Date(row.created_at).toLocaleDateString() }}
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #offers-data="{ row }">
          <span class="font-medium text-indigo-600">{{ row.offers || 0 }}</span>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-eye" :to="`/buyer/requests/${row.id}`" class="mr-2" />
          <UButton size="xs" color="indigo" variant="soft" :to="`/buyer/requests/${row.id}/offers`" v-if="(row.offers || 0) > 0">Compare</UButton>
        </template>
      </UTable>
      
      <div class="flex justify-end mt-4">
        <UPagination :total="4" :page="1" />
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'buyer'
})

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'title', label: 'Request Title' },
  { key: 'budget', label: 'Target Budget' },
  { key: 'created_at', label: 'Posted Date' },
  { key: 'status', label: 'Status' },
  { key: 'offers', label: 'Offers' },
  { key: 'actions', label: 'Actions' }
]

const api = useApi()
const requests = ref<any[]>([])
const loading = ref(true)

const fetchRequests = async () => {
  loading.value = true
  const { data, error } = await api.getMyIntents()
  if (data && Array.isArray(data)) {
    requests.value = data
  } else {
    console.error(error)
    useToast().add({ title: 'Error fetching requests', color: 'red' })
  }
  loading.value = false
}

onMounted(() => {
  fetchRequests()
})

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    'DRAFT': 'gray',
    'PUBLISHED': 'blue',
    'CLOSED': 'yellow',
    'COMPLETED': 'green',
    'CANCELLED': 'red'
  }
  return map[status] || 'gray'
}
</script>
