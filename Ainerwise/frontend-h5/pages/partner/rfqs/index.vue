<template>
  <div class="px-4 py-4">
    <div class="mb-4">
      <h1 class="text-xl font-bold text-slate-800">{{ $t('partner.requests') }}</h1>
      <p class="mt-1 text-xs text-slate-400">{{ $t('partner.requestsSubtitle') }}</p>
    </div>

    <div class="mb-4 flex gap-2 overflow-x-auto pb-1">
      <button v-for="tab in tabs" :key="tab.key" class="shrink-0 rounded-full px-3.5 py-2 text-xs font-semibold"
        :class="activeTab === tab.key ? 'bg-blue-500 text-white' : 'border border-slate-200 bg-white text-slate-500'"
        @click="activeTab = tab.key">
        {{ tab.label }}
      </button>
    </div>

    <div v-if="loading" class="m-card text-center text-sm text-slate-400">{{ $t('partner.loading') }}</div>
    <div v-else-if="filtered.length" class="space-y-3">
      <NuxtLink v-for="rfq in filtered" :key="rfq.id" :to="`/partner/rfqs/${rfq.id}`" class="block rounded-2xl border border-slate-100 bg-white p-4 shadow-sm active:bg-slate-50">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-bold text-slate-800">{{ rfq.title }}</p>
            <p class="mt-1 text-[10px] font-bold uppercase tracking-wider text-blue-500">{{ rfq.trade }}</p>
          </div>
          <span :class="['status-pill shrink-0', statusClass(rfq.invitation_status)]">{{ rfq.invitation_status.replace(/_/g, ' ') }}</span>
        </div>
        <p v-if="rfq.scope_json?.summary" class="mt-3 line-clamp-2 text-xs leading-relaxed text-slate-500">{{ rfq.scope_json.summary }}</p>
        <div class="mt-3 flex items-center justify-between text-[11px] text-slate-400">
          <span>{{ location(rfq) }}</span>
          <span v-if="rfq.bid_deadline">{{ $t('partner.due') }} {{ date(rfq.bid_deadline) }}</span>
        </div>
        <div v-if="rfq.bid" class="mt-3 rounded-xl bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">
          {{ $t('partner.yourBid') }}: {{ rfq.bid.currency }} {{ Number(rfq.bid.amount).toLocaleString() }} · {{ rfq.bid.lead_time_days ?? '—' }} {{ $t('partner.days') }}
        </div>
      </NuxtLink>
    </div>
    <div v-else class="m-card text-center text-sm text-slate-400">{{ $t('partner.noRequests') }}</div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()
const { t } = useI18n()
const items = ref<any[]>([])
const activeTab = ref('open')
const loading = ref(true)
const tabs = computed(() => [
  { key: 'open', label: t('partner.open') },
  { key: 'all', label: t('partner.all') },
  { key: 'bid_submitted', label: t('partner.submitted') },
  { key: 'declined', label: t('partner.declined') },
])
const filtered = computed(() => {
  if (activeTab.value === 'all') return items.value
  if (activeTab.value === 'open') return items.value.filter(r => ['sent', 'viewed'].includes(r.invitation_status))
  return items.value.filter(r => r.invitation_status === activeTab.value)
})

function statusClass(status: string) {
  if (status === 'bid_submitted') return 'bg-emerald-50 text-emerald-600'
  if (status === 'declined') return 'bg-slate-100 text-slate-500'
  return 'bg-blue-50 text-blue-600'
}
function location(rfq: any) {
  return [rfq.scope_json?.city, rfq.scope_json?.country].filter(Boolean).join(', ') || t('partner.locationPending')
}
function date(value: string) {
  return new Date(value).toLocaleDateString()
}

onMounted(async () => {
  try {
    const response = await apiFetch<any>('/partner/rfqs?limit=100')
    items.value = response.items || []
  } finally {
    loading.value = false
  }
})
</script>
