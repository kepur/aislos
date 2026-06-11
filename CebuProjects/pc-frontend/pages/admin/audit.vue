<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">System Audit Logs</h1>
        <p class="text-sm text-slate-500 mt-1">Immutable record of all critical platform events and escrow movements.</p>
      </div>
      <UButton color="white" icon="i-heroicons-arrow-down-tray">Export Logs (CSV)</UButton>
    </div>

    <!-- Filters -->
    <UCard class="bg-white" :ui="{ body: { padding: 'p-4' } }">
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search actor ID, reference..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <USelect :options="['Event Type: All', 'Escrow Status Change', 'Dispute Status Change', 'KYB Status Change', 'Admin Action']" size="sm" />
        <UInput type="date" size="sm" />
        <UButton color="gray" variant="solid" size="sm" block>Apply Filters</UButton>
      </div>
    </UCard>

    <!-- Logs Table -->
    <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden font-mono text-sm">
      <UTable :columns="columns" :rows="logs" :ui="{ td: { padding: 'py-2 px-4' }, th: { padding: 'py-2 px-4 bg-slate-50 text-slate-500' } }">
        
        <template #timestamp-data="{ row }">
          <div class="text-slate-500">{{ row.timestamp }}</div>
        </template>
        
        <template #event-data="{ row }">
          <div class="font-bold" :class="getEventColor(row.event)">{{ row.event }}</div>
        </template>

        <template #actor-data="{ row }">
          <div class="text-slate-700">{{ row.actor }}</div>
        </template>
        
        <template #reference-data="{ row }">
          <div class="text-indigo-600 hover:underline cursor-pointer">{{ row.reference }}</div>
        </template>
        
        <template #details-data="{ row }">
          <div class="text-slate-600 truncate max-w-md">{{ row.details }}</div>
        </template>

      </UTable>
      
      <div class="p-4 border-t border-slate-200 bg-slate-50 flex justify-between items-center">
        <div class="text-xs text-slate-500">Showing 1-10 of 12,492 records</div>
        <UPagination :total="12492" :page="1" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'admin'
})

const columns = [
  { key: 'timestamp', label: 'Timestamp (UTC)' },
  { key: 'event', label: 'Event Type' },
  { key: 'actor', label: 'Actor' },
  { key: 'reference', label: 'Reference ID' },
  { key: 'details', label: 'Details' }
]

const logs = [
  { timestamp: '2023-10-25 14:32:01', event: 'ESCROW_FROZEN', actor: 'System', reference: '#ORD-82910', details: 'Funds frozen due to dispute #DIS-9912 creation.' },
  { timestamp: '2023-10-25 14:31:55', event: 'DISPUTE_OPENED', actor: 'usr_buyer_92', reference: '#DIS-9912', details: 'Reason: Items damaged. Amount: $4500.00' },
  { timestamp: '2023-10-25 12:15:22', event: 'ESCROW_PAYOUT_INIT', actor: 'System', reference: '#ORD-82912', details: 'Payout initiated to supplier sub-account. Amount: $12,400.00' },
  { timestamp: '2023-10-25 12:15:20', event: 'ORDER_DELIVERED', actor: 'usr_buyer_11', reference: '#ORD-82912', details: 'Buyer confirmed delivery manually.' },
  { timestamp: '2023-10-25 10:05:12', event: 'KYB_APPROVED', actor: 'adm_sarah_1', reference: 'sup_9921', details: 'Manual review passed. Granted VERIFIED status.' },
  { timestamp: '2023-10-25 09:12:00', event: 'ESCROW_FUNDED', actor: 'System', reference: '#ORD-82911', details: 'Card charge successful. Funds held.' }
]

const getEventColor = (event: string) => {
  if (event.includes('FROZEN') || event.includes('DISPUTE')) return 'text-red-600'
  if (event.includes('PAYOUT') || event.includes('APPROVED')) return 'text-green-600'
  if (event.includes('FUNDED')) return 'text-indigo-600'
  return 'text-slate-700'
}
</script>
