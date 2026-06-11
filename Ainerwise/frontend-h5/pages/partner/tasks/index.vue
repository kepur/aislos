<template>
  <div class="px-4 py-4">
    <div class="mb-4">
      <h1 class="text-xl font-bold text-slate-800">{{ $t('partner.tasks') }}</h1>
      <p class="mt-1 text-xs text-slate-400">{{ $t('partner.tasksSubtitle') }}</p>
    </div>

    <div class="mb-4 flex gap-2 overflow-x-auto pb-1">
      <button v-for="tab in tabs" :key="tab.key" class="shrink-0 rounded-full px-3.5 py-2 text-xs font-semibold"
        :class="activeTab === tab.key ? 'bg-blue-500 text-white' : 'border border-slate-200 bg-white text-slate-500'"
        @click="activeTab = tab.key">
        {{ tab.label }}
      </button>
    </div>

    <div v-if="loading" class="m-card text-center text-sm text-slate-400">{{ $t('partner.loadingTasks') }}</div>
    <div v-else-if="filtered.length" class="space-y-3">
      <NuxtLink v-for="task in filtered" :key="task.id" :to="`/partner/tasks/${task.id}`" class="block rounded-2xl border border-slate-100 bg-white p-4 shadow-sm active:bg-slate-50">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-bold capitalize text-slate-800">{{ task.task_type?.replace(/_/g, ' ') || $t('partner.serviceTask') }}</p>
            <p class="mt-1 truncate text-[11px] text-slate-500">{{ task.project_title || task.device_name || $t('partner.projectPending') }}</p>
          </div>
          <span :class="['status-pill shrink-0', statusClass(task.status)]">{{ task.status.replace(/_/g, ' ') }}</span>
        </div>
        <div class="mt-3 flex items-center justify-between text-[11px] text-slate-400">
          <span>{{ task.project_region || task.device_name || '—' }}</span>
          <span>{{ $t('partner.due') }} {{ task.due_date || $t('partner.notSet') }}</span>
        </div>
      </NuxtLink>
    </div>
    <div v-else class="m-card text-center text-sm text-slate-400">{{ $t('partner.noTasks') }}</div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()
const { t } = useI18n()
const items = ref<any[]>([])
const activeTab = ref('open')
const loading = ref(true)
const tabs = computed(() => [
  { key: 'open', label: t('partner.openTasks') },
  { key: 'all', label: t('partner.all') },
  { key: 'in_progress', label: t('partner.inProgress') },
  { key: 'done', label: t('partner.done') },
])
const filtered = computed(() => {
  if (activeTab.value === 'all') return items.value
  if (activeTab.value === 'open') return items.value.filter(task => ['scheduled', 'due', 'in_progress'].includes(task.status))
  return items.value.filter(task => task.status === activeTab.value)
})

function statusClass(status: string) {
  if (status === 'done') return 'bg-emerald-50 text-emerald-600'
  if (status === 'in_progress') return 'bg-amber-50 text-amber-600'
  return 'bg-blue-50 text-blue-600'
}

onMounted(async () => {
  try {
    const response = await apiFetch<any>('/partner/tasks?limit=100')
    items.value = response.items || []
  } finally {
    loading.value = false
  }
})
</script>
