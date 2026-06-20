<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Buyer Intents (Requests)</h1>
        <p class="mt-1 text-sm text-slate-500">Live buyer requests from AinerWise Core.</p>
      </div>
      <UButton icon="i-heroicons-arrow-path" color="gray" variant="ghost" :loading="loading" @click="loadIntents">
        Refresh
      </UButton>
    </div>

    <UCard>
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <UInput
          v-model="keyword"
          icon="i-heroicons-magnifying-glass"
          placeholder="Search title, buyer, city, or intent id..."
          class="max-w-sm"
        />
        <div class="flex items-center gap-3">
          <USelect
            v-model="statusFilter"
            :options="statusOptions"
            option-attribute="label"
            value-attribute="value"
            class="w-44"
          />
          <span class="text-sm text-slate-500">{{ filteredIntents.length }} / {{ intents.length }} requests</span>
        </div>
      </div>

      <UAlert
        v-if="error"
        color="red"
        variant="soft"
        icon="i-heroicons-exclamation-triangle"
        class="mb-4"
        :title="error"
      />

      <UTable :columns="columns" :rows="filteredIntents" :loading="loading">
        <template #id-data="{ row }">
          <span class="font-mono text-xs text-indigo-600">{{ shortId(row.id) }}</span>
        </template>
        <template #buyer-data="{ row }">
          <span class="font-mono text-xs text-slate-600">{{ shortId(row.buyer_id) }}</span>
        </template>
        <template #title-data="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ row.title }}</p>
            <p class="text-xs text-slate-400">{{ row.city || 'No city' }}<span v-if="row.country">, {{ row.country }}</span></p>
          </div>
        </template>
        <template #budget-data="{ row }">
          <span class="font-medium text-slate-900">{{ row.budget_max_minor ? formatMinor(row.budget_max_minor, row.currency) : 'N/A' }}</span>
        </template>
        <template #date-data="{ row }">
          <span class="text-xs text-slate-500">{{ formatDate(row.created_at) }}</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex flex-wrap items-center gap-2">
            <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-eye" @click="selectedIntent = row">
              Details
            </UButton>
            <UButton v-if="row.status === 'ACTIVE'" size="xs" color="yellow" variant="soft" @click="moderateIntent(row, 'flag')">
              Flag
            </UButton>
            <UButton v-if="row.status === 'ACTIVE'" size="xs" color="red" variant="soft" @click="moderateIntent(row, 'cancel')">
              Cancel
            </UButton>
            <UButton v-if="row.status === 'CANCELED'" size="xs" color="green" variant="soft" @click="moderateIntent(row, 'restore')">
              Restore
            </UButton>
          </div>
        </template>
      </UTable>

      <div v-if="!loading && filteredIntents.length === 0" class="mt-4 rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
        No buyer requests match the current filters.
      </div>
    </UCard>

    <UCard v-if="selectedIntent">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="font-medium text-slate-900">Intent Details</h3>
          <UButton size="xs" color="gray" variant="ghost" @click="selectedIntent = null">Close</UButton>
        </div>
      </template>
      <dl class="grid grid-cols-1 gap-4 text-sm md:grid-cols-3">
        <div>
          <dt class="text-slate-400">Intent ID</dt>
          <dd class="font-mono text-slate-800">{{ selectedIntent.id }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Buyer ID</dt>
          <dd class="font-mono text-slate-800">{{ selectedIntent.buyer_id }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Offers</dt>
          <dd class="font-medium text-slate-800">{{ selectedIntent.offer_count ?? 0 }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Quantity</dt>
          <dd class="text-slate-800">{{ selectedIntent.qty }} {{ selectedIntent.unit }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Budget Range</dt>
          <dd class="text-slate-800">{{ formatBudget(selectedIntent) }}</dd>
        </div>
        <div>
          <dt class="text-slate-400">Location</dt>
          <dd class="text-slate-800">{{ [selectedIntent.city, selectedIntent.country].filter(Boolean).join(', ') || 'N/A' }}</dd>
        </div>
      </dl>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })

type IntentRow = {
  id: string
  buyer_id: string
  title: string
  qty: number
  unit: string
  budget_min_minor?: number
  budget_max_minor?: number
  currency: string
  country?: string
  city?: string
  status: string
  created_at: string
  offer_count?: number
}

const config = useRuntimeConfig()
const authStore = useAuthStore()
const toast = useToast()

const loading = ref(false)
const error = ref('')
const keyword = ref('')
const statusFilter = ref('')
const intents = ref<IntentRow[]>([])
const selectedIntent = ref<IntentRow | null>(null)

const columns = [
  { key: 'id', label: 'Intent ID' },
  { key: 'buyer', label: 'Buyer Org' },
  { key: 'title', label: 'Request Title' },
  { key: 'budget', label: 'Budget' },
  { key: 'date', label: 'Posted Date' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const statusOptions = [
  { label: 'All Statuses', value: '' },
  { label: 'Draft', value: 'DRAFT' },
  { label: 'Active', value: 'ACTIVE' },
  { label: 'Awarded', value: 'AWARDED' },
  { label: 'Closed', value: 'CLOSED' },
  { label: 'Canceled', value: 'CANCELED' },
  { label: 'Expired', value: 'EXPIRED' },
]

const filteredIntents = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return intents.value.filter((intent) => {
    const matchesStatus = !statusFilter.value || intent.status === statusFilter.value
    const haystack = [
      intent.id,
      intent.buyer_id,
      intent.title,
      intent.city,
      intent.country,
      intent.status,
      intent.currency,
    ].filter(Boolean).join(' ').toLowerCase()
    return matchesStatus && (!q || haystack.includes(q))
  })
})

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    DRAFT: 'gray',
    ACTIVE: 'blue',
    AWARDED: 'green',
    CLOSED: 'gray',
    CANCELED: 'red',
    EXPIRED: 'yellow',
  }
  return map[status] || 'gray'
}

function normalizeList(data: any): IntentRow[] {
  if (Array.isArray(data)) return data
  return data?.items || data?.intents || []
}

function shortId(value?: string) {
  return value ? String(value).slice(0, 8) : 'N/A'
}

function formatDate(value?: string) {
  if (!value) return 'N/A'
  try {
    return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
  } catch {
    return value
  }
}

function formatMinor(amountMinor: number, currency = 'PHP') {
  try {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(Number(amountMinor || 0) / 100)
  } catch {
    return `${(Number(amountMinor || 0) / 100).toLocaleString()} ${currency}`
  }
}

function formatBudget(row: IntentRow) {
  if (row.budget_min_minor && row.budget_max_minor) {
    return `${formatMinor(row.budget_min_minor, row.currency)} - ${formatMinor(row.budget_max_minor, row.currency)}`
  }
  if (row.budget_max_minor) return formatMinor(row.budget_max_minor, row.currency)
  if (row.budget_min_minor) return formatMinor(row.budget_min_minor, row.currency)
  return 'N/A'
}

async function loadIntents() {
  loading.value = true
  error.value = ''
  try {
    const headers = { Authorization: `Bearer ${authStore.accessToken}` }
    const data = await $fetch<any>(`${config.public.apiBase}/admin/intents`, {
      params: { limit: 500 },
      headers,
    })
    intents.value = normalizeList(data)
    if (selectedIntent.value && !intents.value.some((intent) => intent.id === selectedIntent.value?.id)) {
      selectedIntent.value = null
    }
  } catch (e: any) {
    intents.value = []
    selectedIntent.value = null
    const detail = e?.data?.detail
    error.value = typeof detail === 'string' ? detail : 'Failed to load buyer intents.'
  } finally {
    loading.value = false
  }
}

async function moderateIntent(row: IntentRow, action: 'flag' | 'cancel' | 'restore') {
  const reason = import.meta.client ? window.prompt(`Reason for ${action} on intent ${shortId(row.id)}:`) : ''
  if (!reason) return
  try {
    await $fetch(`${config.public.apiBase}/admin/intents/${row.id}/moderate`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
      body: { action, reason },
    })
    toast.add({ title: 'Intent updated', color: 'green' })
    await loadIntents()
  } catch (e: any) {
    const detail = e?.data?.detail
    toast.add({ title: typeof detail === 'string' ? detail : 'Failed to update intent', color: 'red' })
  }
}

onMounted(loadIntents)
</script>
