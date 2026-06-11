<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Payouts & Earnings</h1>
      <p class="text-slate-500 mt-1">Track your completed orders and manage withdrawal methods.</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
      <UCard class="bg-indigo-600 text-white">
        <p class="text-indigo-100 text-sm font-medium">Available for Withdrawal</p>
        <p class="text-3xl font-bold mt-2">$42,500.00</p>
        <div class="mt-4">
          <UButton color="white" variant="solid" size="sm" class="w-full justify-center">Withdraw Funds</UButton>
        </div>
      </UCard>
      
      <UCard class="bg-white border border-slate-200">
        <div class="flex justify-between items-start mb-2">
          <p class="text-slate-500 text-sm font-medium">Primary Payout Method</p>
          <UBadge color="green" variant="subtle">Verified</UBadge>
        </div>
        <div class="flex items-center space-x-3 mt-4">
          <div class="bg-slate-100 p-2 rounded">
            <UIcon name="i-heroicons-building-library" class="w-6 h-6 text-slate-600" />
          </div>
          <div>
            <p class="font-medium text-slate-900">JPMorgan Chase Bank</p>
            <p class="text-sm text-slate-500">Checking •••• 4920</p>
          </div>
        </div>
        <UButton variant="ghost" color="indigo" size="xs" class="mt-4 px-0">Change Method</UButton>
      </UCard>
    </div>

    <UCard>
      <template #header>
        <h3 class="text-lg font-medium text-slate-900">Withdrawal History</h3>
      </template>

      <UTable :columns="columns" :rows="payouts">
        <template #status-data="{ row }">
          <UBadge :color="row.status === 'Completed' ? 'green' : 'blue'" variant="subtle">{{ row.status }}</UBadge>
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'supplier' })

const columns = [
  { key: 'id', label: 'Transfer ID' },
  { key: 'date', label: 'Date' },
  { key: 'amount', label: 'Amount' },
  { key: 'destination', label: 'Destination' },
  { key: 'status', label: 'Status' }
]

const payouts = [
  { id: 'TRX-1092', date: '2023-10-15', amount: '$12,400.00', destination: 'Chase •••• 4920', status: 'Completed' },
  { id: 'TRX-0984', date: '2023-09-30', amount: '$8,250.00', destination: 'Chase •••• 4920', status: 'Completed' },
  { id: 'TRX-0821', date: '2023-09-15', amount: '$15,000.00', destination: 'Chase •••• 4920', status: 'Completed' }
]
</script>
