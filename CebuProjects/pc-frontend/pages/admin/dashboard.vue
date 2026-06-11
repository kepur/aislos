<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 tracking-tight">Platform Operations</h1>
        <p class="text-sm text-slate-500 mt-1">Real-time overview of marketplace activity.</p>
      </div>
      <div class="flex items-center space-x-3">
        <USelect v-model="timeframe" :options="['Today', 'Last 24 Hours', 'Last 7 Days', 'This Month']" size="sm" class="w-36" />
        <UButton color="white" icon="i-heroicons-arrow-down-tray" size="sm" class="shadow-sm">Export Report</UButton>
      </div>
    </div>

    <!-- Admin KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
      <UCard class="bg-white border border-slate-200" :ui="{ body: { padding: 'p-4' } }">
        <div class="flex flex-col">
          <dt class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">GMV (Escrowed)</dt>
          <dd class="text-2xl font-bold text-slate-900">$1.2M</dd>
          <div class="text-xs text-green-600 mt-2 flex items-center"><UIcon name="i-heroicons-arrow-trending-up" class="w-3 h-3 mr-1" /> +12%</div>
        </div>
      </UCard>
      
      <UCard class="bg-white border border-slate-200" :ui="{ body: { padding: 'p-4' } }">
        <div class="flex flex-col">
          <dt class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Active Intents</dt>
          <dd class="text-2xl font-bold text-slate-900">342</dd>
          <div class="text-xs text-green-600 mt-2 flex items-center"><UIcon name="i-heroicons-arrow-trending-up" class="w-3 h-3 mr-1" /> +5%</div>
        </div>
      </UCard>

      <UCard class="bg-white border border-indigo-200 shadow-sm shadow-indigo-100" :ui="{ body: { padding: 'p-4' } }">
        <div class="flex flex-col">
          <dt class="text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-1">Pending KYB</dt>
          <dd class="text-2xl font-bold text-indigo-900">12</dd>
          <div class="text-xs text-slate-500 mt-2">Requires manual review</div>
        </div>
      </UCard>

      <UCard class="bg-white border border-red-200 shadow-sm shadow-red-100" :ui="{ body: { padding: 'p-4' } }">
        <div class="flex flex-col">
          <dt class="text-xs font-semibold text-red-600 uppercase tracking-wide mb-1">Open Disputes</dt>
          <dd class="text-2xl font-bold text-red-900">4</dd>
          <div class="text-xs text-red-500 mt-2 font-medium">1 escalated</div>
        </div>
      </UCard>

      <UCard class="bg-white border border-slate-200" :ui="{ body: { padding: 'p-4' } }">
        <div class="flex flex-col">
          <dt class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Escrow Release SLA</dt>
          <dd class="text-2xl font-bold text-slate-900">1.2 hrs</dd>
          <div class="text-xs text-slate-500 mt-2">Avg. time to payout</div>
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- Operations Queue / Timeline -->
      <UCard class="lg:col-span-1 flex flex-col">
        <template #header>
          <h3 class="text-sm font-semibold text-slate-900 uppercase tracking-wider">Operations Queue</h3>
        </template>
        
        <div class="relative border-l border-slate-200 ml-3 space-y-6 pb-4">
          <div class="relative pl-6">
            <div class="absolute -left-1.5 top-1.5 w-3 h-3 bg-red-500 rounded-full border-2 border-white"></div>
            <div class="text-xs text-slate-500 mb-1">10 mins ago</div>
            <div class="text-sm font-medium text-slate-900">Dispute Escalated: #DIS-9912</div>
            <div class="text-sm text-slate-600 mt-1">Buyer claims items arrived damaged.</div>
            <UButton size="2xs" color="red" variant="soft" class="mt-2">Review Dispute</UButton>
          </div>
          
          <div class="relative pl-6">
            <div class="absolute -left-1.5 top-1.5 w-3 h-3 bg-indigo-500 rounded-full border-2 border-white"></div>
            <div class="text-xs text-slate-500 mb-1">25 mins ago</div>
            <div class="text-sm font-medium text-slate-900">KYB Submission: Visayas Cement Corp</div>
            <div class="text-sm text-slate-600 mt-1">DTI Registration and valid IDs uploaded.</div>
            <UButton size="2xs" color="indigo" variant="soft" class="mt-2">Review Documents</UButton>
          </div>
          
          <div class="relative pl-6">
            <div class="absolute -left-1.5 top-1.5 w-3 h-3 bg-yellow-500 rounded-full border-2 border-white"></div>
            <div class="text-xs text-slate-500 mb-1">1 hour ago</div>
            <div class="text-sm font-medium text-slate-900">Risk Flag: High Value Transaction</div>
            <div class="text-sm text-slate-600 mt-1">Order #ORD-82910 ($120,000) triggered velocity limits.</div>
            <UButton size="2xs" color="yellow" variant="soft" class="mt-2">View Audit Log</UButton>
          </div>
        </div>
      </UCard>

      <!-- Active Marketplace Feed -->
      <UCard class="lg:col-span-2 flex flex-col">
        <template #header>
          <div class="flex justify-between items-center">
            <h3 class="text-sm font-semibold text-slate-900 uppercase tracking-wider">Live Escrow & Orders</h3>
            <div class="flex space-x-2">
              <USelect :options="['All Statuses', 'Funded', 'In Transit', 'Completed']" size="xs" class="w-32" />
            </div>
          </div>
        </template>
        
        <UTable :columns="columns" :rows="orders" :ui="{ td: { padding: 'py-2 px-4 text-sm' }, th: { padding: 'py-2 px-4 text-xs' } }">
          <template #order-data="{ row }">
            <div class="font-medium text-indigo-600 hover:underline cursor-pointer">{{ row.id }}</div>
            <div class="text-xs text-slate-500">{{ row.type }}</div>
          </template>
          
          <template #participants-data="{ row }">
            <div class="text-sm text-slate-900">B: {{ row.buyer }}</div>
            <div class="text-sm text-slate-700">S: {{ row.supplier }}</div>
          </template>

          <template #amount-data="{ row }">
            <div class="font-bold text-slate-900">{{ row.amount }}</div>
          </template>
          
          <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle" size="xs">{{ row.status }}</UBadge>
          </template>
          
          <template #actions-data="{ row }">
            <UDropdown :items="[[{ label: 'View Order' }, { label: 'View Escrow Audit' }, { label: 'Force Refund', icon: 'i-heroicons-exclamation-triangle', class: 'text-red-500' }]]">
              <UButton color="gray" variant="ghost" icon="i-heroicons-ellipsis-vertical" size="sm" />
            </UDropdown>
          </template>
        </UTable>
      </UCard>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({
  layout: 'admin'
})

const timeframe = ref('Today')

const columns = [
  { key: 'order', label: 'Order ID' },
  { key: 'participants', label: 'Buyer / Supplier' },
  { key: 'amount', label: 'Escrow Amount' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const orders = [
  { id: '#ORD-82910', type: 'Marine Engine Parts', buyer: 'Oceanic Transport', supplier: 'Cebu Marine Supply', amount: '$4,500.00', status: 'In Transit' },
  { id: '#ORD-82911', type: 'Portland Cement', buyer: 'Mandaue Builders', supplier: 'Visayas Cement Corp', amount: '$2,175.00', status: 'Funded (Awaiting Shipment)' },
  { id: '#ORD-82912', type: 'IT Equipment', buyer: 'TechHub BPO', supplier: 'PC Express Cebu', amount: '$12,400.00', status: 'Completed (Payout Processing)' },
  { id: '#ORD-82913', type: 'Office Chairs', buyer: 'Startup Inc', supplier: 'Furniture City', amount: '$850.00', status: 'Disputed' }
]

const getStatusColor = (status: string) => {
  if (status.includes('Completed')) return 'green'
  if (status.includes('In Transit')) return 'blue'
  if (status.includes('Disputed')) return 'red'
  if (status.includes('Funded')) return 'indigo'
  return 'gray'
}
</script>
