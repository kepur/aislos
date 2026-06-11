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
          <UButton variant="ghost" color="gray" size="sm" icon="i-heroicons-arrow-path">Refresh</UButton>
        </div>
      </div>
    </UCard>

    <!-- Pings Table -->
    <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <UTable :columns="columns" :rows="pings">
        
        <template #summary-data="{ row }">
          <div>
            <div class="font-bold text-slate-900">{{ row.title }}</div>
            <div class="text-xs text-slate-500">ID: {{ row.id }} • {{ row.category }}</div>
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
import { ref } from 'vue'

definePageMeta({
  layout: 'supplier'
})

const status = ref('Online: Receiving Pings')

const columns = [
  { key: 'summary', label: 'Request Summary' },
  { key: 'qty', label: 'Quantity' },
  { key: 'budget', label: 'Budget' },
  { key: 'logistics', label: 'Distance & Delivery' },
  { key: 'timeLeft', label: 'Time Left' },
  { key: 'actions', label: 'Actions' }
]

const pings = [
  {
    id: '#REQ-82910',
    title: '500 bags Portland Cement',
    category: 'Construction Materials',
    description: 'Looking for Holcim or Republic brand. Must be delivered by tomorrow afternoon.',
    qty: '500 Bags',
    budget: '$2,000 - $2,500',
    preFunded: true,
    distance: '4.2 km',
    deliveryWindow: 'Tomorrow, 2PM',
    timeLeft: '3h 15m'
  },
  {
    id: '#REQ-82911',
    title: '1000m Copper Wire 12 AWG',
    category: 'Electrical',
    description: 'THHN stranded. Need 2 rolls of 500m each.',
    qty: '1000 Meters',
    budget: 'Open',
    preFunded: false,
    distance: '1.5 km',
    deliveryWindow: 'Next Week',
    timeLeft: '1d 12h'
  },
  {
    id: '#REQ-82912',
    title: 'Commercial AC Unit 5HP',
    category: 'HVAC',
    description: 'Floor standing split type, inverter. Daikin or Panasonic preferred.',
    qty: '1 Piece',
    budget: '$1,500 Max',
    preFunded: true,
    distance: '8.0 km',
    deliveryWindow: 'Anytime',
    timeLeft: '5h 45m'
  }
]

const makeOffer = (ping: any) => {
  // Mock make offer action
  alert(`Opening quote editor for ${ping.title}`)
}
</script>
