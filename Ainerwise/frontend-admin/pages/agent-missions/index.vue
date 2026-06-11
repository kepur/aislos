<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="admin-page-title">Agent Missions</h1>
        <p class="admin-page-desc">Project-scoped Agent Teams. Plans grant access only after admin approval; final reports stay preliminary until reviewed.</p>
      </div>
      <div class="flex gap-2">
        <select v-model="statusFilter" class="input-field max-w-52" @change="load">
          <option value="">All statuses</option>
          <option v-for="status in statuses" :key="status" :value="status">{{ formatStatus(status) }}</option>
        </select>
        <button class="btn-primary px-4 py-2 text-sm" :disabled="busy" @click="load">Refresh</button>
      </div>
    </div>

    <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ error }}</div>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.9fr)]">
      <div class="admin-panel overflow-x-auto">
        <table class="admin-table w-full text-sm">
          <thead>
            <tr>
              <th class="text-left px-4 py-3">Mission</th>
              <th class="text-left px-4 py-3">AI Team</th>
              <th class="text-left px-4 py-3">Status</th>
              <th class="text-left px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="mission in missions"
              :key="mission.id"
              class="border-b align-top cursor-pointer hover:bg-gray-50"
              :class="selected?.id === mission.id ? 'bg-cyan-50/60' : ''"
              @click="selectMission(mission)"
            >
              <td class="px-4 py-3 max-w-md">
                <p class="font-medium text-gray-900">{{ mission.goal }}</p>
                <p class="mt-1 text-xs text-gray-500">Project {{ mission.project_id.slice(0, 8) }} · {{ formatDate(mission.created_at) }}</p>
              </td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap gap-1">
                  <span v-for="agent in mission.agents" :key="agent" class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-600">{{ agent }}</span>
                  <span v-if="!mission.agents?.length" class="text-xs text-gray-400">Not planned</span>
                </div>
              </td>
              <td class="px-4 py-3"><StatusBadge :status="mission.status" /></td>
              <td class="px-4 py-3 whitespace-nowrap" @click.stop>
                <button
                  v-if="canPlan(mission)"
                  class="btn-primary px-3 py-1.5 text-xs"
                  :disabled="busy"
                  @click="act(mission, 'plan')"
                >Create Plan</button>
                <button
                  v-else-if="mission.status === 'plan_review'"
                  class="btn-primary px-3 py-1.5 text-xs"
                  :disabled="busy"
                  @click="act(mission, 'approve-plan')"
                >Approve Plan & Grants</button>
                <button
                  v-else-if="canRun(mission)"
                  class="btn-primary px-3 py-1.5 text-xs"
                  :disabled="busy"
                  @click="act(mission, 'run')"
                >{{ mission.status === 'report_rejected' ? 'Run Revised Report' : 'Run Agent Team' }}</button>
                <NuxtLink
                  v-else-if="mission.status === 'in_review'"
                  to="/ai-reviews?target_type=mission_final_report"
                  class="text-xs font-medium text-cyan-600 hover:underline"
                >Review Final Report</NuxtLink>
                <span v-else class="text-xs text-gray-400">{{ formatStatus(mission.status) }}</span>
              </td>
            </tr>
            <tr v-if="!missions.length"><td colspan="4" class="px-4 py-10 text-center text-gray-500">No Agent Missions yet. Customers request them from Project Space.</td></tr>
          </tbody>
        </table>
      </div>

      <aside class="admin-panel p-5">
        <template v-if="selected">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-wider text-gray-400">Mission Detail</p>
              <h2 class="mt-1 font-semibold text-gray-900">{{ selected.goal }}</h2>
            </div>
            <StatusBadge :status="selected.status" />
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <NuxtLink :to="`/projects/${selected.project_id}`" class="text-xs font-medium text-cyan-600 hover:underline">Open project</NuxtLink>
            <NuxtLink v-if="selected.review_id" to="/ai-reviews" class="text-xs font-medium text-cyan-600 hover:underline">Open review queue</NuxtLink>
          </div>

          <section v-if="selected.plan_json" class="mt-5">
            <h3 class="text-sm font-semibold text-gray-800">Approved Workflow Boundary</h3>
            <p class="mt-1 text-xs text-amber-700">Plan approval grants selected Agents project_data access to this project only.</p>
            <pre class="mt-2 max-h-64 overflow-auto rounded-lg bg-gray-50 p-3 text-xs text-gray-600 whitespace-pre-wrap">{{ pretty(selected.plan_json) }}</pre>
          </section>

          <section v-if="selected.tasks?.length" class="mt-5">
            <h3 class="text-sm font-semibold text-gray-800">Task Queue</h3>
            <div class="mt-2 space-y-2">
              <div v-for="task in selected.tasks" :key="task.id" class="rounded-lg border border-gray-100 p-3">
                <div class="flex items-start justify-between gap-2">
                  <div><p class="text-xs font-medium text-gray-800">{{ task.title }}</p><p class="text-[10px] text-gray-400">{{ task.agent_slug }}</p></div>
                  <StatusBadge :status="task.status" />
                </div>
                <pre v-if="task.output_json" class="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-[10px] text-gray-500">{{ pretty(task.output_json) }}</pre>
              </div>
            </div>
          </section>

          <section v-if="selected.final_report_json" class="mt-5">
            <h3 class="text-sm font-semibold text-gray-800">Preliminary Final Report</h3>
            <pre class="mt-2 max-h-80 overflow-auto rounded-lg bg-gray-50 p-3 text-xs text-gray-600 whitespace-pre-wrap">{{ pretty(selected.final_report_json) }}</pre>
          </section>
        </template>
        <p v-else class="py-10 text-center text-sm text-gray-500">Select a mission to inspect its plan, queue and report.</p>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const missions = ref<any[]>([])
const selected = ref<any>(null)
const statusFilter = ref('')
const busy = ref(false)
const error = ref('')
const statuses = ['requested', 'plan_review', 'plan_rejected', 'approved', 'in_review', 'report_rejected', 'completed']

const formatStatus = (value: string) => value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
const formatDate = (value: string) => new Date(value).toLocaleString()
const pretty = (value: any) => JSON.stringify(value, null, 2)
const canPlan = (mission: any) => ['requested', 'plan_rejected'].includes(mission.status)
const canRun = (mission: any) => ['approved', 'report_rejected'].includes(mission.status)

async function load() {
  const query = statusFilter.value ? `?status=${statusFilter.value}` : ''
  error.value = ''
  try {
    const res = await apiFetch<any>(`/admin/agent-missions${query}`)
    missions.value = res.items || []
    if (selected.value) {
      const current = missions.value.find(item => item.id === selected.value.id)
      if (current) await selectMission(current)
    }
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to load Agent Missions.'
  }
}

async function selectMission(mission: any) {
  error.value = ''
  try {
    selected.value = await apiFetch<any>(`/admin/agent-missions/${mission.id}`)
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to load mission detail.'
  }
}

async function act(mission: any, action: 'plan' | 'approve-plan' | 'run') {
  busy.value = true
  error.value = ''
  try {
    await apiFetch(`/admin/agent-missions/${mission.id}/${action}`, { method: 'POST' })
    await load()
    const updated = missions.value.find(item => item.id === mission.id)
    if (updated) await selectMission(updated)
  } catch (e: any) {
    error.value = e?.data?.detail || `Unable to ${action.replace('-', ' ')}.`
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
