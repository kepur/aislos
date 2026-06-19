<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">Risk Flags & Alerts</h1>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      <UCard class="bg-red-50 border-red-200">
        <p class="text-red-600 text-sm font-medium">Critical Alerts</p>
        <p class="text-3xl font-bold text-red-700 mt-2">3</p>
      </UCard>
      <UCard class="bg-yellow-50 border-yellow-200">
        <p class="text-yellow-600 text-sm font-medium">Suspicious Activities</p>
        <p class="text-3xl font-bold text-yellow-700 mt-2">12</p>
      </UCard>
      <UCard class="bg-indigo-50 border-indigo-200">
        <p class="text-indigo-600 text-sm font-medium">Pending Manual Reviews</p>
        <p class="text-3xl font-bold text-indigo-700 mt-2">8</p>
      </UCard>
    </div>

    <UCard>
      <UTable :columns="columns" :rows="flags">
        <template #severity-data="{ row }">
          <UBadge :color="row.severity === 'High' ? 'red' : 'yellow'" variant="solid">{{ row.severity }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="indigo" variant="soft">Investigate</UButton>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })

const columns = [
  { key: 'id', label: 'Flag ID' },
  { key: 'type', label: 'Risk Type' },
  { key: 'target', label: 'Entity' },
  { key: 'severity', label: 'Severity' },
  { key: 'date', label: 'Detected' },
  { key: 'actions', label: 'Actions' }
]

const flags = [
  { id: 'RSK-991', type: 'Unusually Low Price Offer', target: 'Offer OFF-102', severity: 'High', date: '2 hours ago' },
  { id: 'RSK-990', type: 'Rapid Consecutive Orders', target: 'Buyer ID 142', severity: 'Medium', date: '5 hours ago' }
]
</script>
