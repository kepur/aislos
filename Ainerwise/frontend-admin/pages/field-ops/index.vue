<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div><h1 class="admin-page-title">Field Operations / Dispatch</h1><p class="admin-page-desc">WorkPackage, Crew, FieldTask, Assignment and Evidence control center.</p></div>
      <select v-model="workspaceId" class="input-field max-w-sm" @change="refresh">
        <option value="">All workspaces</option>
        <option v-for="item in memberships" :key="item.workspace_id" :value="item.workspace_id">{{ item.workspace_id }}</option>
      </select>
    </div>
    <p v-if="error" class="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">{{ error }}</p>

    <div class="grid gap-4 md:grid-cols-3">
      <button v-for="card in cards" :key="card.key" class="admin-panel p-5 text-left" :class="tab === card.key ? 'border-cyan-400/40' : ''" @click="tab = card.key">
        <p class="text-xs uppercase tracking-wider text-slate-500">{{ card.label }}</p><p class="mt-2 text-3xl font-bold text-white">{{ card.value }}</p>
      </button>
    </div>

    <template v-if="tab === 'packages'">
      <form class="admin-panel grid gap-3 p-5 lg:grid-cols-4" @submit.prevent="createPackage">
        <select v-model="packageForm.workspace_id" required class="input-field"><option value="">Workspace *</option><option v-for="item in memberships" :key="item.workspace_id" :value="item.workspace_id">{{ item.workspace_id }}</option></select>
        <select v-model="packageForm.partner_company_id" class="input-field"><option value="">Unassigned partner</option><option v-for="partner in assignablePartners" :key="partner.id" :value="partner.company_id">{{ partner.partner_type }} · {{ partner.city || partner.company_id }}</option></select>
        <select v-model="packageForm.project_id" class="input-field"><option value="">No linked project</option><option v-for="project in projects" :key="project.id" :value="project.id">{{ project.title }}</option></select>
        <input v-model.trim="packageForm.title" required class="input-field" placeholder="Work package title *">
        <input v-model.trim="packageForm.trade" class="input-field" placeholder="Trade">
        <input v-model="packageForm.planned_start" type="date" class="input-field">
        <input v-model="packageForm.planned_end" type="date" class="input-field">
        <button class="btn-primary py-2" :disabled="busy">Create work package</button>
      </form>

      <div class="grid gap-5 xl:grid-cols-[0.75fr_1.25fr]">
        <div class="space-y-3">
          <button v-for="item in packages" :key="item.id" class="admin-panel block w-full p-4 text-left" :class="selected?.id === item.id ? 'border-cyan-400/40' : ''" @click="openPackage(item.id)">
            <div class="flex justify-between gap-3"><div><p class="font-semibold text-white">{{ item.title }}</p><p class="mt-1 text-xs text-slate-500">{{ item.trade || 'general delivery' }}</p></div><StatusBadge :status="item.status" /></div>
          </button>
          <p v-if="!packages.length" class="admin-panel p-5 text-sm text-slate-500">No work packages.</p>
        </div>

        <div v-if="selected" class="space-y-4">
          <div class="admin-panel p-5"><div class="flex flex-wrap justify-between gap-3"><div><p class="text-xs uppercase tracking-wider text-cyan-400">Selected package</p><h2 class="mt-1 text-xl font-bold text-white">{{ selected.title }}</h2></div><StatusBadge :status="selected.status" /></div><p class="mt-3 text-sm text-slate-500">{{ selected.tasks.length }} field tasks</p></div>
          <form class="admin-panel grid gap-3 p-5 md:grid-cols-2" @submit.prevent="createTask">
            <input v-model.trim="taskForm.title" required class="input-field" placeholder="Task title *">
            <input v-model.trim="taskForm.task_type" required class="input-field" placeholder="Task type *">
            <input v-model.trim="taskForm.required_skill" class="input-field" placeholder="Required skill">
            <input v-model="taskForm.schedule_start" type="datetime-local" class="input-field">
            <textarea v-model.trim="taskForm.safety_notes" class="input-field md:col-span-2" placeholder="Safety notes" />
            <button class="btn-primary py-2 md:col-span-2" :disabled="busy">Create field task</button>
          </form>
          <article v-for="task in selected.tasks" :key="task.id" class="admin-panel p-5">
            <div class="flex flex-wrap justify-between gap-3"><div><p class="text-xs uppercase text-cyan-400">{{ task.task_type }}</p><h3 class="mt-1 font-semibold text-white">{{ task.title }}</h3><p class="mt-1 text-xs text-slate-500">{{ task.evidence_count }} evidence records</p></div><StatusBadge :status="task.status" /></div>
            <div v-for="assignmentItem in task.assignments" :key="assignmentItem.id" class="mt-3 rounded-lg border border-white/5 p-3 text-sm text-slate-300">{{ assignmentItem.worker_name }} · {{ assignmentItem.status }}</div>
            <form class="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]" @submit.prevent="assign(task.id)">
              <select v-model="assignments[task.id].assignee_user_id" required class="input-field"><option value="">Worker</option><option v-for="worker in workers" :key="worker.id" :value="worker.id">{{ worker.full_name || worker.email }}</option></select>
              <select v-model="assignments[task.id].crew_id" class="input-field"><option value="">No crew</option><option v-for="crew in crews" :key="crew.id" :value="crew.id">{{ crew.name }}</option></select>
              <button class="btn-primary py-2" :disabled="busy">Assign</button>
            </form>
            <button class="mt-4 text-xs font-semibold text-cyan-300" @click="loadEvidence(task.id)">Inspect evidence</button>
            <div v-if="evidence[task.id]" class="mt-3 grid gap-2 md:grid-cols-2"><div v-for="item in evidence[task.id]" :key="item.id" class="rounded-lg border border-white/5 p-3"><p class="text-xs font-semibold uppercase text-cyan-300">{{ item.evidence_type }}</p><pre class="mt-2 overflow-auto whitespace-pre-wrap text-xs text-slate-500">{{ JSON.stringify(item.payload_json, null, 2) }}</pre></div></div>
          </article>
        </div>
      </div>
    </template>

    <template v-else-if="tab === 'crews'">
      <form class="admin-panel grid gap-3 p-5 md:grid-cols-4" @submit.prevent="createCrew">
        <select v-model="crewForm.workspace_id" required class="input-field"><option value="">Workspace *</option><option v-for="item in memberships" :key="item.workspace_id" :value="item.workspace_id">{{ item.workspace_id }}</option></select>
        <select v-model="crewForm.partner_company_id" class="input-field"><option value="">Unassigned company</option><option v-for="partner in assignablePartners" :key="partner.id" :value="partner.company_id">{{ partner.partner_type }} · {{ partner.company_id }}</option></select>
        <input v-model.trim="crewForm.name" required class="input-field" placeholder="Crew name *">
        <button class="btn-primary py-2" :disabled="busy">Create crew</button>
      </form>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"><article v-for="crew in crews" :key="crew.id" class="admin-panel p-5"><div class="flex justify-between gap-3"><div><p class="font-semibold text-white">{{ crew.name }}</p><p class="mt-1 text-xs text-slate-500">{{ crew.trade || 'General crew' }}</p></div><StatusBadge :status="crew.status" /></div><form class="mt-4 space-y-2" @submit.prevent="addCrewMember(crew.id)"><select v-model="crewMembers[crew.id].user_id" required class="input-field"><option value="">Worker</option><option v-for="worker in workers" :key="worker.id" :value="worker.id">{{ worker.full_name || worker.email }}</option></select><select v-model="crewMembers[crew.id].role_in_crew" class="input-field"><option value="worker">Worker</option><option value="lead">Lead</option><option value="supervisor">Supervisor</option></select><button class="btn-primary w-full py-2">Add member</button></form></article></div>
    </template>

    <template v-else>
      <div class="admin-panel overflow-hidden"><table class="admin-table"><thead><tr><th>Worker</th><th>Role</th><th>Membership</th><th>Company</th></tr></thead><tbody><tr v-for="worker in workers" :key="worker.id"><td><p class="font-medium text-white">{{ worker.full_name || worker.email }}</p><p class="text-xs text-slate-500">{{ worker.email }}</p></td><td>{{ worker.role }}</td><td>{{ worker.membership_type }}</td><td>{{ worker.company_id || 'unassigned' }}</td></tr></tbody></table></div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })
const { apiFetch } = useApi()
const { memberships, activeWorkspaceId, loadAccess } = usePortalManifest()
const tab = ref('packages')
const workspaceId = ref('')
const packages = ref<any[]>([])
const crews = ref<any[]>([])
const workers = ref<any[]>([])
const partners = ref<any[]>([])
const projects = ref<any[]>([])
const selected = ref<any>()
const assignments = reactive<Record<string, { assignee_user_id: string; crew_id: string }>>({})
const crewMembers = reactive<Record<string, { user_id: string; role_in_crew: string }>>({})
const evidence = reactive<Record<string, any[]>>({})
const busy = ref(false)
const error = ref('')
const packageForm = reactive({ workspace_id: '', project_id: '', partner_company_id: '', title: '', trade: '', planned_start: '', planned_end: '' })
const taskForm = reactive({ title: '', task_type: 'installation', required_skill: '', schedule_start: '', safety_notes: '' })
const crewForm = reactive({ workspace_id: '', partner_company_id: '', name: '', trade: '' })
const assignablePartners = computed(() => partners.value.filter(item => item.company_id))
const cards = computed(() => [{ key: 'packages', label: 'Work packages', value: packages.value.length }, { key: 'crews', label: 'Crews', value: crews.value.length }, { key: 'workers', label: 'Workers', value: workers.value.length }])
async function refresh() {
  error.value = ''
  const scope = workspaceId.value ? `?workspace_id=${encodeURIComponent(workspaceId.value)}` : ''
  try {
    const projectScope = workspaceId.value ? `&workspace_id=${encodeURIComponent(workspaceId.value)}` : ''
    const calls: Promise<any>[] = [apiFetch(`/admin/field-ops/work-packages${scope}`), apiFetch('/service-partners?limit=100'), apiFetch(`/projects?limit=100${projectScope}`)]
    if (workspaceId.value) calls.push(apiFetch(`/admin/field-ops/crews?workspace_id=${workspaceId.value}`), apiFetch(`/admin/field-ops/workers?workspace_id=${workspaceId.value}`))
    const [packageData, partnerData, projectData, crewData, workerData] = await Promise.all(calls)
    packages.value = packageData.items || []
    partners.value = partnerData.items || []
    projects.value = projectData.items || []
    crews.value = crewData?.items || []
    workers.value = workerData?.items || []
    packageForm.workspace_id = workspaceId.value || packageForm.workspace_id
    crewForm.workspace_id = workspaceId.value || crewForm.workspace_id
    for (const crew of crews.value) crewMembers[crew.id] ||= { user_id: '', role_in_crew: 'worker' }
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message
  }
}
async function openPackage(id: string) {
  selected.value = await apiFetch(`/admin/field-ops/work-packages/${id}`)
  for (const task of selected.value.tasks) assignments[task.id] ||= { assignee_user_id: '', crew_id: '' }
}
async function run(action: () => Promise<any>) {
  busy.value = true
  error.value = ''
  try { await action() } catch (e: any) { error.value = e?.data?.detail || e?.message } finally { busy.value = false }
}
const createPackage = () => run(async () => { await apiFetch('/admin/field-ops/work-packages', { method: 'POST', body: { ...packageForm, project_id: packageForm.project_id || null, partner_company_id: packageForm.partner_company_id || null, trade: packageForm.trade || null, planned_start: packageForm.planned_start || null, planned_end: packageForm.planned_end || null } }); packageForm.title = ''; await refresh() })
const createTask = () => selected.value && run(async () => { await apiFetch(`/admin/field-ops/work-packages/${selected.value.id}/tasks`, { method: 'POST', body: { work_package_id: selected.value.id, ...taskForm, required_skill: taskForm.required_skill || null, schedule_start: taskForm.schedule_start || null, safety_notes: taskForm.safety_notes || null } }); taskForm.title = ''; await openPackage(selected.value.id) })
const createCrew = () => run(async () => { await apiFetch('/admin/field-ops/crews', { method: 'POST', body: { ...crewForm, partner_company_id: crewForm.partner_company_id || null, trade: crewForm.trade || null } }); crewForm.name = ''; await refresh() })
const assign = (taskId: string) => run(async () => { await apiFetch(`/admin/field-ops/tasks/${taskId}/assignments`, { method: 'POST', body: { assignee_user_id: assignments[taskId].assignee_user_id, crew_id: assignments[taskId].crew_id || null } }); await openPackage(selected.value.id) })
const addCrewMember = (crewId: string) => run(async () => { await apiFetch(`/admin/field-ops/crews/${crewId}/members`, { method: 'POST', body: crewMembers[crewId] }); crewMembers[crewId].user_id = '' })
async function loadEvidence(taskId: string) { evidence[taskId] = (await apiFetch<any>(`/admin/field-ops/tasks/${taskId}/evidence`)).items || [] }
onMounted(async () => { await loadAccess(); workspaceId.value = activeWorkspaceId.value || memberships.value[0]?.workspace_id || ''; await refresh() })
</script>
