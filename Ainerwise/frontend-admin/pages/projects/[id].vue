<template>
  <div v-if="project">
    <NuxtLink to="/projects" class="text-sm text-primary-600 hover:underline">&larr; Back to Projects</NuxtLink>

    <div class="mt-4 flex items-center justify-between">
      <h1 class="admin-page-title">{{ project.title }}</h1>
      <StatusBadge :status="project.status" />
    </div>

    <!-- Status Timeline -->
    <div class="mt-6 admin-card">
      <h2 class="admin-section-title mb-4">Project Timeline</h2>
      <div class="flex items-center gap-1 overflow-x-auto pb-2">
        <div
          v-for="(step, i) in statusSteps"
          :key="step.key"
          class="flex items-center shrink-0"
        >
          <div class="flex flex-col items-center">
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
              :class="stepClass(step.key, i)"
            >
              {{ i + 1 }}
            </div>
            <span class="text-xs mt-1 max-w-[72px] text-center leading-tight" :class="currentStepIndex >= i ? 'text-gray-900 font-medium' : 'text-gray-400'">
              {{ step.label }}
            </span>
          </div>
          <div v-if="i < statusSteps.length - 1" class="w-6 h-0.5 mt-[-16px]" :class="currentStepIndex > i ? 'bg-green-500' : 'bg-gray-200'" />
        </div>
      </div>
    </div>

    <div class="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left column: Details -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Project Info -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Project Information</h2>
          <dl class="grid grid-cols-2 gap-3 text-sm">
            <div><dt class="text-gray-500">Region</dt><dd class="font-medium">{{ project.region || '-' }}</dd></div>
            <div><dt class="text-gray-500">Start Date</dt><dd class="font-medium">{{ project.start_date || '-' }}</dd></div>
            <div><dt class="text-gray-500">Expected Delivery</dt><dd class="font-medium">{{ project.expected_delivery_date || '-' }}</dd></div>
            <div><dt class="text-gray-500">Lead ID</dt>
              <dd class="font-medium">
                <NuxtLink v-if="project.lead_id" :to="`leads/${project.lead_id}`" class="text-primary-600 hover:underline">
                  {{ project.lead_id.slice(0, 8) }}...
                </NuxtLink>
                <span v-else>-</span>
              </dd>
            </div>
            <div><dt class="text-gray-500">Buyer Company ID</dt><dd class="font-medium font-mono text-xs">{{ project.buyer_company_id?.slice(0, 8) || '-' }}</dd></div>
            <div><dt class="text-gray-500">Telegram Chat</dt><dd class="font-medium">{{ project.telegram_chat_id || 'Not linked' }}</dd></div>
          </dl>
        </div>

        <!-- Team + Partner Assignment -->
        <div class="admin-card">
          <div class="flex items-center justify-between mb-4">
            <h2 class="admin-section-title">Team</h2>
            <button
              class="px-3 py-1.5 text-xs font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700"
              @click="showAssignForm = !showAssignForm"
            >
              {{ showAssignForm ? 'Cancel' : '+ Assign Partner' }}
            </button>
          </div>

          <!-- Assign Partner Form -->
          <div v-if="showAssignForm" class="mb-4 p-4 rounded-lg bg-gray-50 border space-y-3">
            <div v-if="partnersLoading" class="text-sm text-gray-500">Loading verified partners...</div>
            <template v-else>
              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1">Select Verified Partner</label>
                <select v-model="assignForm.partner_id" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                  <option value="">-- Choose a partner --</option>
                  <option v-for="p in availablePartners" :key="p.id" :value="p.id">
                    {{ p.partner_type }} - {{ p.city || p.country || 'Remote' }}
                    <template v-if="p.skills_json?.length"> ({{ p.skills_json.slice(0, 3).join(', ') }})</template>
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1">Role</label>
                <select v-model="assignForm.role" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                  <option value="installer">Installer</option>
                  <option value="surveyor">Surveyor</option>
                  <option value="engineer">Engineer</option>
                  <option value="commissioning">Commissioning</option>
                  <option value="maintenance">Maintenance</option>
                </select>
              </div>
              <button
                class="px-4 py-2 text-sm font-medium bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-60"
                :disabled="assignLoading || !assignForm.partner_id"
                @click="assignPartner"
              >
                {{ assignLoading ? 'Assigning...' : 'Assign to Project' }}
              </button>
              <div v-if="assignError" class="text-xs text-red-600">{{ assignError }}</div>
            </template>
          </div>

          <!-- Team Members List -->
          <div v-if="project.team_json?.length" class="space-y-2">
            <div v-for="(member, i) in project.team_json" :key="i" class="flex items-center justify-between p-2 rounded-lg bg-gray-50">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold">
                  {{ (member.partner_type || member.name || member.role || '?').charAt(0).toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-900">{{ member.name || member.partner_type || '-' }}</p>
                  <p class="text-xs text-gray-500">{{ member.role || '-' }}
                    <span v-if="member.skills?.length" class="text-gray-400"> &middot; {{ member.skills.slice(0, 3).join(', ') }}</span>
                  </p>
                </div>
              </div>
              <button
                class="text-xs text-red-500 hover:text-red-700 px-2 py-1"
                :disabled="removeLoading === member.partner_id"
                @click="removePartner(member.partner_id)"
              >
                {{ removeLoading === member.partner_id ? '...' : 'Remove' }}
              </button>
            </div>
          </div>
          <p v-else class="text-sm text-gray-500">No team members assigned yet.</p>
        </div>

        <!-- Partner Task Dispatch -->
        <div class="admin-card">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h2 class="admin-section-title">Partner Task Dispatch</h2>
              <p class="mt-1 text-xs text-gray-500">Manual, admin-confirmed dispatch. The Partner receives a mobile task link.</p>
            </div>
            <button
              class="px-3 py-1.5 text-xs font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700"
              @click="showDispatchForm = !showDispatchForm"
            >
              {{ showDispatchForm ? 'Cancel' : '+ Dispatch Task' }}
            </button>
          </div>

          <div v-if="showDispatchForm" class="mb-4 grid grid-cols-1 md:grid-cols-2 gap-3 p-4 rounded-lg bg-gray-50 border">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Assigned Partner</label>
              <select v-model="dispatchForm.partner_id" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option value="">-- Choose assigned partner --</option>
                <option v-for="p in assignedPartners" :key="p.id" :value="p.id">
                  {{ p.partner_type }} - {{ p.city || p.country || 'Remote' }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Task Type</label>
              <select v-model="dispatchForm.task_type" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option v-for="type in taskTypes" :key="type" :value="type">{{ type.replace(/_/g, ' ') }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Due Date</label>
              <input v-model="dispatchForm.due_date" type="date" class="w-full text-sm border border-gray-300 rounded-lg p-2" />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Item / Work Area</label>
              <input v-model="dispatchForm.device_name" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. Main switchboard" />
            </div>
            <label class="flex items-center gap-2 text-xs text-gray-700">
              <input v-model="dispatchForm.covered_by_amc" type="checkbox" />
              Covered by AMC
            </label>
            <div class="md:col-span-2">
              <label class="block text-xs font-medium text-gray-700 mb-1">Instructions</label>
              <textarea v-model="dispatchForm.notes" rows="3" class="w-full text-sm border border-gray-300 rounded-lg p-2" />
            </div>
            <div class="md:col-span-2 flex items-center gap-3">
              <button
                class="px-4 py-2 text-sm font-medium bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-60"
                :disabled="dispatchLoading || !dispatchForm.partner_id || !dispatchForm.task_type"
                @click="dispatchTask"
              >
                {{ dispatchLoading ? 'Dispatching...' : 'Confirm & Dispatch' }}
              </button>
              <span v-if="dispatchError" class="text-xs text-red-600">{{ dispatchError }}</span>
            </div>
          </div>

          <div v-if="dispatches.length" class="space-y-2">
            <div v-for="task in dispatches" :key="task.id" class="flex items-start justify-between gap-3 rounded-lg bg-gray-50 p-3">
              <div>
                <p class="text-sm font-medium capitalize text-gray-900">{{ task.task_type?.replace(/_/g, ' ') }}</p>
                <p class="mt-0.5 text-xs text-gray-500">{{ task.device_name || 'General project task' }} · Due {{ task.due_date || 'not set' }}</p>
              </div>
              <StatusBadge :status="task.status" />
            </div>
          </div>
          <p v-else class="text-sm text-gray-500">No Partner tasks dispatched yet.</p>
        </div>

        <!-- Project Plan -->
        <div class="admin-card">
          <div class="flex items-start justify-between gap-3 mb-4">
            <div>
              <h2 class="admin-section-title">Agent Project Access</h2>
              <p class="mt-1 text-xs text-gray-500">Least-privilege project_data access. Support triage and Mission workers cannot read this project until granted.</p>
            </div>
            <NuxtLink to="/agent-missions" class="text-xs font-medium text-primary-600 hover:underline">Mission Control</NuxtLink>
          </div>
          <div class="grid gap-2 sm:grid-cols-2">
            <label v-for="grant in projectAgentGrants" :key="grant.agent_slug" class="flex items-center justify-between gap-3 rounded-lg bg-gray-50 p-3">
              <span><span class="block text-sm font-medium text-gray-800">{{ grant.name }}</span><span class="block text-[10px] text-gray-400">{{ grant.agent_slug }} · {{ grant.status }}</span></span>
              <input
                type="checkbox"
                :checked="grant.granted"
                :disabled="grantLoading === grant.agent_slug"
                @change="toggleAgentGrant(grant, $event)"
              />
            </label>
          </div>
        </div>

        <!-- Project Plan -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Project Plan</h2>
          <div v-if="project.project_plan_json">
            <div v-for="(value, key) in project.project_plan_json" :key="key" class="mb-2">
              <p class="text-xs font-semibold uppercase text-gray-500">{{ key }}</p>
              <p class="text-sm text-gray-700">{{ typeof value === 'object' ? JSON.stringify(value) : value }}</p>
            </div>
          </div>
          <p v-else class="text-sm text-gray-500">No project plan defined yet.</p>
        </div>
      </div>

      <!-- Right column: Actions -->
      <div class="space-y-6">
        <!-- Status Workflow -->
        <StatusWorkflow
          :current-status="project.status"
          entity="project"
          :loading="statusLoading"
          @transition="handleStatusChange"
        />

        <!-- Notes -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Admin Notes</h2>
          <textarea
            v-model="notes"
            rows="5"
            class="w-full text-sm border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Add notes about this project..."
          />
          <button
            class="mt-2 px-4 py-1.5 text-xs font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            :disabled="notesLoading"
            @click="saveNotes"
          >
            {{ notesLoading ? 'Saving...' : 'Save Notes' }}
          </button>
        </div>

        <!-- Meta -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Details</h2>
          <dl class="text-xs space-y-2">
            <div class="flex justify-between"><dt class="text-gray-500">ID</dt><dd class="font-mono">{{ project.id.slice(0, 8) }}...</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Created</dt><dd>{{ new Date(project.created_at).toLocaleString() }}</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Updated</dt><dd>{{ new Date(project.updated_at).toLocaleString() }}</dd></div>
          </dl>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="text-center py-12 text-gray-500">Loading...</div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const route = useRoute()
const { apiFetch } = useApi()
const project = ref<any>(null)
const notes = ref('')
const statusLoading = ref(false)
const notesLoading = ref(false)
const projectAgentGrants = ref<any[]>([])
const grantLoading = ref<string | null>(null)

// Partner assignment state
const showAssignForm = ref(false)
const availablePartners = ref<any[]>([])
const partnersLoading = ref(false)
const assignLoading = ref(false)
const assignError = ref<string | null>(null)
const removeLoading = ref<string | null>(null)
const showDispatchForm = ref(false)
const dispatches = ref<any[]>([])
const dispatchLoading = ref(false)
const dispatchError = ref<string | null>(null)
const assignForm = reactive({
  partner_id: '',
  role: 'installer',
})
const taskTypes = ['site_survey', 'installation', 'testing', 'commissioning', 'inspection', 'calibration', 'maintenance']
const dispatchForm = reactive({
  partner_id: '',
  task_type: 'installation',
  due_date: '',
  device_name: '',
  notes: '',
  covered_by_amc: false,
})
const assignedPartners = computed(() => {
  const ids = new Set((project.value?.team_json || []).map((member: any) => member.partner_id))
  return availablePartners.value.filter(partner => ids.has(partner.id))
})

const statusSteps = [
  { key: 'planning', label: 'Planning' },
  { key: 'site_survey', label: 'Site Survey' },
  { key: 'quotation_confirmed', label: 'Quote OK' },
  { key: 'procurement', label: 'Procurement' },
  { key: 'delivery', label: 'Delivery' },
  { key: 'installation', label: 'Installation' },
  { key: 'testing', label: 'Testing' },
  { key: 'handover', label: 'Handover' },
  { key: 'maintenance', label: 'Maintenance' },
  { key: 'closed', label: 'Closed' },
]

const currentStepIndex = computed(() => {
  if (!project.value) return -1
  return statusSteps.findIndex(s => s.key === project.value.status)
})

function stepClass(key: string, index: number) {
  if (key === project.value?.status) return 'bg-primary-600 text-white'
  if (currentStepIndex.value > index) return 'bg-green-500 text-white'
  return 'bg-gray-200 text-gray-500'
}

onMounted(async () => {
  try {
    project.value = await apiFetch<any>(`/projects/${route.params.id}`)
    notes.value = project.value?.notes || ''
  } catch {}
  loadPartners()
  loadDispatches()
  loadAgentGrants()
})

async function loadPartners() {
  partnersLoading.value = true
  try {
    const res = await apiFetch<any>('/service-partners?verification_status=verified&limit=100')
    availablePartners.value = res.items || []
  } catch {
    availablePartners.value = []
  } finally {
    partnersLoading.value = false
  }
}

async function assignPartner() {
  if (!assignForm.partner_id) return
  assignLoading.value = true
  assignError.value = null
  try {
    project.value = await apiFetch<any>(`/projects/${route.params.id}/assign-partner`, {
      method: 'POST',
      body: {
        partner_id: assignForm.partner_id,
        role: assignForm.role,
      },
    })
    showAssignForm.value = false
    assignForm.partner_id = ''
    assignForm.role = 'installer'
  } catch (e: any) {
    assignError.value = e?.data?.detail || e?.message || 'Failed to assign partner'
    console.error('Assign partner failed:', e)
  } finally {
    assignLoading.value = false
  }
}

async function removePartner(partnerId: string) {
  if (!partnerId) return
  removeLoading.value = partnerId
  try {
    project.value = await apiFetch<any>(`/projects/${route.params.id}/team/${partnerId}`, {
      method: 'DELETE',
    })
  } catch (e: any) {
    console.error('Remove partner failed:', e)
  } finally {
    removeLoading.value = null
  }
}

async function loadDispatches() {
  try {
    const response = await apiFetch<any>(`/projects/${route.params.id}/dispatches`)
    dispatches.value = response.items || []
  } catch {
    dispatches.value = []
  }
}

async function loadAgentGrants() {
  try {
    const response = await apiFetch<any>(`/admin/projects/${route.params.id}/agent-grants`)
    projectAgentGrants.value = response.items || []
  } catch {
    projectAgentGrants.value = []
  }
}

async function setAgentGrant(grant: any, granted: boolean) {
  grantLoading.value = grant.agent_slug
  try {
    await apiFetch(`/admin/projects/${route.params.id}/agent-grants`, {
      method: 'POST',
      body: { agent_slug: grant.agent_slug, granted },
    })
    await loadAgentGrants()
  } finally {
    grantLoading.value = null
  }
}

function toggleAgentGrant(grant: any, event: Event) {
  const target = event.target as HTMLInputElement
  setAgentGrant(grant, target.checked)
}

async function dispatchTask() {
  dispatchLoading.value = true
  dispatchError.value = null
  try {
    await apiFetch(`/projects/${route.params.id}/dispatch`, {
      method: 'POST',
      body: {
        ...dispatchForm,
        due_date: dispatchForm.due_date || null,
        device_name: dispatchForm.device_name || null,
        notes: dispatchForm.notes || null,
      },
    })
    showDispatchForm.value = false
    dispatchForm.partner_id = ''
    dispatchForm.task_type = 'installation'
    dispatchForm.due_date = ''
    dispatchForm.device_name = ''
    dispatchForm.notes = ''
    dispatchForm.covered_by_amc = false
    await loadDispatches()
  } catch (e: any) {
    dispatchError.value = e?.data?.detail || e?.message || 'Task dispatch failed'
  } finally {
    dispatchLoading.value = false
  }
}

async function handleStatusChange(newStatus: string) {
  statusLoading.value = true
  try {
    project.value = await apiFetch<any>(`/projects/${route.params.id}/status`, {
      method: 'PATCH',
      body: { status: newStatus },
    })
  } catch (e: any) {
    console.error('Status update failed:', e)
  } finally {
    statusLoading.value = false
  }
}

async function saveNotes() {
  notesLoading.value = true
  try {
    project.value = await apiFetch<any>(`/projects/${route.params.id}/notes`, {
      method: 'PATCH',
      body: { notes: notes.value },
    })
  } catch (e: any) {
    console.error('Notes update failed:', e)
  } finally {
    notesLoading.value = false
  }
}
</script>
