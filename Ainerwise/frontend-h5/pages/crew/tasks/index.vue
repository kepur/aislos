<template>
  <div class="space-y-4 p-4">
    <div><p class="text-[10px] font-bold uppercase tracking-widest text-amber-600">Crew delivery</p><h1 class="mt-1 text-xl font-bold text-slate-900">Crew tasks</h1></div>
    <div class="flex gap-2 overflow-x-auto"><button v-for="item in tabs" :key="item" class="shrink-0 rounded-full px-3 py-2 text-xs font-semibold capitalize" :class="filter === item ? 'bg-amber-500 text-white' : 'border border-amber-200 bg-white text-slate-500'" @click="filter = item">{{ item }}</button></div>
    <NuxtLink v-for="task in filtered" :key="task.id" :to="`/crew/tasks/${task.id}`" class="m-card block"><div class="flex justify-between gap-3"><div><p class="text-sm font-bold text-slate-800">{{ task.title }}</p><p class="mt-1 text-xs text-slate-400">{{ task.crew_name }} · {{ task.work_package_title }}</p></div><span class="status-pill bg-amber-50 text-amber-600">{{ label(task.status) }}</span></div><p class="mt-3 text-[10px] uppercase text-amber-600">{{ label(task.task_type) }}</p></NuxtLink>
    <p v-if="!filtered.length && !error" class="m-card text-center text-sm text-slate-400">No crew tasks in this view.</p><p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'crew-lead' })
const { apiFetch } = useApi()
const items = ref<any[]>([])
const filter = ref('open')
const error = ref('')
const tabs = ['open', 'all', 'in_progress', 'blocked', 'done']
const label = (value: string) => value?.replaceAll('_', ' ') || 'unknown'
const filtered = computed(() => filter.value === 'all' ? items.value : filter.value === 'open' ? items.value.filter(item => item.status !== 'done') : items.value.filter(item => item.status === filter.value))
onMounted(async () => {
  try { items.value = (await apiFetch<any>('/crew/tasks')).items || [] } catch (e: any) { error.value = e?.data?.detail || e?.message }
})
</script>

