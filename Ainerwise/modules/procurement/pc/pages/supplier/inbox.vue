<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Ping Inbox</h1>
        <p class="text-sm text-slate-500 mt-1">Real-time buyer requests matching your catalog and alert rules.</p>
      </div>
      <div class="flex items-center space-x-3">
        <div class="text-sm text-slate-600 font-medium">Status:</div>
        <USelect v-model="status" :options="['Online: Receiving Pings', 'Offline', 'Busy']" class="w-48" color="green" />
      </div>
    </div>

    <!-- Filters Bar -->
    <UCard class="bg-white" :ui="{ body: { padding: 'p-4 sm:p-4' } }">
      <div class="flex flex-wrap items-center gap-4">
        <div class="relative w-64">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search requests..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <USelect :options="['Category: All', 'Construction Materials', 'Hardware', 'Electrical']" size="sm" class="w-48" />
        <USelect :options="['Distance: Any', 'Within 5km', 'Within 10km']" size="sm" class="w-40" />
        <USelect :options="['Sort: Newest First', 'Sort: Highest Budget', 'Sort: Closest', 'Sort: Pre-funded First']" size="sm" class="w-48" />

        <div class="flex items-center ml-auto space-x-4">
          <label class="flex items-center gap-2 cursor-pointer select-none"><input type="checkbox" class="w-4 h-4 rounded border-slate-300 accent-indigo-600 cursor-pointer" /><span class="text-sm text-slate-700">Pre-funded only</span></label>
          <UButton variant="ghost" color="gray" size="sm" icon="i-heroicons-arrow-path" :loading="offerStore.loading" @click="loadPings">Refresh</UButton>
        </div>
      </div>
    </UCard>

    <!-- Pings Table -->
    <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <UTable :columns="columns" :rows="tableRows" :loading="offerStore.loading">

        <template #summary-data="{ row }">
          <div>
            <div class="font-bold text-slate-900">{{ row.title }}</div>
            <div class="text-xs text-slate-500">ID: {{ row.shortId }} • {{ row.category }}</div>
            <div class="mt-1 line-clamp-1 text-sm text-slate-600">{{ row.description }}</div>
          </div>
        </template>

        <template #budget-data="{ row }">
          <div class="text-sm font-semibold text-slate-800">{{ row.budget }}</div>
          <UBadge v-if="row.preFunded" color="green" size="xs" variant="subtle" class="mt-1">Pre-funded</UBadge>
        </template>

        <template #logistics-data="{ row }">
          <div class="text-sm text-slate-700 flex flex-col space-y-1">
            <span class="flex items-center"><UIcon name="i-heroicons-map-pin" class="w-3 h-3 mr-1 text-slate-400" /> {{ row.distance }}</span>
            <span class="flex items-center"><UIcon name="i-heroicons-calendar" class="w-3 h-3 mr-1 text-slate-400" /> {{ row.deliveryWindow }}</span>
          </div>
        </template>

        <template #timeLeft-data="{ row }">
          <div class="flex items-center text-orange-600 font-medium text-sm">
            <UIcon name="i-heroicons-clock" class="w-4 h-4 mr-1" />
            {{ row.timeLeft }}
          </div>
        </template>

        <template #actions-data="{ row }">
          <UButton color="indigo" size="sm" class="font-bold w-full justify-center" @click="makeOffer(row)">Make Offer</UButton>
          <div class="text-center mt-2">
            <UButton color="gray" variant="ghost" size="xs" class="text-slate-400 hover:text-slate-600">Dismiss</UButton>
          </div>
        </template>

      </UTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Intent } from '~/types'

definePageMeta({
  layout: 'supplier'
})

const router = useRouter()
const offerStore = useOfferStore()
const status = ref('Online: Receiving Pings')

const columns = [
  { key: 'summary', label: 'Request Summary' },
  { key: 'qty', label: 'Quantity' },
  { key: 'budget', label: 'Budget' },
  { key: 'logistics', label: 'Distance & Delivery' },
  { key: 'timeLeft', label: 'Time Left' },
  { key: 'actions', label: 'Actions' }
]

const tableRows = computed(() => offerStore.pings.map((ping) => mapPingRow(ping)))

function mapPingRow(ping: Intent) {
  const budget =
    ping.budget_min_minor && ping.budget_max_minor
      ? `${formatMinor(ping.budget_min_minor, ping.currency)} - ${formatMinor(ping.budget_max_minor, ping.currency)}`
      : ping.budget_max_minor
        ? `Up to ${formatMinor(ping.budget_max_minor, ping.currency)}`
        : 'Open'
  return {
    id: ping.id,
    shortId: `#${String(ping.id).slice(0, 8)}`,
    title: ping.title,
    category: ping.category_id ? `Category ${String(ping.category_id).slice(0, 8)}` : 'General',
    description: ping.notes || 'No additional notes.',
    qty: `${ping.qty || 1} ${ping.unit || 'pcs'}`,
    budget,
    preFunded: Boolean(ping.budget_max_minor),
    distance: [ping.city, ping.country].filter(Boolean).join(', ') || `${ping.radius_km || 30} km service area`,
    deliveryWindow: formatDeliveryWindow(ping),
    timeLeft: formatTimeLeft(ping.expires_at),
  }
}

function formatMinor(amountMinor: number, currency = 'PHP') {
  try {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amountMinor / 100)
  } catch {
    return `${(amountMinor / 100).toLocaleString()} ${currency}`
  }
}

function formatDeliveryWindow(ping: Intent) {
  if (ping.delivery_window_start || ping.delivery_window_end) {
    return [ping.delivery_window_start, ping.delivery_window_end].filter(Boolean).map((date) => new Date(String(date)).toLocaleDateString()).join(' - ')
  }
  return 'Flexible'
}

function formatTimeLeft(expiresAt?: string) {
  if (!expiresAt) return 'Open'
  const ms = new Date(expiresAt).getTime() - Date.now()
  if (!Number.isFinite(ms) || ms <= 0) return 'Expired'
  const hours = Math.floor(ms / 3600000)
  if (hours < 24) return `${hours}h left`
  return `${Math.floor(hours / 24)}d left`
}

async function loadPings() {
  await offerStore.fetchPings()
}

const makeOffer = (ping: { id: string }) => {
  router.push(`/supplier/offers/new?intent_id=${ping.id}`)
}

onMounted(loadPings)
</script>
