<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">Pricing Intelligence & Analytics</h1>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <UCard>
        <template #header>
          <h3 class="font-medium text-slate-900">Average Quote vs Final Price</h3>
        </template>
        <div class="h-64 flex items-center justify-center bg-slate-50 border border-dashed border-slate-200 rounded">
          <p class="text-slate-400">Chart rendering (Chart.js placeholder)</p>
        </div>
      </UCard>
      
      <UCard>
        <template #header>
          <h3 class="font-medium text-slate-900">Category Volume Trends</h3>
        </template>
        <div class="h-64 flex items-center justify-center bg-slate-50 border border-dashed border-slate-200 rounded">
          <p class="text-slate-400">Chart rendering (Chart.js placeholder)</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <template #header>
        <h3 class="font-medium text-slate-900">Recent Benchmark Anomalies</h3>
      </template>
      <UTable :columns="columns" :rows="anomalies">
        <template #variance-data="{ row }">
          <span :class="row.variance.includes('+') ? 'text-red-600' : 'text-green-600'" class="font-medium">
            {{ row.variance }}
          </span>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })

const columns = [
  { key: 'category', label: 'Category' },
  { key: 'benchmark', label: 'Benchmark Price' },
  { key: 'actual', label: 'Actual Avg Price' },
  { key: 'variance', label: 'Variance' }
]

const anomalies = [
  { category: 'Portland Cement (Per Bag)', benchmark: '$4.10', actual: '$4.80', variance: '+17%' },
  { category: 'Steel Rebar (Per Ton)', benchmark: '$650.00', actual: '$610.00', variance: '-6%' }
]
</script>
