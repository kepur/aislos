<template>
  <div class="space-y-4 p-4">
    <div><p class="text-[10px] font-bold uppercase tracking-widest text-blue-500">Company workforce</p><h1 class="mt-1 text-xl font-bold text-slate-800">Workers</h1></div>
    <div v-for="worker in workers" :key="`${worker.id}:${worker.workspace_id}`" class="m-card"><p class="text-sm font-bold text-slate-800">{{ worker.full_name || worker.email }}</p><p class="mt-1 text-xs text-slate-400">{{ worker.email }}</p><p class="mt-3 text-[10px] uppercase text-blue-500">{{ label(worker.membership_type) }} · {{ label(worker.role) }}</p></div>
    <p v-if="!workers.length && !error" class="m-card text-center text-sm text-slate-400">No active workers.</p>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { apiFetch } = useApi()
const workers = ref<any[]>([])
const error = ref('')
const label = (value: string) => value?.replaceAll('_', ' ') || 'unknown'
onMounted(async () => {
  try {
    workers.value = (await apiFetch<any>('/partner/field-ops/workers')).items || []
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
})
</script>

