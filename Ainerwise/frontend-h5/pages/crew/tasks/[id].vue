<template>
  <div class="space-y-4 p-4">
    <NuxtLink to="/crew/tasks" class="text-xs font-semibold text-amber-600">Back to crew tasks</NuxtLink>
    <div v-if="task" class="m-card"><div class="flex justify-between gap-3"><div><p class="text-[10px] uppercase tracking-wide text-amber-600">{{ label(task.task_type) }}</p><h1 class="mt-1 text-lg font-bold text-slate-900">{{ task.title }}</h1><p class="mt-1 text-xs text-slate-400">{{ task.work_package.title }}</p></div><span class="status-pill bg-amber-50 text-amber-600">{{ label(task.status) }}</span></div><p v-if="task.safety_notes" class="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-600">{{ task.safety_notes }}</p></div>
    <div v-if="task" class="m-card space-y-3"><h2 class="text-sm font-bold text-slate-800">Task control</h2><div class="grid grid-cols-2 gap-2"><button v-for="status in ['in_progress','paused','blocked','done']" :key="status" class="rounded-xl border border-amber-200 px-3 py-2 text-xs font-semibold text-amber-700" @click="changeStatus(status)">{{ label(status) }}</button></div></div>
    <form v-if="task" class="m-card space-y-3" @submit.prevent="submitAction"><h2 class="text-sm font-bold text-slate-800">Handover / exception / completion</h2><select v-model="actionType" class="m-input"><option value="exceptions">Report exception</option><option value="handover">Submit handover</option><option value="completion">Submit crew completion</option></select><textarea v-model.trim="notes" required rows="4" class="m-input" placeholder="Notes, blockers or completion summary" /><button class="m-btn-primary bg-amber-500">Submit action</button></form>
    <div v-if="task" class="m-card"><h2 class="text-sm font-bold text-slate-800">Crew members</h2><div v-for="member in task.members" :key="member.id" class="mt-2 rounded-xl bg-amber-50 p-3"><p class="text-xs font-semibold text-slate-800">{{ member.full_name || member.email }}</p><p class="mt-1 text-[10px] uppercase text-amber-600">{{ member.role_in_crew }}</p></div></div>
    <div v-if="task" class="m-card"><h2 class="text-sm font-bold text-slate-800">Evidence timeline</h2><div v-for="item in task.evidence" :key="item.id" class="mt-2 rounded-xl bg-slate-50 p-3"><p class="text-[10px] font-bold uppercase text-amber-600">{{ item.evidence_type }}</p><p class="mt-1 break-all text-xs text-slate-500">{{ JSON.stringify(item.payload_json) }}</p></div><p v-if="!task.evidence.length" class="py-3 text-center text-xs text-slate-400">No evidence yet.</p></div>
    <p v-if="notice" class="m-card text-sm text-emerald-600">{{ notice }}</p><p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth', layout: 'crew-lead' })
const route = useRoute()
const { apiFetch } = useApi()
const task = ref<any>()
const actionType = ref('exceptions')
const notes = ref('')
const error = ref('')
const notice = ref('')
const label = (value: string) => value?.replaceAll('_', ' ') || 'unknown'
async function load() { task.value = await apiFetch(`/crew/tasks/${route.params.id}`) }
async function changeStatus(status: string) {
  try {
    await apiFetch(`/crew/tasks/${route.params.id}/status`, { method: 'PATCH', body: { status, offline_version: task.value.offline_version } })
    notice.value = `Task marked ${label(status)}.`
    await load()
  } catch (e: any) { error.value = e?.data?.detail || e?.message }
}
async function submitAction() {
  try {
    await apiFetch(`/crew/tasks/${route.params.id}/${actionType.value}`, { method: 'POST', body: { notes: notes.value } })
    notice.value = 'Crew action submitted.'
    notes.value = ''
    await load()
  } catch (e: any) { error.value = e?.data?.detail || e?.message }
}
onMounted(() => load().catch((e: any) => error.value = e?.data?.detail || e?.message))
</script>

