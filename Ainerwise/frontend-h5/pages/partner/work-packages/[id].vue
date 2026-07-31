<template>
  <div class="space-y-4 p-4">
    <NuxtLink to="/partner/work-packages" class="text-xs font-semibold text-blue-600">Back to packages</NuxtLink>
    <div v-if="work" class="m-card"><div class="flex justify-between gap-3"><div><p class="text-[10px] uppercase tracking-wide text-blue-500">Work package</p><h1 class="mt-1 text-lg font-bold text-slate-800">{{ work.title }}</h1></div><span class="status-pill bg-blue-50 text-blue-600">{{ label(work.status) }}</span></div><p class="mt-3 text-xs text-slate-400">{{ work.tasks.length }} field tasks</p></div>
    <div v-for="task in work?.tasks || []" :key="task.id" class="m-card">
      <div class="flex justify-between gap-3"><div><p class="text-sm font-semibold text-slate-800">{{ task.title }}</p><p class="mt-1 text-[10px] uppercase text-blue-500">{{ label(task.task_type) }}</p></div><span class="status-pill bg-slate-100 text-slate-500">{{ label(task.status) }}</span></div>
      <p class="mt-2 text-xs text-slate-400">{{ task.evidence_count }} evidence records</p>
      <div v-for="assignmentItem in task.assignments" :key="assignmentItem.id" class="mt-2 rounded-xl bg-slate-50 p-3 text-xs text-slate-600">{{ assignmentItem.worker_name }}</div>
      <form class="mt-3 space-y-2" @submit.prevent="assign(task.id)">
        <select v-model="assignments[task.id].assignee_user_id" required class="m-input"><option value="">Select worker</option><option v-for="worker in workers.filter(x => x.workspace_id === work.workspace_id)" :key="worker.id" :value="worker.id">{{ worker.full_name || worker.email }}</option></select>
        <select v-model="assignments[task.id].crew_id" class="m-input"><option value="">No crew</option><option v-for="crew in crews.filter(x => x.workspace_id === work.workspace_id)" :key="crew.id" :value="crew.id">{{ crew.name }}</option></select>
        <button class="m-btn-primary">Assign worker</button>
      </form>
      <button class="mt-3 text-xs font-semibold text-blue-600" @click="viewEvidence(task.id)">View evidence</button>
      <div v-if="evidence[task.id]" class="mt-2 space-y-2"><div v-for="item in evidence[task.id]" :key="item.id" class="rounded-xl bg-slate-50 p-3"><p class="text-[10px] font-bold uppercase text-blue-500">{{ item.evidence_type }}</p><p class="mt-1 break-all text-xs text-slate-500">{{ JSON.stringify(item.payload_json) }}</p></div></div>
    </div>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const route = useRoute()
const { apiFetch } = useApi()
const work = ref<any>()
const workers = ref<any[]>([])
const crews = ref<any[]>([])
const assignments = reactive<Record<string, { assignee_user_id: string; crew_id: string }>>({})
const evidence = reactive<Record<string, any[]>>({})
const error = ref('')
const label = (value: string) => value?.replaceAll('_', ' ') || 'unknown'
async function load() {
  const [packageData, workerData, crewData] = await Promise.all([apiFetch<any>(`/partner/field-ops/work-packages/${route.params.id}`), apiFetch<any>('/partner/field-ops/workers'), apiFetch<any>('/partner/field-ops/crews')])
  work.value = packageData
  workers.value = workerData.items || []
  crews.value = crewData.items || []
  for (const task of packageData.tasks) assignments[task.id] ||= { assignee_user_id: '', crew_id: '' }
}
async function assign(taskId: string) {
  try {
    await apiFetch(`/partner/field-ops/tasks/${taskId}/assignments`, { method: 'POST', body: { assignee_user_id: assignments[taskId].assignee_user_id, crew_id: assignments[taskId].crew_id || null } })
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
}
async function viewEvidence(taskId: string) {
  evidence[taskId] = (await apiFetch<any>(`/partner/field-ops/tasks/${taskId}/evidence`)).items || []
}
onMounted(() => load().catch((e: any) => error.value = e?.data?.detail || e?.message))
</script>

