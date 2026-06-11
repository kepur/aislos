<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Dispute Resolution Center</h1>
        <p class="text-sm text-slate-500 mt-1">Manage frozen escrow funds and arbitrate buyer-supplier conflicts.</p>
      </div>
    </div>

    <!-- Overview Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <UCard class="bg-red-50 border-red-200">
        <div class="text-red-800 text-sm font-semibold mb-1">Open Disputes</div>
        <div class="text-3xl font-bold text-red-900">4</div>
      </UCard>
      <UCard class="bg-indigo-50 border-indigo-200">
        <div class="text-indigo-800 text-sm font-semibold mb-1">Frozen Funds</div>
        <div class="text-3xl font-bold text-indigo-900">$8,450</div>
      </UCard>
      <UCard class="bg-white border-slate-200">
        <div class="text-slate-600 text-sm font-semibold mb-1">Avg Resolution Time</div>
        <div class="text-3xl font-bold text-slate-900">2.4 Days</div>
      </UCard>
      <UCard class="bg-white border-slate-200">
        <div class="text-slate-600 text-sm font-semibold mb-1">Resolved (30 Days)</div>
        <div class="text-3xl font-bold text-slate-900">18</div>
      </UCard>
    </div>

    <!-- Disputes Table -->
    <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <div class="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <h3 class="font-bold text-slate-900">Active Cases</h3>
        <USelect :options="['Sort by: Escalate Time', 'Sort by: Value', 'Sort by: Age']" size="sm" class="w-48" />
      </div>
      <UTable :columns="columns" :rows="disputes">
        
        <template #case-data="{ row }">
          <div>
            <div class="font-bold text-slate-900">{{ row.id }}</div>
            <div class="text-xs text-slate-500 mt-0.5">Ord: {{ row.orderId }}</div>
          </div>
        </template>
        
        <template #parties-data="{ row }">
          <div class="text-sm">
            <div class="text-slate-900"><span class="font-medium text-slate-500">B:</span> {{ row.buyer }}</div>
            <div class="text-slate-900"><span class="font-medium text-slate-500">S:</span> {{ row.supplier }}</div>
          </div>
        </template>

        <template #reason-data="{ row }">
          <div class="text-sm text-slate-800 font-medium">{{ row.reason }}</div>
          <div class="text-xs text-slate-500 mt-0.5 truncate w-48">{{ row.description }}</div>
        </template>
        
        <template #funds-data="{ row }">
          <div class="text-sm font-bold text-red-600">${{ row.frozenFunds }}</div>
        </template>

        <template #status-data="{ row }">
          <UBadge :color="row.status === 'Escalated' ? 'red' : 'yellow'" variant="subtle" size="sm">
            {{ row.status }}
          </UBadge>
        </template>

        <template #actions-data="{ row }">
          <UButton size="xs" color="indigo" variant="solid">Arbitrate</UButton>
        </template>

      </UTable>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'admin'
})

const columns = [
  { key: 'case', label: 'Case ID' },
  { key: 'parties', label: 'Buyer / Supplier' },
  { key: 'reason', label: 'Reason' },
  { key: 'funds', label: 'Frozen Funds' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const disputes = [
  {
    id: '#DIS-9912',
    orderId: '#ORD-82910',
    buyer: 'Oceanic Transport Corp',
    supplier: 'Cebu Marine Supply',
    reason: 'Items damaged',
    description: 'Received the engine parts but box was crushed.',
    frozenFunds: '4,500.00',
    status: 'Escalated'
  },
  {
    id: '#DIS-9913',
    orderId: '#ORD-82913',
    buyer: 'Startup Inc',
    supplier: 'Furniture City',
    reason: 'Items not delivered',
    description: 'Supplier marked as delivered but nothing arrived.',
    frozenFunds: '850.00',
    status: 'Awaiting Supplier Response'
  }
]
</script>
