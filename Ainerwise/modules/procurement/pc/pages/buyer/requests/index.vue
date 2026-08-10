<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">{{ appStore.t('buyer.requests.title') }}</h1>
      <UButton to="/post-request" color="indigo" icon="i-heroicons-plus">{{ appStore.t('buyer.requests.new') }}</UButton>
    </div>

    <UCard>
      <div class="flex items-center justify-between mb-4">
        <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" :placeholder="appStore.t('buyer.requests.search')"
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <div class="flex items-center space-x-2">
          <USelect :options="statusOptions" />
          <UButton color="gray" variant="ghost" icon="i-heroicons-funnel" />
        </div>
      </div>

      <UTable
        :columns="columns"
        :rows="requests"
        :loading="loading"
        :empty-state="{ icon: 'i-heroicons-circle-stack-20-solid', label: appStore.t('buyer.requests.empty') }"
      >
        <template #id-data="{ row }">
          <span class="text-xs text-gray-500">{{ row.id.slice(0, 8) }}</span>
        </template>
        <template #budget-data="{ row }">
          <span v-if="row.budget_min_minor || row.budget_max_minor">
            {{ row.currency }} {{ row.budget_min_minor ? row.budget_min_minor / 100 : 0 }} - {{ row.budget_max_minor ? row.budget_max_minor / 100 : 'Max' }}
          </span>
          <span v-else>{{ appStore.t('buyer.requests.open') }}</span>
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
          <UButton size="xs" color="indigo" variant="soft" :to="`/buyer/requests/${row.id}/offers`" v-if="(row.offers || 0) > 0">
            {{ appStore.t('buyer.requests.compare') }}
          </UButton>
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

const appStore = useAppStore()

const statusOptions = computed(() => [
  appStore.t('buyer.requests.allStatuses'),
  appStore.t('buyer.requests.statusDraft'),
  appStore.t('buyer.requests.statusReceiving'),
  appStore.t('buyer.requests.statusReviewing'),
  appStore.t('buyer.requests.statusAwarded'),
])

const columns = computed(() => [
  { key: 'id', label: appStore.t('buyer.requests.colId') },
  { key: 'title', label: appStore.t('buyer.requests.colTitle') },
  { key: 'budget', label: appStore.t('buyer.requests.colBudget') },
  { key: 'created_at', label: appStore.t('buyer.requests.colDate') },
  { key: 'status', label: appStore.t('buyer.requests.colStatus') },
  { key: 'offers', label: appStore.t('buyer.requests.colOffers') },
  { key: 'actions', label: appStore.t('buyer.requests.colActions') },
])

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
    useToast().add({ title: appStore.t('buyer.requests.fetchError'), color: 'red' })
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
