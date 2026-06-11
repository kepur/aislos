<template>
  <div v-if="lead">
    <NuxtLink to="leads" class="text-sm text-primary-600 hover:underline">&larr; Back to Leads</NuxtLink>

    <div class="mt-4 flex items-center justify-between">
      <h1 class="admin-page-title">Lead Detail</h1>
      <StatusBadge :status="lead.status" />
    </div>

    <div class="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left column: Details -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Contact Info -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Contact Information</h2>
          <dl class="grid grid-cols-2 gap-3 text-sm">
            <div><dt class="text-gray-500">Name</dt><dd class="font-medium">{{ lead.contact_name || '-' }}</dd></div>
            <div><dt class="text-gray-500">Email</dt><dd class="font-medium">{{ lead.contact_email || '-' }}</dd></div>
            <div><dt class="text-gray-500">Phone</dt><dd class="font-medium">{{ lead.contact_phone || '-' }}</dd></div>
            <div><dt class="text-gray-500">Language</dt><dd class="font-medium">{{ lead.language }}</dd></div>
          </dl>
        </div>

        <!-- Project Info -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Project Information</h2>
          <dl class="grid grid-cols-2 gap-3 text-sm">
            <div><dt class="text-gray-500">Type</dt><dd class="font-medium">{{ lead.project_type || '-' }}</dd></div>
            <div><dt class="text-gray-500">Country</dt><dd class="font-medium">{{ lead.country || '-' }}</dd></div>
            <div><dt class="text-gray-500">City</dt><dd class="font-medium">{{ lead.city || '-' }}</dd></div>
            <div><dt class="text-gray-500">Budget</dt><dd class="font-medium">{{ lead.budget_range || '-' }}</dd></div>
            <div><dt class="text-gray-500">Systems</dt><dd class="font-medium">{{ lead.systems_needed_json?.join(', ') || '-' }}</dd></div>
          </dl>
        </div>

        <!-- Industrial Factory Intake -->
        <div v-if="isIndustrialLead" class="bg-white rounded-xl border border-orange-200 p-6">
          <div class="flex items-start justify-between gap-4 mb-4">
            <div>
              <h2 class="admin-section-title">Factory / Industrial Plant Intake</h2>
              <p class="text-xs text-gray-500 mt-1">Mechanical equipment, OT systems, energy loads, safety boundaries, and lifecycle review.</p>
            </div>
            <span class="px-3 py-1 rounded-full text-xs font-semibold bg-orange-50 text-orange-700">Industrial</span>
          </div>
          <dl class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <dt class="text-gray-500">Production / Machines</dt>
              <dd class="font-medium text-gray-900 mt-1 whitespace-pre-wrap">{{ industrialInfo.production || '-' }}</dd>
            </div>
            <div>
              <dt class="text-gray-500">PLC / SCADA / OT Systems</dt>
              <dd class="font-medium text-gray-900 mt-1 whitespace-pre-wrap">{{ industrialInfo.protocols || industrialInfo.existing || '-' }}</dd>
            </div>
            <div>
              <dt class="text-gray-500">Energy / Utilities</dt>
              <dd class="font-medium text-gray-900 mt-1 whitespace-pre-wrap">{{ industrialInfo.energy || '-' }}</dd>
            </div>
            <div>
              <dt class="text-gray-500">Safety / Access Boundary</dt>
              <dd class="font-medium text-gray-900 mt-1 whitespace-pre-wrap">{{ industrialInfo.safety || '-' }}</dd>
            </div>
          </dl>
          <div class="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800">
            Machine control, safety interlocks, and production downtime risks require engineering review before any final scope or quote.
          </div>
        </div>

        <!-- Description -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Description</h2>
          <p class="text-sm text-gray-600 whitespace-pre-wrap">{{ lead.description || 'No description provided.' }}</p>
        </div>

        <!-- Site Surveys -->
        <div class="admin-card">
          <div class="flex items-center justify-between mb-4">
            <h2 class="admin-section-title">Site Surveys</h2>
            <button
              class="px-3 py-1.5 text-xs font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700"
              @click="showSurveyForm = !showSurveyForm"
            >
              {{ showSurveyForm ? 'Cancel' : '+ New Survey' }}
            </button>
          </div>

          <!-- Create Survey Form -->
          <div v-if="showSurveyForm" class="mb-4 p-4 rounded-lg bg-gray-50 border space-y-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Survey Type</label>
              <select v-model="surveyForm.survey_type" class="w-full text-sm border border-gray-300 rounded-lg p-2">
                <option value="quick">Quick Assessment</option>
                <option value="detailed">Detailed Survey</option>
                <option value="professional">Professional Survey</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1">Area (sqm)</label>
                <input v-model="surveyForm.area" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. 250" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1">Floors</label>
                <input v-model="surveyForm.floors" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. 3" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1">Rooms / Zones</label>
                <input v-model="surveyForm.rooms" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. 12" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-700 mb-1">Building Type</label>
                <input v-model="surveyForm.building_type" type="text" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="e.g. Office" />
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Existing Infrastructure Notes</label>
              <textarea v-model="surveyForm.infrastructure_notes" rows="2" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="Existing KNX wiring, network cabling, etc." />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Additional Notes</label>
              <textarea v-model="surveyForm.notes" rows="2" class="w-full text-sm border border-gray-300 rounded-lg p-2" placeholder="Any other observations..." />
            </div>
            <button
              class="px-4 py-2 text-sm font-medium bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-60"
              :disabled="surveyLoading"
              @click="createSurvey"
            >
              {{ surveyLoading ? 'Creating...' : 'Create Survey' }}
            </button>
          </div>

          <!-- Surveys List -->
          <div v-if="surveys.length" class="space-y-3">
            <div v-for="survey in surveys" :key="survey.id" class="p-3 rounded-lg border bg-gray-50">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 text-xs font-medium rounded-full"
                    :class="{
                      'bg-blue-100 text-blue-700': survey.survey_type === 'quick',
                      'bg-purple-100 text-purple-700': survey.survey_type === 'detailed',
                      'bg-green-100 text-green-700': survey.survey_type === 'professional',
                    }"
                  >{{ survey.survey_type }}</span>
                  <span class="text-xs text-gray-500">{{ new Date(survey.created_at).toLocaleDateString() }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span v-if="survey.completeness_score != null" class="text-xs text-gray-600">
                    Completeness: {{ survey.completeness_score }}%
                  </span>
                  <span v-if="survey.risk_score != null" class="text-xs" :class="survey.risk_score > 0.6 ? 'text-red-600' : 'text-gray-600'">
                    Risk: {{ (survey.risk_score * 100).toFixed(0) }}%
                  </span>
                </div>
              </div>
              <div v-if="survey.survey_json" class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div v-if="survey.survey_json.area"><span class="text-gray-500">Area:</span> {{ survey.survey_json.area }} sqm</div>
                <div v-if="survey.survey_json.floors"><span class="text-gray-500">Floors:</span> {{ survey.survey_json.floors }}</div>
                <div v-if="survey.survey_json.rooms"><span class="text-gray-500">Rooms:</span> {{ survey.survey_json.rooms }}</div>
                <div v-if="survey.survey_json.building_type"><span class="text-gray-500">Type:</span> {{ survey.survey_json.building_type }}</div>
              </div>
              <p v-if="survey.survey_json?.infrastructure_notes" class="text-xs text-gray-600 mt-1">
                <span class="font-medium">Infrastructure:</span> {{ survey.survey_json.infrastructure_notes }}
              </p>
              <p v-if="survey.survey_json?.notes" class="text-xs text-gray-600 mt-1">
                <span class="font-medium">Notes:</span> {{ survey.survey_json.notes }}
              </p>
            </div>
          </div>
          <p v-else class="text-sm text-gray-500">No site surveys yet. Create one to capture site details.</p>
        </div>

        <!-- AI Analysis -->
        <div class="admin-card">
          <div class="flex items-start justify-between gap-4 mb-4">
            <div>
              <h2 class="admin-section-title">AI Analysis</h2>
              <p class="text-xs text-gray-500 mt-1">Preliminary intake review for admin use.</p>
            </div>
            <button
              class="px-3 py-1.5 text-xs font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-60"
              :disabled="aiLoading"
              @click="runAnalysis"
            >
              {{ aiLoading ? 'Analyzing...' : 'Run Analysis' }}
            </button>
          </div>
          <div v-if="lead.ai_analysis_json" class="text-sm">
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-3 text-xs text-yellow-700">
              {{ lead.ai_analysis_json.disclaimer || 'Preliminary recommendation. Final solution requires engineering review and site verification.' }}
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
              <div class="rounded-lg border p-3">
                <p class="text-xs text-gray-500">Classification</p>
                <p class="font-medium text-gray-900 mt-1">{{ lead.ai_analysis_json.classification?.project_class || '-' }}</p>
              </div>
              <div class="rounded-lg border p-3">
                <p class="text-xs text-gray-500">Completeness</p>
                <p class="font-medium text-gray-900 mt-1">{{ lead.ai_analysis_json.completeness?.score ?? '-' }}%</p>
              </div>
              <div class="rounded-lg border p-3">
                <p class="text-xs text-gray-500">Next Status</p>
                <p class="font-medium text-gray-900 mt-1">{{ lead.ai_analysis_json.recommended_status || '-' }}</p>
              </div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              <div class="rounded-lg border p-3 bg-primary-50 border-primary-100">
                <p class="text-xs text-primary-700">Lead Score</p>
                <p class="admin-section-title mt-1">
                  {{ lead.ai_analysis_json.lead_score?.score ?? lead.site_info_json?.lead_score ?? '-' }}
                  <span class="text-sm text-gray-500">
                    / {{ lead.ai_analysis_json.lead_score?.stage || lead.site_info_json?.lead_stage || 'Unscored' }}
                  </span>
                </p>
              </div>
              <div class="rounded-lg border p-3" :class="lead.ai_analysis_json.phase1_requested || lead.site_info_json?.phase1_requested ? 'bg-emerald-50 border-emerald-100' : 'bg-gray-50'">
                <p class="text-xs text-gray-500">Phase-1 Intent</p>
                <p class="admin-section-title mt-1">
                  {{ lead.ai_analysis_json.phase1_requested || lead.site_info_json?.phase1_requested ? 'Requested' : 'Not requested yet' }}
                </p>
              </div>
            </div>
            <div v-if="lead.ai_analysis_json.recommended_next_action" class="mb-4">
              <h3 class="text-xs font-semibold uppercase text-gray-500 mb-1">Recommended Next Action</h3>
              <p class="text-gray-700">{{ lead.ai_analysis_json.recommended_next_action }}</p>
            </div>
            <div v-if="lead.ai_analysis_json.proposal_tiers?.length" class="mb-4">
              <h3 class="text-xs font-semibold uppercase text-gray-500 mb-2">Preliminary Proposal Tiers</h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div
                  v-for="tier in lead.ai_analysis_json.proposal_tiers"
                  :key="tier.tier"
                  class="rounded-lg border p-3 bg-gray-50"
                >
                  <p class="font-medium text-gray-900">{{ tier.name }} · {{ tier.intelligence_level }}</p>
                  <p class="text-xs text-gray-600 mt-1">Device: {{ Array.isArray(tier.device_cost_estimate) ? `${tier.device_cost_estimate[0]}-${tier.device_cost_estimate[1]} EUR` : tier.device_cost_estimate }}</p>
                  <p class="text-xs text-gray-600 mt-1">Risk: {{ tier.risk_level }} · {{ tier.complexity }}</p>
                  <p class="text-xs text-gray-500 mt-2">{{ tier.next_step }}</p>
                </div>
              </div>
            </div>
            <div v-if="lead.ai_analysis_json.completeness?.questions?.length" class="mb-4">
              <h3 class="text-xs font-semibold uppercase text-gray-500 mb-2">Missing Information Questions</h3>
              <ul class="space-y-1">
                <li v-for="question in lead.ai_analysis_json.completeness.questions" :key="question" class="text-gray-700">
                  {{ question }}
                </li>
              </ul>
            </div>
            <div v-if="lead.ai_analysis_json.risks?.length" class="mb-4">
              <h3 class="text-xs font-semibold uppercase text-gray-500 mb-2">Risk Notes</h3>
              <div class="space-y-2">
                <div v-for="risk in lead.ai_analysis_json.risks" :key="`${risk.area}-${risk.note}`" class="rounded-lg bg-gray-50 p-3">
                  <p class="font-medium text-gray-900">{{ risk.area }} / {{ risk.level }}</p>
                  <p class="text-gray-600 mt-1">{{ risk.note }}</p>
                </div>
              </div>
            </div>
            <div v-if="lead.ai_analysis_json.matched_solutions?.length" class="mb-4">
              <h3 class="text-xs font-semibold uppercase text-gray-500 mb-2">Matched Solutions</h3>
              <div class="flex flex-wrap gap-2">
                <NuxtLink
                  v-for="solution in lead.ai_analysis_json.matched_solutions"
                  :key="solution.id"
                  :to="`/solutions/${solution.slug}`"
                  class="px-3 py-1.5 rounded-lg bg-primary-50 text-primary-700 text-xs font-medium hover:bg-primary-100"
                >
                  {{ solution.title }}
                </NuxtLink>
              </div>
            </div>
            <details class="mt-4">
              <summary class="cursor-pointer text-xs font-medium text-gray-500">Raw JSON</summary>
              <pre class="bg-gray-50 p-4 rounded overflow-auto text-xs mt-2">{{ JSON.stringify(lead.ai_analysis_json, null, 2) }}</pre>
            </details>
          </div>
          <p v-else class="text-sm text-gray-500">No AI analysis yet.</p>
        </div>
      </div>

      <!-- Right column: Actions -->
      <div class="space-y-6">
        <!-- Status Workflow -->
        <StatusWorkflow
          :current-status="lead.status"
          entity="lead"
          :loading="statusLoading"
          @transition="handleStatusChange"
        />

        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Lead Conversion</h2>
          <div class="grid grid-cols-3 gap-3 text-sm">
            <div class="rounded-lg bg-primary-50 p-3">
              <p class="text-xs text-primary-700">Score</p>
              <p class="text-2xl font-bold text-primary-700">{{ leadScoreValue }}</p>
            </div>
            <div class="rounded-lg bg-gray-50 p-3">
              <p class="text-xs text-gray-500">Stage</p>
              <p class="admin-section-title mt-1 capitalize">{{ leadStageValue }}</p>
            </div>
            <div class="rounded-lg bg-blue-50 p-3">
              <p class="text-xs text-blue-700">Intelligence</p>
              <p class="text-2xl font-bold text-blue-700">{{ intelligenceLevel }}</p>
            </div>
          </div>
          <div class="mt-3 rounded-lg p-3 text-sm" :class="phase1Requested ? 'bg-emerald-50 text-emerald-800' : 'bg-amber-50 text-amber-800'">
            {{ phase1Requested ? 'Customer requested Phase-1 Proposal.' : 'Customer has not requested Phase-1 Proposal yet.' }}
          </div>
        </div>

        <!-- P1 Actions: Create Project + Draft Quote -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Operations</h2>
          <div class="space-y-3">
            <button
              class="w-full px-4 py-2.5 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60 flex items-center justify-center gap-2"
              :disabled="projectLoading"
              @click="createProjectFromLead"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
              {{ projectLoading ? 'Creating...' : 'Create Project from Lead' }}
            </button>
            <button
              class="w-full px-4 py-2.5 text-sm font-medium rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60 flex items-center justify-center gap-2"
              :disabled="draftQuoteLoading"
              @click="draftQuoteFromLead"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              {{ draftQuoteLoading ? 'Generating...' : 'Draft Quote from Lead' }}
            </button>
          </div>
          <!-- Success messages -->
          <div v-if="projectCreated" class="mt-3 p-2 rounded-lg bg-indigo-50 text-indigo-700 text-xs">
            Project created.
            <NuxtLink :to="`projects/${projectCreated}`" class="font-medium underline">View Project &rarr;</NuxtLink>
          </div>
          <div v-if="quoteCreated" class="mt-3 p-2 rounded-lg bg-emerald-50 text-emerald-700 text-xs">
            Draft quote generated.
            <NuxtLink :to="`quotes`" class="font-medium underline">View Quotes &rarr;</NuxtLink>
          </div>
          <div v-if="opError" class="mt-3 p-2 rounded-lg bg-red-50 text-red-700 text-xs">{{ opError }}</div>
        </div>

        <!-- Assignment -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Assignment</h2>
          <p class="text-sm text-gray-500 mb-2">
            {{ lead.assigned_admin_id ? `Assigned to: ${lead.assigned_admin_id}` : 'Not assigned' }}
          </p>
        </div>

        <!-- Notes -->
        <div class="admin-card">
          <h2 class="admin-section-title mb-4">Admin Notes</h2>
          <textarea
            v-model="notes"
            rows="5"
            class="w-full text-sm border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Add notes about this lead..."
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
            <div class="flex justify-between"><dt class="text-gray-500">ID</dt><dd class="font-mono">{{ lead.id.slice(0, 8) }}...</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Created</dt><dd>{{ new Date(lead.created_at).toLocaleString() }}</dd></div>
          </dl>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="text-center py-12 text-gray-500">{{ $t('common.loading') }}</div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const route = useRoute()
const { apiFetch } = useApi()
const lead = ref<any>(null)
const notes = ref('')
const statusLoading = ref(false)
const notesLoading = ref(false)
const aiLoading = ref(false)

// Site Survey state
const surveys = ref<any[]>([])
const showSurveyForm = ref(false)
const surveyLoading = ref(false)
const surveyForm = reactive({
  survey_type: 'quick',
  area: '',
  floors: '',
  rooms: '',
  building_type: '',
  infrastructure_notes: '',
  notes: '',
})

// P1 Operations state
const projectLoading = ref(false)
const draftQuoteLoading = ref(false)
const projectCreated = ref<string | null>(null)
const quoteCreated = ref<string | null>(null)
const opError = ref<string | null>(null)

const leadScoreValue = computed(() => lead.value?.lead_score ?? lead.value?.ai_analysis_json?.lead_score?.score ?? '-')
const leadStageValue = computed(() => lead.value?.lead_stage ?? lead.value?.ai_analysis_json?.lead_score?.stage ?? 'Unscored')
const intelligenceLevel = computed(() => lead.value?.desired_intelligence_level ? `L${lead.value.desired_intelligence_level}` : '-')
const phase1Requested = computed(() => Boolean(lead.value?.ai_analysis_json?.phase1_requested || lead.value?.site_info_json?.phase1_requested))
const industrialInfo = computed(() => {
  const site = lead.value?.site_info_json || {}
  return {
    production: site.production_machines || site.production || '',
    existing: site.existing_systems || '',
    protocols: site.industrial_protocols || site.ot_protocols || '',
    energy: site.energy_solar || site.energy || '',
    safety: site.safety_requirements || site.identity_access || '',
  }
})
const isIndustrialLead = computed(() => {
  const text = [
    lead.value?.project_type,
    lead.value?.description,
    lead.value?.site_info_json?.category_key,
    lead.value?.ai_analysis_json?.classification?.project_class,
    lead.value?.systems_needed_json?.join(' '),
  ].join(' ').toLowerCase()
  return ['factory', 'industrial', 'production', 'plc', 'scada', 'machinery'].some((token) => text.includes(token))
})

onMounted(async () => {
  try {
    lead.value = await apiFetch<any>(`/leads/${route.params.id}`)
    notes.value = lead.value?.notes || ''
  } catch {}
  // Load surveys
  loadSurveys()
})

async function loadSurveys() {
  try {
    const res = await apiFetch<any>(`/leads/${route.params.id}/surveys`)
    surveys.value = res.items || []
  } catch {}
}

async function createSurvey() {
  surveyLoading.value = true
  try {
    const surveyJson: Record<string, any> = {}
    if (surveyForm.area) surveyJson.area = surveyForm.area
    if (surveyForm.floors) surveyJson.floors = surveyForm.floors
    if (surveyForm.rooms) surveyJson.rooms = surveyForm.rooms
    if (surveyForm.building_type) surveyJson.building_type = surveyForm.building_type
    if (surveyForm.infrastructure_notes) surveyJson.infrastructure_notes = surveyForm.infrastructure_notes
    if (surveyForm.notes) surveyJson.notes = surveyForm.notes

    await apiFetch<any>(`/leads/${route.params.id}/surveys`, {
      method: 'POST',
      body: {
        lead_id: route.params.id,
        survey_type: surveyForm.survey_type,
        survey_json: surveyJson,
      },
    })
    showSurveyForm.value = false
    // Reset form
    Object.assign(surveyForm, { survey_type: 'quick', area: '', floors: '', rooms: '', building_type: '', infrastructure_notes: '', notes: '' })
    await loadSurveys()
  } catch (e: any) {
    console.error('Create survey failed:', e)
  } finally {
    surveyLoading.value = false
  }
}

async function createProjectFromLead() {
  projectLoading.value = true
  opError.value = null
  projectCreated.value = null
  try {
    const res = await apiFetch<any>(`/projects/from-lead/${route.params.id}`, {
      method: 'POST',
      body: {},
    })
    projectCreated.value = res.id
  } catch (e: any) {
    opError.value = e?.data?.detail || e?.message || 'Failed to create project'
    console.error('Create project failed:', e)
  } finally {
    projectLoading.value = false
  }
}

async function draftQuoteFromLead() {
  draftQuoteLoading.value = true
  opError.value = null
  quoteCreated.value = null
  try {
    const res = await apiFetch<any>(`/quotes/draft-from-lead/${route.params.id}`, {
      method: 'POST',
    })
    quoteCreated.value = res.id
    // Refresh lead (status may have changed to quotation_drafting)
    lead.value = await apiFetch<any>(`/leads/${route.params.id}`)
  } catch (e: any) {
    opError.value = e?.data?.detail || e?.message || 'Failed to draft quote'
    console.error('Draft quote failed:', e)
  } finally {
    draftQuoteLoading.value = false
  }
}

async function handleStatusChange(newStatus: string) {
  statusLoading.value = true
  try {
    lead.value = await apiFetch<any>(`/leads/${route.params.id}/status`, {
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
    lead.value = await apiFetch<any>(`/leads/${route.params.id}/notes`, {
      method: 'PATCH',
      body: { notes: notes.value },
    })
  } catch (e: any) {
    console.error('Notes update failed:', e)
  } finally {
    notesLoading.value = false
  }
}

async function runAnalysis() {
  aiLoading.value = true
  try {
    await apiFetch<any>(`/leads/${route.params.id}/analyze`, { method: 'POST' })
    lead.value = await apiFetch<any>(`/leads/${route.params.id}`)
  } catch (e: any) {
    console.error('AI analysis failed:', e)
  } finally {
    aiLoading.value = false
  }
}
</script>
