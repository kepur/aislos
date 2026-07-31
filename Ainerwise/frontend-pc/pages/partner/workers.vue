<template>
  <section class="space-y-5">
    <div><p class="text-xs font-bold uppercase tracking-wider text-blue-300">Company workforce</p><h1 class="mt-1 text-3xl font-bold text-white">Workers</h1><p class="mt-2 text-sm text-slate-400">Only active workers from this Partner Company and an accessible Workspace are shown.</p></div>
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <div v-for="worker in workers" :key="`${worker.id}:${worker.workspace_id}`" class="pc-card">
        <p class="text-lg font-semibold text-white">{{ worker.full_name || worker.email }}</p>
        <p class="mt-1 text-sm text-slate-400">{{ worker.email }}</p>
        <dl class="mt-4 space-y-2 text-xs"><div class="flex justify-between gap-3"><dt class="text-slate-500">Role</dt><dd class="text-blue-300">{{ label(worker.role) }}</dd></div><div class="flex justify-between gap-3"><dt class="text-slate-500">Membership</dt><dd class="text-slate-300">{{ label(worker.membership_type) }}</dd></div><div class="flex justify-between gap-3"><dt class="text-slate-500">Workspace</dt><dd class="max-w-[12rem] truncate text-slate-300">{{ worker.workspace_id }}</dd></div></dl>
      </div>
    </div>
    <p v-if="!workers.length && !error" class="pc-card text-slate-500">No active company workers.</p>
    <p v-if="error" class="pc-card text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'partner-workspace', middleware: ['auth'] })
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

