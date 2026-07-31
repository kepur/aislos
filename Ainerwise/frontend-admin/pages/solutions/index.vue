<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="admin-page-title">{{ $t('admin.solutions') }}</h1>
      <NuxtLink to="solutions/create" class="btn-primary text-sm">{{ $t('common.create') }}</NuxtLink>
    </div>
    <div v-if="loadError" class="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ loadError }}
      <button class="ml-2 font-semibold underline" @click="loadSolutions">Retry</button>
    </div>
    <div class="admin-panel">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Title</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Category</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Visible</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sol in solutions" :key="sol.id" class="border-b">
            <td class="px-4 py-3 font-medium">{{ sol.title }}</td>
            <td class="px-4 py-3">{{ sol.category || '-' }}</td>
            <td class="px-4 py-3"><StatusBadge :status="sol.public_visible ? 'active' : 'draft'" :label="sol.public_visible ? 'Visible' : 'Hidden'" /></td>
            <td class="px-4 py-3">
              <NuxtLink :to="`solutions/${sol.id}/edit`" class="text-primary-600 hover:underline text-xs">{{ $t('common.edit') }}</NuxtLink>
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
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const solutions = ref<any[]>([])
const loadError = ref('')

async function loadSolutions() {
  loadError.value = ''
  try {
    const res = await apiFetch<any>('/solutions')
    solutions.value = res.items || res || []
  } catch (e: any) {
    loadError.value = e?.data?.detail || e?.message || 'Unable to load solutions.'
  }
}

onMounted(loadSolutions)
</script>
