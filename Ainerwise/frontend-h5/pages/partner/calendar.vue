<template>
  <div class="px-4 py-4">
    <div class="mb-4">
      <h1 class="text-xl font-bold text-slate-800">{{ $t('partner.calendar') }}</h1>
      <p class="mt-1 text-xs text-slate-400">{{ $t('partner.calendarSubtitle') }}</p>
    </div>

    <div v-if="loading" class="m-card text-center text-sm text-slate-400">{{ $t('partner.loadingCalendar') }}</div>
    <div v-else-if="groups.length" class="space-y-5">
      <section v-for="group in groups" :key="group.date">
        <p class="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-400">{{ formatDate(group.date) }}</p>
        <div class="space-y-2">
          <NuxtLink v-for="item in group.items" :key="item.id" :to="item.href" class="flex items-start gap-3 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <div class="mt-0.5 h-9 w-9 shrink-0 rounded-xl text-center text-[10px] font-bold leading-9"
              :class="item.type === 'task' ? 'bg-blue-50 text-blue-600' : 'bg-indigo-50 text-indigo-600'">
              {{ item.type === 'task' ? $t('partner.taskShort') : $t('partner.projectShort') }}
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-bold text-slate-800">{{ item.title }}</p>
              <p class="mt-1 truncate text-[11px] text-slate-500">{{ item.subtitle || '—' }}</p>
            </div>
            <span class="status-pill shrink-0 bg-slate-100 text-slate-500">{{ item.status.replace(/_/g, ' ') }}</span>
          </NuxtLink>
        </div>
      </section>
    </div>
    <div v-else class="m-card text-center text-sm text-slate-400">{{ $t('partner.noCalendarItems') }}</div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const { apiFetch } = useApi()
const items = ref<any[]>([])
const loading = ref(true)
const groups = computed(() => {
  const grouped = new Map<string, any[]>()
  for (const item of items.value) {
    grouped.set(item.date, [...(grouped.get(item.date) || []), item])
  }
  return [...grouped.entries()].map(([date, entries]) => ({ date, items: entries }))
})
function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(async () => {
  try {
    const response = await apiFetch<any>('/partner/calendar')
    items.value = response.items || []
  } finally {
    loading.value = false
  }
})
</script>
