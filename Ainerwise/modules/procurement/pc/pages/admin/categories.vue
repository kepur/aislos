<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold text-slate-900">Taxonomy & Category Schema</h1>
      <UButton color="indigo" icon="i-heroicons-plus">Add Category</UButton>
    </div>

    <UCard>
      <div class="flex items-center justify-between mb-4">
        <div class="relative max-w-sm">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input type="text" placeholder="Search categories..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
      </div>

      <UTable :columns="columns" :rows="categories">
        <template #status-data="{ row }">
          <UBadge :color="row.status === 'Active' ? 'green' : 'gray'" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-pencil-square" />
        </template>
      </UTable>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Category Name' },
  { key: 'parent', label: 'Parent Category' },
  { key: 'suppliers', label: 'Registered Suppliers' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: 'Actions' }
]

const categories = [
  { id: 'CAT-101', name: 'Portland Cement', parent: 'Construction Materials', suppliers: 142, status: 'Active' },
  { id: 'CAT-102', name: 'Marine Engines', parent: 'Heavy Machinery', suppliers: 28, status: 'Active' },
  { id: 'CAT-103', name: 'Office Laptops', parent: 'IT Equipment', suppliers: 85, status: 'Active' }
]
</script>
