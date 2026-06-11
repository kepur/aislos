<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">{{ $t('admin.solutions') }}</h1>
      <NuxtLink to="/admin/solutions/create" class="btn-primary text-sm">{{ $t('common.create') }}</NuxtLink>
    </div>
    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Title</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Category</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Visible</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sol in solutions" :key="sol.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">{{ sol.title }}</td>
            <td class="px-4 py-3">{{ sol.category || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="sol.public_visible ? 'active' : 'draft'" :label="sol.public_visible ? 'Visible' : 'Hidden'" /></td>
            <td class="px-4 py-3">
              <NuxtLink :to="`/admin/solutions/${sol.id}/edit`" class="text-primary-600 hover:underline text-xs">{{ $t('common.edit') }}</NuxtLink>
            </td>
          </tr>
          <tr v-if="!solutions.length">
            <td colspan="4" class="px-4 py-8 text-center text-gray-500">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const solutions = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/solutions')
    solutions.value = res.items || res || []
  } catch {}
})
</script>
