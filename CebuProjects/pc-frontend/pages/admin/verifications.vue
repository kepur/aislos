<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">KYB Verification Queue</h1>
        <p class="text-sm text-slate-500 mt-1">Review supplier applications to grant them verified status.</p>
      </div>
    </div>

    <!-- Filters -->
    <UCard class="bg-white" :ui="{ body: { padding: 'p-4' } }">
      <div class="flex flex-wrap items-center gap-4">
        <div class="relative w-64">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search company name or TIN..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <USelect :options="['Status: Pending Review', 'Status: Approved', 'Status: Rejected', 'Status: Incomplete']" size="sm" class="w-48" />
        <USelect :options="['Sort: Oldest First', 'Sort: Newest First']" size="sm" class="w-40" />
      </div>
    </UCard>

    <!-- Verification Table -->
    <div class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <UTable :columns="columns" :rows="applications">
        
        <template #company-data="{ row }">
          <div>
            <div class="font-bold text-indigo-600 hover:underline cursor-pointer">{{ row.companyName }}</div>
            <div class="text-xs text-slate-500 mt-0.5">TIN: {{ row.taxId }}</div>
          </div>
        </template>
        
        <template #submitted-data="{ row }">
          <div class="text-sm text-slate-700">{{ row.submittedAt }}</div>
        </template>

        <template #documents-data="{ row }">
          <div class="flex space-x-2">
            <UTooltip text="View Business Registration">
              <UButton color="gray" variant="soft" icon="i-heroicons-document-text" size="2xs" />
            </UTooltip>
            <UTooltip text="View Representative ID">
              <UButton color="gray" variant="soft" icon="i-heroicons-identification" size="2xs" />
            </UTooltip>
          </div>
        </template>

        <template #status-data="{ row }">
          <UBadge :color="row.status === 'Pending' ? 'yellow' : 'green'" variant="subtle" size="sm">
            {{ row.status }}
          </UBadge>
        </template>
        
        <template #actions-data="{ row }">
          <div class="flex items-center space-x-2">
            <UButton size="xs" color="indigo" variant="solid">Review</UButton>
          </div>
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
  { key: 'company', label: 'Company Information' },
  { key: 'submitted', label: 'Submitted Date' },
  { key: 'documents', label: 'Documents' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const applications = [
  { companyName: 'Visayas Cement Corp', taxId: '000-123-456-000', submittedAt: 'Oct 25, 2023 09:12 AM', status: 'Pending' },
  { companyName: 'Cebu Marine Supply', taxId: '111-222-333-000', submittedAt: 'Oct 24, 2023 14:30 PM', status: 'Pending' },
  { companyName: 'TechHub BPO', taxId: '999-888-777-000', submittedAt: 'Oct 22, 2023 10:00 AM', status: 'Approved' }
]
</script>
