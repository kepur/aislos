<template>
  <div class="min-h-screen pt-10 pb-20">
    <section class="container-main px-4 sm:px-6 lg:px-8 py-8 lg:py-10">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-8">
        <div>
          <p class="text-sm font-bold uppercase tracking-wider text-primary-400">{{ $t('lead.forgeKicker') }}</p>
          <h1 class="mt-2 text-4xl font-bold text-white">{{ $t('lead.forgeTitle') }}</h1>
          <p class="mt-3 max-w-4xl text-slate-300">{{ $t('lead.forgeSubtitle') }}</p>
        </div>
        <div class="border glass-panel border-primary-500/30 px-6 py-4 text-center">
          <p class="text-sm text-slate-400">{{ $t('lead.progress') }}</p>
          <p class="text-3xl font-bold text-primary-400">{{ progress }}%</p>
        </div>
      </div>

      <div v-if="!selectedCategory" class="grid grid-cols-1 lg:grid-cols-[0.8fr_1.2fr] gap-6">
        <div class="glass-panel p-6 border-primary-500/30">
          <p class="text-sm font-bold uppercase tracking-wider text-primary-700">Step 1</p>
          <h2 class="mt-2 text-2xl font-bold text-white">{{ $t('lead.step1Label') }}</h2>
          <p class="mt-3 text-slate-300">{{ $t('lead.step1Desc') }}</p>
          <div class="mt-6 bg-amber-400/10 border border-amber-500/30 p-4 text-sm text-amber-200">
            {{ $t('lead.estimateWarning') }}
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            v-for="category in projectCategories"
            :key="category.key"
            type="button"
            class="text-left glass-panel p-5 border-white/10 hover:border-primary-400 hover:shadow-md transition"
            @click="startCategory(category.key)"
          >
            <p class="text-xs font-bold uppercase tracking-wider text-primary-600">{{ category.level }}</p>
            <h3 class="mt-2 font-bold text-white">{{ category.label }}</h3>
            <p class="mt-2 text-sm text-slate-300">{{ category.description }}</p>
          </button>
        </div>
      </div>

      <div v-else class="space-y-6">
        <div class="glass-panel border-primary-500/30 border p-4">
          <div class="flex flex-col xl:flex-row xl:items-center gap-4">
            <div class="flex-1">
              <p class="text-xs font-bold uppercase tracking-wider text-primary-700">Selected project</p>
              <h2 class="mt-1 text-2xl font-bold text-white">{{ selectedCategory.label }}</h2>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="level in levelOptions"
                :key="level.key"
                type="button"
                class="border px-4 py-2 text-sm font-semibold transition"
                :class="targetLevel === level.key ? 'bg-primary-600 text-white border-primary-500' : 'bg-white text-slate-300 border-slate-200 hover:border-slate-500'"
                @click="targetLevel = level.key"
              >
                {{ level.key }} · {{ level.label }}
              </button>
            </div>
            <button type="button" class="border px-4 py-2 text-sm font-semibold text-slate-300 hover:border-slate-500" @click="resetForge">
              Change category
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-[1.05fr_0.95fr] gap-6">
          <div class="glass-panel border-primary-500/30 overflow-hidden">
            <div class="border-b p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <p class="text-sm font-bold uppercase tracking-wider text-primary-400">LangGraph Intake</p>
                <h2 class="mt-1 text-2xl font-bold text-white">Collect project information step by step</h2>
              </div>
              <button type="button" class="bg-primary-900/300/20 text-primary-400 px-4 py-2 text-sm font-semibold" @click="askNextQuestion">
                AI Analyze
              </button>
            </div>

            <div ref="chatScroll" class="h-[590px] overflow-y-auto p-5 lg:p-8 space-y-5 bg-transparent">
              <div
                v-for="message in messages"
                :key="message.id"
                class="flex"
                :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
              >
                <div
                  class="max-w-[86%] border p-4 text-sm leading-7"
                  :class="message.role === 'user' ? 'bg-primary-600 text-white border-primary-500' : 'bg-white text-slate-300 border-slate-200'"
                >
                  <p class="whitespace-pre-wrap">{{ message.text }}</p>
                  <p class="mt-2 text-xs" :class="message.role === 'user' ? 'text-primary-100' : 'text-slate-400'">
                    {{ message.tag }}
                  </p>
                </div>
              </div>
            </div>

            <div class="border-t bg-white p-4">
              <div v-if="submitted" class="bg-emerald-400/10 border border-emerald-500/30 p-4 text-emerald-200">
                {{ phase1Requested ? 'Phase-1 Proposal request submitted.' : 'Requirement submitted.' }}
                Admin will review the AI estimate and follow up manually.
              </div>
              <form v-else class="flex flex-col sm:flex-row gap-3" @submit.prevent="sendMessage">
                <textarea
                  v-model="draft"
                  rows="2"
                  class="input-field resize-none"
                  :placeholder="currentQuestion?.placeholder || 'Answer the AI question...'"
                  @keydown.enter.exact.prevent="sendMessage"
                ></textarea>
                <button type="submit" class="btn-primary sm:w-40" :disabled="loading || Boolean(currentQuestion && !draft.trim())">
                  {{ loading ? 'Working...' : currentQuestion ? 'Send' : 'Submit' }}
                </button>
              </form>
              <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
            </div>
          </div>

          <aside class="glass-panel p-6 border-primary-500/30 h-fit xl:sticky xl:top-24">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-sm font-bold uppercase tracking-wider text-primary-700">Project Preview</p>
                <h2 class="mt-1 text-2xl font-bold text-white">{{ progress }}% complete</h2>
              </div>
              <span class="border px-3 py-1 text-sm font-semibold text-primary-700">{{ targetLevel }} target</span>
            </div>

            <div class="mt-6 space-y-3">
              <div
                v-for="module in previewModules"
                :key="module.key"
                class="border p-4 flex items-start justify-between gap-4"
                :class="module.done ? 'border-emerald-200 bg-emerald-50' : module.active ? 'border-amber-200 bg-amber-50' : 'border-slate-200 bg-white'"
              >
                <div class="flex gap-3">
                  <span class="mt-2 h-3 w-3 shrink-0" :class="module.done ? 'bg-emerald-400' : module.active ? 'bg-amber-400' : 'bg-slate-600'"></span>
                  <div>
                    <p class="font-semibold text-white">{{ module.label }}</p>
                    <p class="mt-1 text-sm text-slate-300">{{ module.summary }}</p>
                  </div>
                </div>
                <span class="shrink-0 px-3 py-1 text-xs font-bold" :class="module.done ? 'bg-emerald-500/20 text-emerald-300' : module.active ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-100 text-slate-300'">
                  {{ module.done ? 'Done' : module.active ? 'Active' : 'Pending' }}
                </span>
              </div>
            </div>

            <div class="mt-6 border p-4">
              <p class="text-sm font-semibold text-white">Selected intelligence behavior</p>
              <p class="mt-2 text-sm text-slate-300">{{ targetLevelMeta.description }}</p>
            </div>

            <div class="mt-6 bg-amber-400/10 border border-amber-500/30 p-4 text-sm text-amber-200">
              {{ estimateNotice }}
            </div>

            <div class="mt-6 border p-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-white">Lead Score</p>
                  <p class="mt-1 text-xs text-slate-400">Calculated from completeness, budget, contact, target level, and Phase-1 intent.</p>
                </div>
                <div class="text-right">
                  <p class="text-2xl font-bold text-primary-700">{{ leadScore }}</p>
                  <p class="text-xs font-semibold text-slate-400">{{ leadStage }}</p>
                </div>
              </div>
            </div>

            <div class="mt-6">
              <p class="text-sm font-semibold text-white">Preliminary Proposal Directions</p>
              <div class="mt-3 space-y-3">
                <div
                  v-for="plan in proposalPlans"
                  :key="plan.tier"
                  class="border p-4"
                  :class="plan.tier === 'premium_ai' ? 'border-indigo-200 bg-primary-900/300/20' : 'border-slate-200 bg-white'"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="font-semibold text-white">{{ plan.name }}</p>
                      <p class="mt-1 text-xs text-slate-400">{{ plan.level }} · {{ plan.complexity }}</p>
                    </div>
                    <span class="text-xs font-bold text-primary-700">{{ plan.risk }}</span>
                  </div>
                  <p class="mt-3 text-sm text-slate-300">{{ plan.summary }}</p>
                  <dl class="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div><dt class="text-slate-400">Device</dt><dd class="font-semibold text-white">{{ plan.device }}</dd></div>
                    <div><dt class="text-slate-400">Support</dt><dd class="font-semibold text-white">{{ plan.support }}</dd></div>
                  </dl>
                </div>
              </div>
            </div>

            <div v-if="!currentQuestion && !submitted" class="mt-6 border border-primary-500/30 bg-primary-900/30 p-4">
              <p class="font-semibold text-white">Ready for Phase-1 Proposal</p>
              <p class="mt-2 text-sm text-slate-300">
                Free AI estimate gives direction only. Phase-1 means human review, deeper BOM,
                architecture draft, supplier confirmation, and one meeting.
              </p>
              <button type="button" class="mt-4 btn-primary w-full" :disabled="loading" @click="requestPhase1Proposal">
                {{ loading ? 'Submitting...' : 'Request Phase-1 Proposal' }}
              </button>
            </div>
          </aside>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
const { apiFetch } = useApi()

type CategoryKey = 'villa' | 'school' | 'apartment' | 'office' | 'hotel' | 'energy' | 'retrofit' | 'custom'
type LevelKey = 'L3' | 'L4' | 'L5'

const estimateNotice = 'AI estimate only. Final quote requires manual review, customer meeting, site survey, supplier confirmation, and signed contract.'

const projectCategories = [
  { key: 'villa', label: 'Smart Villa / Future Home', level: 'L3-L5', description: 'Home AI brain, local privacy, family identity, comfort, energy, EV, smart room equipment.', systems: ['KNX', 'Home Assistant', 'CCTV', 'Energy Monitoring', 'EV Charging', 'Offline AI'] },
  { key: 'school', label: 'School / Campus', level: 'L3-L4', description: 'Classrooms, safety, CO2, access, CCTV, network, energy reports, maintenance workflow.', systems: ['CCTV', 'Access Control', 'HVAC', 'Energy Monitoring', 'Network'] },
  { key: 'apartment', label: 'Apartment Building', level: 'L3-L4', description: 'Property brain for common areas, parking, visitor access, meters, tenant support.', systems: ['Access Control', 'CCTV', 'Energy Monitoring', 'Maintenance'] },
  { key: 'office', label: 'Enterprise Office Building', level: 'L3-L5', description: 'Meeting rooms, visitor access, occupancy, IT network, facility AI daily summary.', systems: ['HVAC', 'Lighting', 'Access Control', 'Network', 'Offline AI'] },
  { key: 'hotel', label: 'Hotel / Serviced Apartment', level: 'L3-L4', description: 'Guest room control, away energy saving, housekeeping access, remote maintenance.', systems: ['KNX', 'HVAC', 'Lighting', 'Access Control', 'Remote Maintenance'] },
  { key: 'energy', label: 'Solar + Energy Site', level: 'L3-L5', description: 'PV, battery, EV charging, tariffs, critical loads, alerts, monthly AI energy reports.', systems: ['Solar', 'Battery', 'EV Charging', 'Energy Monitoring'] },
  { key: 'retrofit', label: 'Existing Building Retrofit', level: 'L3-L4', description: 'Upgrade older wiring, CCTV, network, access, and energy visibility without overpromising.', systems: ['CCTV', 'Network', 'Lighting', 'Energy Monitoring'] },
  { key: 'custom', label: 'Custom Future Building', level: 'L4-L5', description: 'Advanced AI, local AI box, identity, robot-ready paths, and manual engineering review.', systems: ['Offline AI', 'Network', 'CCTV', 'Energy Monitoring'] },
] as const

const levelOptions = [
  { key: 'L3', label: 'Energy Optimized', description: 'Focus on energy monitoring, scenes, schedules, dashboards, alarms, and lifecycle reports.' },
  { key: 'L4', label: 'AI Assisted', description: 'Adds AI analysis, anomaly detection, admin-reviewed recommendations, and smart operational summaries.' },
  { key: 'L5', label: 'Local AI Brain', description: 'Adds local AI box, privacy-first identity, offline control logic, and advanced cross-system orchestration.' },
] as const

const questionBank: Record<CategoryKey, Array<{ key: string; module: string; prompt: string; placeholder: string }>> = {
  villa: [
    { key: 'location', module: 'location', prompt: 'Where is the villa located? Please include country and city.', placeholder: 'Example: Belgrade, Serbia' },
    { key: 'building', module: 'site', prompt: 'What is the approximate area, number of floors, and main room list?', placeholder: 'Example: 320 sqm, 2 floors, living room, kitchen, 4 bedrooms...' },
    { key: 'existing', module: 'existing', prompt: 'What systems already exist: network, CCTV, alarm, HVAC, solar, EV charger, smart switches, or KNX?', placeholder: 'Describe current wiring, internet, CCTV, solar, HVAC...' },
    { key: 'goals', module: 'goals', prompt: 'What should the home become: energy saving, AI family brain, security, comfort, offline privacy, or robot-ready?', placeholder: 'Example: offline AI privacy, energy saving, face access, EV charging...' },
    { key: 'identity', module: 'identity', prompt: 'Do you need identity features such as face recognition, visitor QR, car plate, fingerprint, or future voiceprint?', placeholder: 'List required access and identity features...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need solar, battery, EV charging, peak/off-peak tariff logic, or appliance energy optimization?', placeholder: 'Describe PV, battery, EV and energy goals...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and service period should we design around?', placeholder: 'Example: 15k-50k EUR, 5-year support' },
    { key: 'contact', module: 'contact', prompt: 'Finally, who should we contact? Please provide name, email, and optional Telegram/WhatsApp.', placeholder: 'Example: Wei, wei@example.com, Telegram @...' },
  ],
  school: [
    { key: 'location', module: 'location', prompt: 'Where is the campus located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'How many buildings, classrooms, floors, labs, admin areas, and students are involved?', placeholder: 'Example: 2 buildings, 32 classrooms, 600 students...' },
    { key: 'existing', module: 'existing', prompt: 'What existing CCTV, access control, network, HVAC, solar, or BMS systems are already installed?', placeholder: 'Describe existing systems and pain points...' },
    { key: 'goals', module: 'goals', prompt: 'What are the top goals: safety, energy saving, classroom comfort, lab access, network visibility, or maintenance?', placeholder: 'List top priorities...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need solar monitoring, classroom CO2, HVAC scheduling, or monthly energy reports?', placeholder: 'Describe energy and environment needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and support period should we assume?', placeholder: 'Example: 50k-100k EUR, 5-year lifecycle support' },
    { key: 'contact', module: 'contact', prompt: 'Who should AinerWise contact for this campus assessment?', placeholder: 'Name, email, phone or Telegram' },
  ],
  apartment: [
    { key: 'location', module: 'location', prompt: 'Where is the apartment building located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'How many units, floors, common areas, parking areas, and meters are involved?', placeholder: 'Example: 40 units, 8 floors, garage, lobby...' },
    { key: 'existing', module: 'existing', prompt: 'What existing intercom, CCTV, access, meters, lighting, or network systems exist?', placeholder: 'Describe current systems...' },
    { key: 'goals', module: 'goals', prompt: 'What should improve: visitor access, common-area energy, tenant experience, parking, repair workflow, or security?', placeholder: 'List property goals...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need common-area energy reports, PV for public loads, or meter monitoring?', placeholder: 'Energy and metering needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and service period are realistic?', placeholder: 'Example: 15k-50k EUR, 3-year support' },
    { key: 'contact', module: 'contact', prompt: 'Who should we contact for property follow-up?', placeholder: 'Name, email, phone or Telegram' },
  ],
  office: [
    { key: 'location', module: 'location', prompt: 'Where is the office building located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'How large is the office, how many floors, employees, meeting rooms, IT rooms, and visitor areas?', placeholder: 'Example: 4100 sqm, 4 floors, 12 meeting rooms...' },
    { key: 'existing', module: 'existing', prompt: 'What existing access control, CCTV, network, HVAC, booking, or BMS systems are in place?', placeholder: 'Describe current office systems...' },
    { key: 'goals', module: 'goals', prompt: 'What are the goals: meeting automation, visitor access, energy saving, workplace utilization, local AI, or facility summaries?', placeholder: 'List office AI/facility goals...' },
    { key: 'identity', module: 'identity', prompt: 'Do you need employee identity, visitor QR, face access, mobile credentials, or admin-only AI permissions?', placeholder: 'Describe identity and access needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and maintenance period should we assume?', placeholder: 'Example: 50k-100k EUR, 5-year support' },
    { key: 'contact', module: 'contact', prompt: 'Who is the office project contact?', placeholder: 'Name, email, phone or Telegram' },
  ],
  hotel: [
    { key: 'location', module: 'location', prompt: 'Where is the hotel or serviced apartment located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'How many rooms, floors, room types, common areas, and service areas are involved?', placeholder: 'Example: 48 rooms, 5 floors, lobby, corridors...' },
    { key: 'existing', module: 'existing', prompt: 'What existing door locks, thermostats, CCTV, PMS, network, or room controls exist?', placeholder: 'Describe current hotel systems...' },
    { key: 'goals', module: 'goals', prompt: 'What should improve: guest welcome mode, away energy saving, housekeeping permissions, room status, or maintenance?', placeholder: 'List guest and operation goals...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need HVAC energy saving, room occupancy sensing, solar dashboard, or monthly hotel reports?', placeholder: 'Energy and room-control needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and support period should we design around?', placeholder: 'Example: 50k-100k EUR, 5-year lifecycle support' },
    { key: 'contact', module: 'contact', prompt: 'Who should we contact for hotel follow-up?', placeholder: 'Name, email, phone or Telegram' },
  ],
  energy: [
    { key: 'location', module: 'location', prompt: 'Where is the solar or energy site located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'What building or site loads should be monitored: office, warehouse, hotel, EV, critical loads?', placeholder: 'Describe site and load profile...' },
    { key: 'existing', module: 'existing', prompt: 'What PV, inverter, battery, meter, EV charger, or EMS equipment already exists?', placeholder: 'Inverter brand, battery, meters, EV chargers...' },
    { key: 'goals', module: 'goals', prompt: 'What do you want to optimize: PV self-consumption, peak tariff, EV charging, battery, alerts, or reports?', placeholder: 'List energy optimization goals...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need tariff rules, load priority, anomaly alarms, monthly reports, or remote maintenance?', placeholder: 'Describe energy logic and reporting needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and support period should we assume?', placeholder: 'Example: 15k-50k EUR, 3-year support' },
    { key: 'contact', module: 'contact', prompt: 'Who should AinerWise contact for this energy assessment?', placeholder: 'Name, email, phone or Telegram' },
  ],
  retrofit: [
    { key: 'location', module: 'location', prompt: 'Where is the existing building located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'What building type, area, floors, and rooms/zones are involved?', placeholder: 'Describe building structure...' },
    { key: 'existing', module: 'existing', prompt: 'What systems exist today and what is outdated or painful?', placeholder: 'Wiring, CCTV, access, HVAC, network, lighting...' },
    { key: 'goals', module: 'goals', prompt: 'What is the retrofit goal: basic control, security upgrade, energy dashboard, KNX, or Home Assistant?', placeholder: 'Describe desired retrofit outcome...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and support period should we assume?', placeholder: 'Example: 5k-15k EUR, 3-year support' },
    { key: 'contact', module: 'contact', prompt: 'Who should we contact for retrofit follow-up?', placeholder: 'Name, email, phone or Telegram' },
  ],
  custom: [
    { key: 'location', module: 'location', prompt: 'Where will this future building or concept project be located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'What kind of building or site is this, and what scale should we assume?', placeholder: 'Describe building type, area, floors, rooms...' },
    { key: 'goals', module: 'goals', prompt: 'What future capability are you imagining: local AI brain, robots, digital human, autonomous energy, identity, or predictive maintenance?', placeholder: 'Describe the vision...' },
    { key: 'existing', module: 'existing', prompt: 'What systems already exist or must be integrated?', placeholder: 'KNX, HA, CCTV, HVAC, solar, robot platform...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and phase should this start with: concept, Phase-1 proposal, or implementation?', placeholder: 'Example: design-only first, 5-year support later' },
    { key: 'contact', module: 'contact', prompt: 'Who should we contact for custom engineering review?', placeholder: 'Name, email, phone or Telegram' },
  ],
}

const selectedKey = ref<CategoryKey | null>(null)
const targetLevel = ref<LevelKey>('L3')
const messages = ref<Array<{ id: number; role: 'ai' | 'user'; text: string; tag: string }>>([])
const answers = reactive<Record<string, string>>({})
const currentIndex = ref(0)
const draft = ref('')
const submitted = ref(false)
const phase1Requested = ref(false)
const loading = ref(false)
const error = ref('')
const chatScroll = ref<HTMLElement | null>(null)

const selectedCategory = computed(() => projectCategories.find((item) => item.key === selectedKey.value) || null)
const targetLevelMeta = computed(() => levelOptions.find((item) => item.key === targetLevel.value) || levelOptions[0])
const currentQuestions = computed(() => selectedKey.value ? questionBank[selectedKey.value] : [])
const currentQuestion = computed(() => currentQuestions.value[currentIndex.value] || null)
const answeredCount = computed(() => Object.keys(answers).filter((key) => answers[key]?.trim()).length)
const progress = computed(() => {
  if (!selectedCategory.value) return 0
  const total = currentQuestions.value.length + 1
  return Math.min(100, Math.round(((answeredCount.value + 1) / total) * 100))
})

const leadScore = computed(() => {
  let score = progress.value >= 85 ? 20 : progress.value >= 50 ? 10 : 0
  if (answers.budget) score += /50|100|premium|enterprise|over/i.test(answers.budget) ? 20 : 12
  if (/3|5|8|10|lifecycle/i.test(answers.budget || '')) score += 15
  if (extractEmail(answers.contact || '')) score += 10
  if (/telegram|whatsapp|@|\+/i.test(answers.contact || '')) score += 10
  if (targetLevel.value === 'L4' || targetLevel.value === 'L5') score += 10
  if (phase1Requested.value) score += 25
  return Math.min(score, 100)
})

const leadStage = computed(() => {
  if (leadScore.value >= 85) return 'Phase-1 Ready'
  if (leadScore.value >= 70) return 'Qualified Lead'
  if (leadScore.value >= 45) return 'Warm Lead'
  return 'Cold Lead'
})

const proposalPlans = computed(() => {
  const largeProject = ['school', 'office', 'hotel'].includes(selectedKey.value || '')
  const ranges = largeProject
    ? { budget: '15k-50k EUR', standard: '50k-100k EUR', premium: '100k-250k EUR' }
    : { budget: '5k-15k EUR', standard: '15k-50k EUR', premium: '50k-120k EUR' }
  return [
    {
      tier: 'budget',
      name: 'Budget Plan',
      level: 'L1-L2',
      complexity: 'Starter retrofit',
      risk: 'Medium risk',
      device: ranges.budget,
      support: '1-3 years',
      summary: 'Basic control, essential CCTV/access/network/energy monitoring, and limited automation.',
    },
    {
      tier: 'standard',
      name: 'Standard Plan',
      level: 'L2-L3',
      complexity: 'Practical delivery',
      risk: 'Managed risk',
      device: ranges.standard,
      support: '3-5 years',
      summary: 'Sensor automation, energy dashboard, remote maintenance, and service-ready device choices.',
    },
    {
      tier: 'premium_ai',
      name: 'Premium AI Plan',
      level: targetLevel.value === 'L5' ? 'L4-L5' : 'L3-L4',
      complexity: 'Manual review required',
      risk: 'High review',
      device: ranges.premium,
      support: '5-10 years',
      summary: 'AI analysis, identity/access intelligence, local AI options, and deeper lifecycle planning.',
    },
    {
      tier: 'future_autonomous',
      name: 'Future Autonomous Plan',
      level: 'L5-L6',
      complexity: 'Concept demo',
      risk: 'Custom only',
      device: 'Custom engineering',
      support: 'Custom SLA',
      summary: 'Robot-ready and autonomous facility concepts. No fixed price before engineering review.',
    },
  ]
})

const previewModules = computed(() => {
  const modules = [
    { key: 'category', label: 'Project Category', summary: selectedCategory.value?.label || 'Choose project type' },
    { key: 'location', label: 'Site Location', summary: answers.location || 'Country and city required' },
    { key: 'site', label: 'Building / Site Profile', summary: answers.building || 'Area, rooms, floors, or loads' },
    { key: 'existing', label: 'Existing Systems', summary: answers.existing || 'Network, CCTV, HVAC, solar, access, KNX...' },
    { key: 'goals', label: 'Smart Goals', summary: answers.goals || 'Energy, security, comfort, AI, maintenance...' },
    { key: 'identity', label: 'Identity & Access', summary: answers.identity || 'Only needed for projects with access/AI identity' },
    { key: 'energy', label: 'Energy & Solar', summary: answers.energy || 'PV, battery, EV, tariffs, reports' },
    { key: 'budget', label: 'Budget & Service Period', summary: answers.budget || 'Budget range and support years' },
    { key: 'contact', label: 'Contact', summary: answers.contact || 'Name and email/phone' },
  ]
  const activeModule = currentQuestion.value?.module
  return modules.map((module) => ({
    ...module,
    done: module.key === 'category' || Boolean(answers[module.key]),
    active: module.key === activeModule,
  }))
})

function scrollChat() {
  nextTick(() => {
    if (chatScroll.value) chatScroll.value.scrollTop = chatScroll.value.scrollHeight
  })
}

function pushAi(text: string, tag = 'gap_question') {
  messages.value.push({ id: Date.now() + Math.random(), role: 'ai', text, tag })
  scrollChat()
}

function pushUser(text: string) {
  messages.value.push({ id: Date.now() + Math.random(), role: 'user', text, tag: 'intake_chat' })
  scrollChat()
}

function startCategory(key: CategoryKey) {
  selectedKey.value = key
  const category = projectCategories.find((item) => item.key === key)
  targetLevel.value = category?.level.includes('L5') ? 'L5' : 'L3'
  messages.value = []
  Object.keys(answers).forEach((answerKey) => delete answers[answerKey])
  currentIndex.value = 0
  submitted.value = false
  phase1Requested.value = false
  pushAi(`Great. I will create a ${category?.label} assessment and ask only the next missing smart-building question.\n\n${currentQuestion.value?.prompt}`)
}

function askNextQuestion() {
  if (currentQuestion.value) {
    pushAi(currentQuestion.value.prompt, 'ai_analyze')
  } else {
    pushAi('I have enough information for a preliminary AI estimate. You can submit this assessment for admin review.', 'proposal_ready')
  }
}

async function sendMessage() {
  error.value = ''
  if (!currentQuestion.value) {
    await submitLead()
    return
  }
  if (!draft.value.trim()) return
  const text = draft.value.trim()
  draft.value = ''
  pushUser(text)

  if (currentQuestion.value) {
    answers[currentQuestion.value.module] = text
    currentIndex.value += 1
    const next = currentQuestion.value
    if (next) {
      pushAi(`Captured. Next missing item:\n\n${next.prompt}`)
      return
    }
    pushAi(`Thanks. The intake is now complete enough for a preliminary estimate.\n\nTarget level: ${targetLevel.value} ${targetLevelMeta.value.label}\n\n${estimateNotice}`, 'proposal_ready')
    return
  }

  await submitLead()
}

async function requestPhase1Proposal() {
  phase1Requested.value = true
  pushUser('Request Phase-1 Proposal')
  pushAi('Understood. I will mark this as Phase-1 intent. Human review is required before any detailed BOM, architecture diagram, supplier confirmation, or final quotation.', 'phase1_requested')
  await submitLead(true)
}

function resetForge() {
  selectedKey.value = null
  messages.value = []
  Object.keys(answers).forEach((answerKey) => delete answers[answerKey])
  currentIndex.value = 0
  submitted.value = false
  phase1Requested.value = false
  error.value = ''
}

function extractEmail(value: string) {
  return value.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0] || ''
}

function budgetToRange(value: string) {
  const lower = value.toLowerCase()
  if (lower.includes('100')) return 'over_100k'
  if (lower.includes('50')) return '50k_100k'
  if (lower.includes('15')) return '15k_50k'
  if (lower.includes('5')) return '5k_15k'
  return value || 'to_be_confirmed'
}

async function submitLead(requestPhase1 = false) {
  if (!selectedCategory.value) return
  loading.value = true
  phase1Requested.value = requestPhase1 || phase1Requested.value
  try {
    const transcript = messages.value.map((message) => `${message.role.toUpperCase()}: ${message.text}`).join('\n\n')
    await apiFetch('/leads', {
      method: 'POST',
      body: {
        project_type: selectedCategory.value.label,
        country: answers.location || '',
        budget_range: budgetToRange(answers.budget || ''),
        systems_needed_json: selectedCategory.value.systems,
        description: [
          `AI Project Forge transcript for ${selectedCategory.value.label}.`,
          `Target intelligence level: ${targetLevel.value} ${targetLevelMeta.value.label}.`,
          `Lead score: ${leadScore.value} (${leadStage.value}).`,
          phase1Requested.value ? 'Customer requested paid Phase-1 Proposal.' : 'Customer has not requested Phase-1 Proposal yet.',
          estimateNotice,
          transcript,
        ].join('\n\n'),
        contact_name: answers.contact?.split(',')?.[0] || 'AI Assessment Lead',
        contact_email: extractEmail(answers.contact || '') || 'unknown@ainerwise.local',
        contact_phone: answers.contact || '',
        site_info_json: {
          target_intelligence_level: targetLevel.value,
          category_key: selectedCategory.value.key,
          lead_score: leadScore.value,
          lead_stage: leadStage.value,
          phase1_requested: phase1Requested.value,
          proposal_tiers: proposalPlans.value,
          building: answers.building,
          existing_systems: answers.existing,
          smart_goals: answers.goals,
          identity_access: answers.identity,
          energy_solar: answers.energy,
          budget_and_service: answers.budget,
          estimate_notice: estimateNotice,
          transcript: messages.value,
        },
      },
    })
    submitted.value = true
    pushAi('Submitted. AinerWise admin will review the preliminary AI estimate before any quote or commitment.', 'submitted')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Submission failed'
  } finally {
    loading.value = false
  }
}
</script>
