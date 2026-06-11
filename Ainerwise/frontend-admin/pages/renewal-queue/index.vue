<template>
  <div class="space-y-6">
    <div>
      <h1 class="admin-page-title">{{ t('lc.rqTitle') }}</h1>
      <p class="admin-page-desc">{{ t('lc.rqDesc') }}</p>
    </div>

    <div v-if="Object.keys(queue.counts || {}).length" class="flex flex-wrap gap-2">
      <span v-for="(count, type) in queue.counts" :key="type"
        class="px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
        {{ String(type).replace(/_/g, ' ') }}: {{ count }}
      </span>
    </div>

    <div class="bg-white rounded-xl border overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-500">
          <tr>
            <th class="text-left font-medium px-4 py-2.5">{{ t('lc.type') }}</th>
            <th class="text-left font-medium px-4 py-2.5">{{ t('lc.opportunity') }}</th>
            <th class="text-left font-medium px-4 py-2.5">{{ t('lc.due') }}</th>
            <th class="text-left font-medium px-4 py-2.5">{{ t('lc.suggestedAction') }}</th>
            <th class="text-left font-medium px-4 py-2.5">{{ t('lc.priority') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y">
          <tr v-for="(o, i) in queue.opportunities || []" :key="i" class="hover:bg-gray-50">
            <td class="px-4 py-2.5">
              <span class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-gray-700">
                {{ o.type.replace(/_/g, ' ') }}
              </span>
            </td>
            <td class="px-4 py-2.5 text-gray-700">{{ o.title }}</td>
            <td class="px-4 py-2.5 text-gray-500">{{ o.due_date || '—' }}</td>
            <td class="px-4 py-2.5 text-gray-600">{{ o.suggested_action }}</td>
            <td class="px-4 py-2.5">
              <span :class="['px-2 py-0.5 rounded-full text-[11px] font-medium', priorityClass(o.priority)]">{{ o.priority }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!(queue.opportunities || []).length" class="p-8 text-center text-gray-500">
        {{ t('lc.noRenewals') }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const { t } = useI18n({ useScope: 'global' })
const queue = ref<any>({ opportunities: [], counts: {} })

function priorityClass(p: string) {
  if (p === 'high') return 'bg-red-50 text-red-600'
  if (p === 'medium') return 'bg-amber-50 text-amber-600'
  return 'bg-gray-100 text-gray-500'
}

onMounted(async () => {
  try {
    queue.value = await apiFetch<any>('/renewal-queue')
  } catch {
    queue.value = { opportunities: [], counts: {} }
  }
})
</script>
