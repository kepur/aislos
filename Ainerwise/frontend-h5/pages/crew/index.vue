<template>
  <div class="space-y-4 p-4">
    <div><p class="text-[10px] font-bold uppercase tracking-widest text-amber-600">Crew Lead</p><h1 class="mt-1 text-xl font-bold text-slate-900">Site coordination</h1><p class="mt-1 text-xs text-slate-500">Task-driven crew handover, exceptions, evidence and completion.</p></div>
    <div v-if="data" class="grid grid-cols-2 gap-2"><NuxtLink v-for="card in cards" :key="card.label" :to="card.to" class="m-card p-3 text-center"><p class="text-xl font-bold text-amber-600">{{ card.value }}</p><p class="mt-1 text-[10px] text-slate-400">{{ card.label }}</p></NuxtLink></div>
    <div class="m-card"><div class="flex justify-between"><h2 class="text-sm font-bold text-slate-800">Led crews</h2><NuxtLink to="/crew/members" class="text-xs font-semibold text-amber-600">Members</NuxtLink></div><div v-for="crew in data?.crews || []" :key="crew.id" class="mt-3 rounded-xl bg-amber-50 p-3"><p class="text-sm font-semibold text-slate-800">{{ crew.name }}</p><p class="mt-1 text-xs text-slate-400">{{ crew.trade || 'General crew' }}</p></div><p v-if="data && !data.crews.length" class="py-3 text-center text-xs text-slate-400">No led crews.</p></div>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'crew-lead' })
const { apiFetch } = useApi()
const data = ref<any>()
const error = ref('')
const cards = computed(() => data.value ? [
  { label: 'Crew tasks', value: data.value.counts.open_tasks, to: '/crew/tasks' },
  { label: 'Blocked', value: data.value.counts.blocked_tasks, to: '/crew/tasks' },
  { label: 'Members', value: data.value.counts.members, to: '/crew/members' },
  { label: 'Completed', value: data.value.counts.done_tasks, to: '/crew/tasks' },
] : [])
onMounted(async () => {
  try { data.value = await apiFetch('/crew') } catch (e: any) { error.value = e?.data?.detail || e?.message }
})
</script>

