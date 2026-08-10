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
          <p class="text-sm font-bold uppercase tracking-wider text-primary-300">{{ $t('lead.step1') }}</p>
          <h2 class="mt-2 text-2xl font-bold text-white">{{ $t('lead.step1Label') }}</h2>
          <p class="mt-3 text-slate-300">{{ $t('lead.step1Desc') }}</p>
          <div class="mt-6 pc-notice-warning">
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
            <p class="text-xs font-bold uppercase tracking-wider text-primary-400">{{ category.level }}</p>
            <h3 class="mt-2 font-bold text-white">{{ category.label }}</h3>
            <p class="mt-2 text-sm text-slate-300">{{ category.description }}</p>
          </button>
        </div>
      </div>

      <div v-else class="space-y-6">
        <div class="glass-panel border-primary-500/30 border p-4">
          <div class="flex flex-col xl:flex-row xl:items-center gap-4">
            <div class="flex-1">
              <p class="text-xs font-bold uppercase tracking-wider text-primary-300">{{ $t('lead.selectedProject') }}</p>
              <h2 class="mt-1 text-2xl font-bold text-white">{{ selectedCategory.label }}</h2>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="level in levelOptions"
                :key="level.key"
                type="button"
                class="border px-4 py-2 text-sm font-semibold transition"
                :class="targetLevel === level.key ? 'pc-chip pc-chip-active' : 'pc-chip pc-chip-inactive'"
                @click="targetLevel = level.key"
              >
                {{ level.key }} · {{ level.label }}
              </button>
            </div>
            <button type="button" class="border px-4 py-2 text-sm font-semibold text-slate-300 hover:border-slate-500" @click="resetForge">
              {{ $t('lead.changeCategory') }}
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-[1.05fr_0.95fr] gap-6">
          <div class="glass-panel border-primary-500/30 overflow-hidden">
            <div class="border-b p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <p class="text-sm font-bold uppercase tracking-wider text-primary-400">{{ $t('lead.intakeKicker') }}</p>
                <h2 class="mt-1 text-2xl font-bold text-white">{{ $t('lead.collectStep') }}</h2>
              </div>
              <button type="button" class="bg-primary-900/300/20 text-primary-400 px-4 py-2 text-sm font-semibold" @click="askNextQuestion">
                {{ $t('lead.aiAnalyze') }}
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
                  class="pc-chat-bubble"
                  :class="message.role === 'user' ? 'pc-chat-user' : 'pc-chat-assistant'"
                >
                  <p class="whitespace-pre-wrap">{{ message.text }}</p>
                  <p class="mt-2 text-xs" :class="message.role === 'user' ? 'text-primary-100' : 'text-slate-400'">
                    {{ message.tag }}
                  </p>
                </div>
              </div>
            </div>

            <div class="border-t border-white/10 bg-white/5 p-4">
              <div v-if="submitted" class="bg-emerald-400/10 border border-emerald-500/30 p-4 text-emerald-200">
                {{ phase1Requested ? $t('lead.submittedPhase1') : $t('lead.submittedRequirement') }}
                {{ $t('lead.submittedFollowup') }}
              </div>
              <form v-else class="flex flex-col sm:flex-row gap-3" @submit.prevent="sendMessage">
                <textarea
                  v-model="draft"
                  rows="2"
                  class="input-field resize-none"
                  :placeholder="currentQuestion?.placeholder || $t('lead.answerPlaceholder')"
                  @keydown.enter.exact.prevent="sendMessage"
                ></textarea>
                <button type="submit" class="btn-primary sm:w-40" :disabled="loading || (!readyToSubmit && !draft.trim())">
                  {{ loading ? $t('lead.working') : (readyToSubmit && !draft.trim()) ? $t('lead.submitShort') : $t('lead.send') }}
                </button>
              </form>
              <p v-if="error" class="mt-2 text-sm text-red-400">{{ error }}</p>
            </div>
          </div>

          <aside class="glass-panel p-6 border-primary-500/30 h-fit xl:sticky xl:top-24">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-sm font-bold uppercase tracking-wider text-primary-300">{{ $t('lead.projectPreview') }}</p>
                <h2 class="mt-1 text-2xl font-bold text-white">{{ $t('lead.percentComplete', { n: progress }) }}</h2>
              </div>
              <span class="border px-3 py-1 text-sm font-semibold text-primary-300">{{ $t('lead.levelTarget', { level: targetLevel }) }}</span>
            </div>

            <div class="mt-6 space-y-3">
              <div
                v-for="module in previewModules"
                :key="module.key"
                class="pc-status-card"
                :class="module.done ? 'pc-status-done' : module.active ? 'pc-status-active' : 'pc-status-pending'"
              >
                <div class="flex gap-3">
                  <span class="mt-2 h-3 w-3 shrink-0" :class="module.done ? 'bg-emerald-400' : module.active ? 'bg-amber-400' : 'bg-slate-600'"></span>
                  <div>
                    <p class="font-semibold text-white">{{ module.label }}</p>
                    <p class="mt-1 text-sm text-slate-300">{{ module.summary }}</p>
                  </div>
                </div>
                <span class="shrink-0 px-3 py-1 text-xs font-bold" :class="module.done ? 'pc-badge-done' : module.active ? 'pc-badge-active' : 'pc-badge-pending'">
                  {{ module.done ? $t('lead.statusDone') : module.active ? $t('lead.statusActive') : $t('lead.statusPending') }}
                </span>
              </div>
            </div>

            <div class="mt-6 border p-4">
              <p class="text-sm font-semibold text-white">{{ $t('lead.selectedBehavior') }}</p>
              <p class="mt-2 text-sm text-slate-300">{{ targetLevelMeta.description }}</p>
            </div>

            <div class="mt-6 pc-notice-warning">
              {{ estimateNotice }}
            </div>

            <div class="mt-6 border p-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-white">{{ $t('lead.leadScore') }}</p>
                  <p class="mt-1 text-xs text-slate-400">{{ $t('lead.leadScoreDesc') }}</p>
                </div>
                <div class="text-right">
                  <p class="text-2xl font-bold text-primary-300">{{ leadScore }}</p>
                  <p class="text-xs font-semibold text-slate-400">{{ leadStage }}</p>
                </div>
              </div>
            </div>

            <div class="mt-6">
              <p class="text-sm font-semibold text-white">{{ $t('lead.proposalDirections') }}</p>
              <div class="mt-3 space-y-3">
                <div
                  v-for="plan in proposalPlans"
                  :key="plan.tier"
                  class="border p-4"
                  :class="plan.tier === 'premium_ai' ? 'border-primary-500/30 bg-primary-500/10' : 'border-white/10 bg-white/5'"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="font-semibold text-white">{{ plan.name }}</p>
                      <p class="mt-1 text-xs text-slate-400">{{ plan.level }} · {{ plan.complexity }}</p>
                    </div>
                    <span class="text-xs font-bold text-primary-300">{{ plan.risk }}</span>
                  </div>
                  <p class="mt-3 text-sm text-slate-300">{{ plan.summary }}</p>
                  <dl class="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div><dt class="text-slate-400">{{ $t('lead.device') }}</dt><dd class="font-semibold text-white">{{ plan.device }}</dd></div>
                    <div><dt class="text-slate-400">{{ $t('lead.support') }}</dt><dd class="font-semibold text-white">{{ plan.support }}</dd></div>
                  </dl>
                </div>
              </div>
            </div>

            <div v-if="readyToSubmit && !submitted" class="mt-6 border border-primary-500/30 bg-primary-900/30 p-4">
              <p class="font-semibold text-white">{{ $t('lead.readyPhase1Title') }}</p>
              <p class="mt-2 text-sm text-slate-300">{{ $t('lead.readyPhase1Desc') }}</p>
              <button type="button" class="mt-4 btn-primary w-full" :disabled="loading" @click="requestPhase1Proposal">
                {{ loading ? $t('lead.submitting') : $t('lead.requestPhase1') }}
              </button>
            </div>
          </aside>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n({ useScope: 'global' })
const { apiFetch } = useApi()
const assistant = useAssistant()
const aiComplete = ref(false)
onMounted(() => { assistant.checkStatus() })

function mergeExtracted(extracted: Record<string, any>) {
  if (!extracted) return
  for (const [k, v] of Object.entries(extracted)) {
    if (v === null || v === undefined || v === '') continue
    answers[k] = typeof v === 'string' ? v : JSON.stringify(v)
  }
  if (extracted.budget_and_service && !answers.budget) answers.budget = String(extracted.budget_and_service)
}

type CategoryKey = 'villa' | 'school' | 'apartment' | 'office' | 'factory' | 'hotel' | 'energy' | 'storage' | 'kitchen' | 'water' | 'asset' | 'agri' | 'retrofit' | 'custom'
type LevelKey = 'L3' | 'L4' | 'L5'

const estimateNotice = computed(() => t('lead.estimateNotice'))

const categoryDefs: Array<{ key: CategoryKey; level: string; systems: string[] }> = [
  { key: 'villa' as const, level: 'L3-L5', systems: ['KNX', 'Home Assistant', 'CCTV', 'Energy Monitoring', 'EV Charging', 'Offline AI'] },
  { key: 'school' as const, level: 'L3-L4', systems: ['CCTV', 'Access Control', 'HVAC', 'Energy Monitoring', 'Network'] },
  { key: 'apartment' as const, level: 'L3-L4', systems: ['Access Control', 'CCTV', 'Energy Monitoring', 'Maintenance'] },
  { key: 'office' as const, level: 'L3-L5', systems: ['HVAC', 'Lighting', 'Access Control', 'Network', 'Offline AI'] },
  { key: 'factory' as const, level: 'L3-L5', systems: ['Industrial Automation', 'PLC/SCADA', 'Machine Energy Monitoring', 'Compressed Air', 'Robots', 'OT Network', 'Solar/Battery'] },
  { key: 'hotel' as const, level: 'L3-L4', systems: ['KNX', 'HVAC', 'Lighting', 'Access Control', 'Remote Maintenance'] },
  { key: 'energy' as const, level: 'L3-L5', systems: ['Solar', 'Battery', 'EV Charging', 'Energy Monitoring'] },
  { key: 'storage' as const, level: 'L2-L4', systems: ['StorageGuard', 'Temperature & Humidity Monitoring', 'Door Sensors', 'Outage Alerts', 'Compliance Reports', 'Calibration', 'Alarm Monitoring'] },
  { key: 'kitchen' as const, level: 'L2-L3', systems: ['KitchenGuard', 'Gas & CO Monitoring', 'Water Leak', 'Cut-off Valve', 'Alarm Monitoring', 'Annual Inspection'] },
  { key: 'water' as const, level: 'L2-L4', systems: ['AquaGuard', 'pH / EC / Turbidity / COD', 'Compliance Reports', 'Calibration', 'Probe Replacement', 'Alarm Monitoring'] },
  { key: 'asset' as const, level: 'L2-L3', systems: ['AssetPulse', 'Asset Tags', 'Geofence Alerts', 'Inventory', 'Multi-site Reports'] },
  { key: 'agri' as const, level: 'L3-L4', systems: ['AgriBrain', 'Soil & Climate', 'Irrigation', 'Seasonal Service'] },
  { key: 'retrofit' as const, level: 'L3-L4', systems: ['CCTV', 'Network', 'Lighting', 'Energy Monitoring'] },
  { key: 'custom' as const, level: 'L4-L5', systems: ['Offline AI', 'Network', 'CCTV', 'Energy Monitoring'] },
]

const questionOrder: Record<CategoryKey, Array<{ key: string; module: string }>> = {
  villa: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'existing', module: 'existing' }, { key: 'goals', module: 'goals' }, { key: 'identity', module: 'identity' }, { key: 'energy', module: 'energy' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  school: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'existing', module: 'existing' }, { key: 'goals', module: 'goals' }, { key: 'energy', module: 'energy' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  apartment: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'existing', module: 'existing' }, { key: 'goals', module: 'goals' }, { key: 'energy', module: 'energy' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  office: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'existing', module: 'existing' }, { key: 'goals', module: 'goals' }, { key: 'identity', module: 'identity' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  factory: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'existing', module: 'existing' }, { key: 'production', module: 'production' }, { key: 'goals', module: 'goals' }, { key: 'energy', module: 'energy' }, { key: 'identity', module: 'identity' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  hotel: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'existing', module: 'existing' }, { key: 'goals', module: 'goals' }, { key: 'energy', module: 'energy' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  energy: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'existing', module: 'existing' }, { key: 'goals', module: 'goals' }, { key: 'energy', module: 'energy' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  storage: [{ key: 'location', module: 'location' }, { key: 'storage_type', module: 'storage_type' }, { key: 'temperature_humidity', module: 'temperature_humidity' }, { key: 'compliance_use', module: 'compliance_use' }, { key: 'outage', module: 'outage' }, { key: 'alert_channels', module: 'alert_channels' }, { key: 'monitoring_points', module: 'monitoring_points' }, { key: 'calibration_cycle', module: 'calibration_cycle' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  kitchen: [{ key: 'location', module: 'location' }, { key: 'kitchen_count', module: 'kitchen_count' }, { key: 'gas_type', module: 'gas_type' }, { key: 'alarm_contacts', module: 'alarm_contacts' }, { key: 'service_term', module: 'service_term' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  water: [{ key: 'location', module: 'location' }, { key: 'water_system', module: 'water_system' }, { key: 'parameters', module: 'parameters' }, { key: 'reporting', module: 'reporting' }, { key: 'service_term', module: 'service_term' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  asset: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'goals', module: 'goals' }, { key: 'monitoring_points', module: 'monitoring_points' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  agri: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'goals', module: 'goals' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  retrofit: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'existing', module: 'existing' }, { key: 'goals', module: 'goals' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
  custom: [{ key: 'location', module: 'location' }, { key: 'building', module: 'site' }, { key: 'goals', module: 'goals' }, { key: 'existing', module: 'existing' }, { key: 'budget', module: 'budget' }, { key: 'contact', module: 'contact' }],
}

const projectCategories = computed(() => categoryDefs.map((category) => ({
  ...category,
  label: t(`lead.categories.${category.key}.label`),
  description: t(`lead.categories.${category.key}.description`),
})))

const levelOptions = computed(() => (['L3', 'L4', 'L5'] as LevelKey[]).map((key) => ({
  key,
  label: t(`lead.levels.${key}.label`),
  description: t(`lead.levels.${key}.description`),
})))

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

const selectedCategory = computed(() => projectCategories.value.find((item) => item.key === selectedKey.value) || null)
const targetLevelMeta = computed(() => levelOptions.value.find((item) => item.key === targetLevel.value) || levelOptions.value[0])
const currentQuestions = computed(() => {
  if (!selectedKey.value) return []
  return (questionOrder[selectedKey.value] || []).map((item) => ({
    ...item,
    prompt: t(`lead.questions.${selectedKey.value}.${item.key}.prompt`),
    placeholder: t(`lead.questions.${selectedKey.value}.${item.key}.placeholder`),
  }))
})
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
  if (leadScore.value >= 85) return t('lead.stages.phase1Ready')
  if (leadScore.value >= 70) return t('lead.stages.qualified')
  if (leadScore.value >= 45) return t('lead.stages.warm')
  return t('lead.stages.cold')
})

const proposalPlans = computed(() => {
  const industrialProject = selectedKey.value === 'factory'
  const largeProject = ['school', 'office', 'hotel'].includes(selectedKey.value || '')
  const ranges = industrialProject
    ? { budget: '30k-100k EUR', standard: '100k-300k EUR', premium: '300k-800k+ EUR' }
    : largeProject
    ? { budget: '15k-50k EUR', standard: '50k-100k EUR', premium: '100k-250k EUR' }
    : { budget: '5k-15k EUR', standard: '15k-50k EUR', premium: '50k-120k EUR' }
  return [
    {
      tier: 'budget',
      name: t('lead.plans.budget.name'),
      level: 'L1-L2',
      complexity: t('lead.plans.budget.complexity'),
      risk: t('lead.plans.budget.risk'),
      device: ranges.budget,
      support: t('lead.plans.budget.support'),
      summary: industrialProject ? t('lead.plans.budget.summaryIndustrial') : t('lead.plans.budget.summary'),
    },
    {
      tier: 'standard',
      name: t('lead.plans.standard.name'),
      level: 'L2-L3',
      complexity: t('lead.plans.standard.complexity'),
      risk: t('lead.plans.standard.risk'),
      device: ranges.standard,
      support: t('lead.plans.standard.support'),
      summary: industrialProject ? t('lead.plans.standard.summaryIndustrial') : t('lead.plans.standard.summary'),
    },
    {
      tier: 'premium_ai',
      name: t('lead.plans.premium_ai.name'),
      level: targetLevel.value === 'L5' ? 'L4-L5' : 'L3-L4',
      complexity: t('lead.plans.premium_ai.complexity'),
      risk: t('lead.plans.premium_ai.risk'),
      device: ranges.premium,
      support: t('lead.plans.premium_ai.support'),
      summary: industrialProject ? t('lead.plans.premium_ai.summaryIndustrial') : t('lead.plans.premium_ai.summary'),
    },
    {
      tier: 'future_autonomous',
      name: t('lead.plans.future_autonomous.name'),
      level: 'L5-L6',
      complexity: t('lead.plans.future_autonomous.complexity'),
      risk: t('lead.plans.future_autonomous.risk'),
      device: t('lead.plans.future_autonomous.device'),
      support: t('lead.plans.future_autonomous.support'),
      summary: t('lead.plans.future_autonomous.summary'),
    },
  ]
})

const previewModules = computed(() => {
  const modules = selectedKey.value === 'storage'
    ? [
        { key: 'category', answerKey: 'category' },
        { key: 'location', answerKey: 'location' },
        { key: 'storage_type', answerKey: 'storage_type' },
        { key: 'temperature_humidity', answerKey: 'temperature_humidity' },
        { key: 'compliance_use', answerKey: 'compliance_use' },
        { key: 'outage', answerKey: 'outage' },
        { key: 'alert_channels', answerKey: 'alert_channels' },
        { key: 'monitoring_points', answerKey: 'monitoring_points' },
        { key: 'calibration_cycle', answerKey: 'calibration_cycle' },
        { key: 'budget', answerKey: 'budget' },
        { key: 'contact', answerKey: 'contact' },
      ]
    : [
        { key: 'category', answerKey: 'category' },
        { key: 'location', answerKey: 'location' },
        { key: 'site', answerKey: 'site' },
        { key: 'existing', answerKey: 'existing' },
        { key: 'production', answerKey: 'production' },
        { key: 'goals', answerKey: 'goals' },
        { key: 'identity', answerKey: 'identity' },
        { key: 'energy', answerKey: 'energy' },
        { key: 'budget', answerKey: 'budget' },
        { key: 'contact', answerKey: 'contact' },
      ]
  const activeModule = currentQuestion.value?.module
  return modules.map((module) => ({
    key: module.key,
    label: t(`lead.modules.${module.key}`),
    summary: module.key === 'category'
      ? (selectedCategory.value?.label || t('lead.moduleHints.category'))
      : (answers[module.answerKey] || t(`lead.moduleHints.${module.key}`)),
    done: module.key === 'category' || Boolean(answers[module.answerKey]),
    active: module.key === activeModule,
  }))
})

function scrollChat() {
  nextTick(() => {
    if (chatScroll.value) chatScroll.value.scrollTop = chatScroll.value.scrollHeight
  })
}

function pushAi(text: string, tag = t('lead.tagGap')) {
  messages.value.push({ id: Date.now() + Math.random(), role: 'ai', text, tag })
  scrollChat()
}

function pushUser(text: string) {
  messages.value.push({ id: Date.now() + Math.random(), role: 'user', text, tag: t('lead.tagIntake') })
  scrollChat()
}

async function startCategory(key: CategoryKey) {
  selectedKey.value = key
  const category = projectCategories.value.find((item) => item.key === key)
  targetLevel.value = category?.level.includes('L5') ? 'L5' : 'L3'
  messages.value = []
  Object.keys(answers).forEach((answerKey) => delete answers[answerKey])
  currentIndex.value = 0
  submitted.value = false
  phase1Requested.value = false
  aiComplete.value = false

  if (assistant.enabled.value) {
    loading.value = true
    try {
      const res = await assistant.ask(key, [{ role: 'user', content: t('lead.assistantSeed', { category: category?.label }) }], { target_intelligence_level: targetLevel.value })
      if (res?.configured && res.reply) {
        pushAi(res.reply, res.complete ? t('lead.tagReady') : t('lead.tagAi'))
        if (res.complete) aiComplete.value = true
        return
      }
    } catch {
      // fall through to scripted
    } finally {
      loading.value = false
    }
  }
  pushAi(t('lead.chatOpening', { category: category?.label, prompt: currentQuestion.value?.prompt || '' }))
}

function askNextQuestion() {
  if (currentQuestion.value) {
    pushAi(currentQuestion.value.prompt, t('lead.tagAi'))
  } else {
    pushAi(t('lead.chatEnough'), t('lead.tagReady'))
  }
}

const readyToSubmit = computed(() => aiComplete.value || !currentQuestion.value)

async function sendMessage() {
  error.value = ''
  if (!draft.value.trim()) {
    if (readyToSubmit.value && !submitted.value) await submitLead()
    return
  }
  const text = draft.value.trim()
  draft.value = ''
  pushUser(text)

  if (assistant.enabled.value && selectedCategory.value) {
    loading.value = true
    try {
      const history = messages.value.map((m) => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text }))
      const res = await assistant.ask(selectedCategory.value.key, history, { ...answers, target_intelligence_level: targetLevel.value })
      if (res?.configured) {
        mergeExtracted(res.extracted)
        if (res.reply) pushAi(res.reply, res.complete ? t('lead.tagReady') : t('lead.tagAi'))
        if (res.complete) aiComplete.value = true
        return
      }
    } catch {
      // fall through to scripted flow
    } finally {
      loading.value = false
    }
  }

  if (currentQuestion.value) {
    answers[currentQuestion.value.module] = text
    currentIndex.value += 1
    const next = currentQuestion.value
    if (next) {
      pushAi(t('lead.chatCaptured', { prompt: next.prompt }))
      return
    }
    pushAi(t('lead.chatComplete', {
      level: targetLevel.value,
      levelLabel: targetLevelMeta.value.label,
      notice: estimateNotice.value,
    }), t('lead.tagReady'))
    return
  }

  await submitLead()
}

async function requestPhase1Proposal() {
  phase1Requested.value = true
  pushUser(t('lead.requestPhase1'))
  pushAi(t('lead.chatPhase1Ack'), t('lead.tagPhase1'))
  await submitLead(true)
}

function resetForge() {
  selectedKey.value = null
  messages.value = []
  Object.keys(answers).forEach((answerKey) => delete answers[answerKey])
  currentIndex.value = 0
  submitted.value = false
  phase1Requested.value = false
  aiComplete.value = false
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
    const { getAttribution } = useMarketingAttribution()
    const transcript = messages.value.map((message) => `${message.role.toUpperCase()}: ${message.text}`).join('\n\n')
    await apiFetch('/leads', {
      method: 'POST',
      body: {
        ...getAttribution(),
        project_type: selectedCategory.value.label,
        country: answers.location || '',
        budget_range: budgetToRange(answers.budget || ''),
        systems_needed_json: selectedCategory.value.systems,
        description: [
          `AI Project Forge transcript for ${selectedCategory.value.label}.`,
          `Target intelligence level: ${targetLevel.value} ${targetLevelMeta.value.label}.`,
          `Lead score: ${leadScore.value} (${leadStage.value}).`,
          phase1Requested.value ? 'Customer requested paid Phase-1 Proposal.' : 'Customer has not requested Phase-1 Proposal yet.',
          estimateNotice.value,
          transcript,
        ].join('\n\n'),
        contact_name: answers.contact?.split(',')?.[0] || 'AI Assessment Lead',
        contact_email: extractEmail(answers.contact || '') || 'unknown@ainerwise.local',
        contact_phone: answers.contact || '',
        site_info_json: {
          ...answers,
          target_intelligence_level: targetLevel.value,
          category_key: selectedCategory.value.key,
          lead_score: leadScore.value,
          lead_stage: leadStage.value,
          phase1_requested: phase1Requested.value,
          proposal_tiers: proposalPlans.value,
          building: answers.building || answers.site,
          existing_systems: answers.existing,
          production_machines: answers.production,
          smart_goals: answers.goals,
          identity_access: answers.identity,
          energy_solar: answers.energy,
          storage_type: answers.storage_type,
          temperature_humidity: answers.temperature_humidity,
          compliance_use: answers.compliance_use,
          outage_protection: answers.outage,
          alert_channels: answers.alert_channels,
          monitoring_points: answers.monitoring_points,
          calibration_cycle: answers.calibration_cycle,
          budget_and_service: answers.budget,
          estimate_notice: estimateNotice.value,
          transcript: messages.value,
        },
      },
    })
    submitted.value = true
    pushAi(t('lead.chatSubmitted'), t('lead.tagSubmitted'))
  } catch (e: any) {
    error.value = e?.data?.detail || t('lead.submitFailed')
  } finally {
    loading.value = false
  }
}
</script>
