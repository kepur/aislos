<template>
  <div class="space-y-4 p-4">
    <div><p class="text-[10px] font-bold uppercase tracking-widest text-amber-600">Crew roster</p><h1 class="mt-1 text-xl font-bold text-slate-900">Members</h1></div>
    <div v-for="item in items" :key="`${item.crew_id}:${item.id}`" class="m-card"><div class="flex justify-between gap-3"><div><p class="text-sm font-bold text-slate-800">{{ item.full_name || item.email }}</p><p class="mt-1 text-xs text-slate-400">{{ item.email }}</p></div><span class="status-pill bg-amber-50 text-amber-600">{{ item.role_in_crew }}</span></div><p class="mt-3 text-[10px] uppercase text-amber-600">{{ item.crew_name }}</p></div>
    <p v-if="!items.length && !error" class="m-card text-center text-sm text-slate-400">No active crew members.</p><p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'crew-lead' })
const { apiFetch } = useApi()
const items = ref<any[]>([])
const error = ref('')
onMounted(async () => {
  try { items.value = (await apiFetch<any>('/crew/members')).items || [] } catch (e: any) { error.value = e?.data?.detail || e?.message }
})
</script>

