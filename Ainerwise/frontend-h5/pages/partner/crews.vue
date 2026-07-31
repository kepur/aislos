<template>
  <div class="space-y-4 p-4">
    <div><p class="text-[10px] font-bold uppercase tracking-widest text-blue-500">Flexible workforce</p><h1 class="mt-1 text-xl font-bold text-slate-800">Crews</h1></div>
    <form class="m-card space-y-3" @submit.prevent="create"><select v-model="form.workspace_id" required class="m-input"><option value="">Workspace</option><option v-for="item in memberships" :key="item.workspace_id" :value="item.workspace_id">{{ item.workspace_id }}</option></select><input v-model.trim="form.name" required class="m-input" placeholder="Crew name"><input v-model.trim="form.trade" class="m-input" placeholder="Trade"><button class="m-btn-primary">Create crew</button></form>
    <div v-for="crew in crews" :key="crew.id" class="m-card"><div class="flex justify-between gap-3"><div><p class="text-sm font-bold text-slate-800">{{ crew.name }}</p><p class="mt-1 text-xs text-slate-400">{{ crew.trade || 'General crew' }}</p></div><span class="status-pill bg-blue-50 text-blue-600">{{ crew.status }}</span></div><form class="mt-3 space-y-2" @submit.prevent="add(crew)"><select v-model="member[crew.id].user_id" required class="m-input"><option value="">Add worker</option><option v-for="worker in workers.filter(x => x.workspace_id === crew.workspace_id)" :key="worker.id" :value="worker.id">{{ worker.full_name || worker.email }}</option></select><select v-model="member[crew.id].role_in_crew" class="m-input"><option value="worker">Worker</option><option value="lead">Crew lead</option><option value="supervisor">Supervisor</option></select><button class="m-btn-primary">Add member</button></form></div>
    <NuxtLink to="/partner/workers" class="m-card block text-center text-sm font-semibold text-blue-600">View company workers</NuxtLink>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { apiFetch } = useApi()
const { memberships, loadAccess } = usePortalManifest()
const crews = ref<any[]>([])
const workers = ref<any[]>([])
const member = reactive<Record<string, { user_id: string; role_in_crew: string }>>({})
const form = reactive({ workspace_id: '', name: '', trade: '' })
const error = ref('')
async function load() {
  await loadAccess()
  const [crewData, workerData] = await Promise.all([apiFetch<any>('/partner/field-ops/crews'), apiFetch<any>('/partner/field-ops/workers')])
  crews.value = crewData.items || []
  workers.value = workerData.items || []
  form.workspace_id ||= memberships.value[0]?.workspace_id || ''
  for (const crew of crews.value) member[crew.id] ||= { user_id: '', role_in_crew: 'worker' }
}
async function create() {
  await apiFetch('/partner/field-ops/crews', { method: 'POST', body: { ...form, trade: form.trade || null } })
  form.name = ''
  await load()
}
async function add(crew: any) {
  await apiFetch(`/partner/field-ops/crews/${crew.id}/members`, { method: 'POST', body: member[crew.id] })
  member[crew.id].user_id = ''
}
onMounted(() => load().catch((e: any) => error.value = e?.data?.detail || e?.message))
</script>

