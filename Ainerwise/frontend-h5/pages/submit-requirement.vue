<template>
  <div class="px-4 py-4">
    <!-- Not logged in -->
    <div v-if="!isLoggedIn" class="text-center py-16">
      <div class="w-20 h-20 mx-auto rounded-full bg-blue-50 flex items-center justify-center mb-4">
        <svg class="w-10 h-10 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
        </svg>
      </div>
      <h2 class="text-lg font-bold text-slate-800">{{ $t('lead.loginRequired') }}</h2>
      <NuxtLink to="/login?redirect=/submit-requirement" class="inline-block mt-5 text-sm font-semibold bg-blue-500 text-white px-8 py-3 rounded-full shadow-md shadow-blue-500/20">{{ $t('nav.login') }}</NuxtLink>
    </div>

    <template v-else>
      <h1 class="text-lg font-bold text-slate-800 mb-1">{{ $t('lead.forgeTitle') }}</h1>
      <p class="text-xs text-slate-400 mb-3">{{ $t('lead.forgeSubtitle') }}</p>

      <!-- Step 1: category cards -->
      <div v-if="!selectedKey" class="grid grid-cols-2 gap-2.5">
        <button v-for="c in categories" :key="c.key" type="button"
          class="text-left bg-white rounded-2xl p-3.5 border border-slate-100 shadow-sm active:bg-slate-50"
          @click="startCategory(c.key)">
          <p class="text-[10px] font-bold uppercase tracking-wider text-blue-500">{{ c.level }}</p>
          <h3 class="mt-1 text-sm font-bold text-slate-800 leading-tight">{{ c.label }}</h3>
        </button>
      </div>

      <!-- Step 2: chat -->
      <div v-else class="space-y-3">
        <div class="flex items-center justify-between gap-2">
          <p class="text-sm font-bold text-slate-800">{{ selectedCategory?.label }}</p>
          <button type="button" class="text-xs text-slate-400" @click="reset">{{ $t('lead.changeCategory') }}</button>
        </div>

        <div ref="chatScroll" class="bg-white rounded-2xl border border-slate-100 shadow-sm p-3 h-[58vh] overflow-y-auto space-y-3">
          <div v-for="m in messages" :key="m.id" class="flex" :class="m.role === 'user' ? 'justify-end' : 'justify-start'">
            <div class="max-w-[82%] rounded-2xl px-3 py-2 text-xs leading-relaxed"
              :class="m.role === 'user' ? 'bg-blue-500 text-white' : 'bg-slate-100 text-slate-700'">
              <p class="whitespace-pre-wrap">{{ m.text }}</p>
            </div>
          </div>
        </div>

        <div v-if="submitted" class="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs text-emerald-700">
          {{ $t('lead.submittedNotice') }}
        </div>
        <form v-else class="flex gap-2" @submit.prevent="sendMessage">
          <input v-model="draft" type="text" :placeholder="$t('lead.answerPlaceholder')"
            class="flex-1 text-sm border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20" />
          <button type="submit" :disabled="loading || (!readyToSubmit && !draft.trim())"
            class="text-sm font-semibold bg-blue-500 text-white px-4 rounded-xl disabled:opacity-50">
            {{ loading ? '…' : (readyToSubmit && !draft.trim()) ? $t('lead.submit') : $t('lead.send') }}
          </button>
        </form>
        <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
        <p class="text-[11px] text-amber-600 bg-amber-50 rounded-xl p-2.5">{{ estimateNotice }}</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
const { isLoggedIn } = useAuth()
const { apiFetch } = useApi()
const assistant = useAssistant()

const estimateNotice = 'AI estimate only. Final quote requires manual review, site survey, supplier confirmation, and signed contract.'

const categories = [
  { key: 'villa', label: 'Smart Villa / Home', level: 'L3-L5', systems: ['KNX', 'Home Assistant', 'CCTV', 'Energy Monitoring'] },
  { key: 'storage', label: 'Cold Chain / Storage', level: 'StorageGuard', systems: ['StorageGuard', 'Temperature & Humidity Monitoring', 'Door Sensors', 'Outage Alerts', 'Compliance Reports'] },
  { key: 'kitchen', label: 'Kitchen Safety', level: 'KitchenGuard', systems: ['KitchenGuard', 'Gas & CO Monitoring', 'Water Leak', 'Alarm Monitoring'] },
  { key: 'water', label: 'Water / Effluent', level: 'AquaGuard', systems: ['AquaGuard', 'pH / EC / Turbidity / COD', 'Compliance Reports', 'Calibration'] },
  { key: 'energy', label: 'Solar / Energy', level: 'EnergyGuard', systems: ['EnergyGuard', 'Solar', 'Battery', 'EV Charging', 'Energy Monitoring'] },
  { key: 'factory', label: 'Factory / Industrial', level: 'FactoryPulse', systems: ['FactoryPulse', 'PLC/SCADA', 'Machine Energy Monitoring', 'OT Network'] },
  { key: 'office', label: 'Office / Hotel', level: 'L3-L4', systems: ['HVAC', 'Lighting', 'Access Control', 'CCTV'] },
  { key: 'asset', label: 'Asset Tracking', level: 'AssetPulse', systems: ['AssetPulse', 'Asset Tags', 'Geofence Alerts', 'Inventory'] },
] as const

type CKey = typeof categories[number]['key']

// Compact scripted fallback (used when AI agent is not configured).
const questionBank: Record<string, { module: string; prompt: string }[]> = {
  _default: [
    { module: 'location', prompt: 'Where is the site located (country and city)?' },
    { module: 'site', prompt: 'Briefly describe the site: size, rooms/zones, and what exists today.' },
    { module: 'goals', prompt: 'What is the main goal: monitoring, compliance, energy, safety, automation?' },
    { module: 'monitoring_points', prompt: 'Roughly how many monitoring points / devices?' },
    { module: 'budget', prompt: 'What budget range and service period should we design around?' },
    { module: 'contact', prompt: 'Finally, your name and email/phone for follow-up?' },
  ],
}

const selectedKey = ref<CKey | null>(null)
const selectedCategory = computed(() => categories.find((c) => c.key === selectedKey.value) || null)
const messages = ref<Array<{ id: number; role: 'ai' | 'user'; text: string }>>([])
const answers = reactive<Record<string, string>>({})
const idx = ref(0)
const draft = ref('')
const loading = ref(false)
const submitted = ref(false)
const aiComplete = ref(false)
const error = ref('')
const chatScroll = ref<HTMLElement | null>(null)

const scriptQuestions = computed(() => questionBank[selectedKey.value || ''] || questionBank._default)
const currentQ = computed(() => scriptQuestions.value[idx.value] || null)
const readyToSubmit = computed(() => aiComplete.value || !currentQ.value)

onMounted(() => { assistant.checkStatus() })

function scroll() { nextTick(() => { if (chatScroll.value) chatScroll.value.scrollTop = chatScroll.value.scrollHeight }) }
function pushAi(text: string) { messages.value.push({ id: Date.now() + Math.random(), role: 'ai', text }); scroll() }
function pushUser(text: string) { messages.value.push({ id: Date.now() + Math.random(), role: 'user', text }); scroll() }
function mergeExtracted(ex: Record<string, any>) {
  if (!ex) return
  for (const [k, v] of Object.entries(ex)) {
    if (v === null || v === undefined || v === '') continue
    answers[k] = typeof v === 'string' ? v : JSON.stringify(v)
  }
  if (ex.budget_and_service && !answers.budget) answers.budget = String(ex.budget_and_service)
}

async function startCategory(key: CKey) {
  selectedKey.value = key
  messages.value = []
  Object.keys(answers).forEach((k) => delete answers[k])
  idx.value = 0; submitted.value = false; aiComplete.value = false; error.value = ''
  const label = categories.find((c) => c.key === key)?.label
  if (assistant.enabled.value) {
    loading.value = true
    try {
      const res = await assistant.ask(key, [{ role: 'user', content: `AI facility assessment for: ${label}.` }], {})
      if (res?.configured && res.reply) { pushAi(res.reply); if (res.complete) aiComplete.value = true; return }
    } catch {} finally { loading.value = false }
  }
  pushAi(`Let's assess your ${label} project.\n\n${currentQ.value?.prompt || ''}`)
}

async function sendMessage() {
  error.value = ''
  if (!draft.value.trim()) { if (readyToSubmit.value && !submitted.value) await submitLead(); return }
  const text = draft.value.trim(); draft.value = ''; pushUser(text)

  if (assistant.enabled.value && selectedKey.value) {
    loading.value = true
    try {
      const history = messages.value.map((m) => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text }))
      const res = await assistant.ask(selectedKey.value, history, { ...answers })
      if (res?.configured) {
        mergeExtracted(res.extracted)
        if (res.reply) pushAi(res.reply)
        if (res.complete) aiComplete.value = true
        return
      }
    } catch {} finally { loading.value = false }
  }

  if (currentQ.value) {
    answers[currentQ.value.module] = text
    idx.value += 1
    if (currentQ.value) { pushAi(`Captured.\n\n${currentQ.value.prompt}`); return }
    pushAi('Thanks — I have enough for a preliminary estimate. Tap Submit to send it for review.')
    return
  }
  await submitLead()
}

function extractEmail(v: string) { return v.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0] || '' }
function budgetToRange(v = '') { const l = v.toLowerCase(); if (l.includes('100')) return 'over_100k'; if (l.includes('50')) return '50k_100k'; if (l.includes('15')) return '15k_50k'; if (l.includes('5')) return '5k_15k'; return v || 'to_be_confirmed' }

async function submitLead() {
  if (!selectedCategory.value || submitted.value) return
  loading.value = true; error.value = ''
  try {
    const transcript = messages.value.map((m) => `${m.role.toUpperCase()}: ${m.text}`).join('\n\n')
    await apiFetch('/leads', { method: 'POST', body: {
      project_type: selectedCategory.value.label,
      country: answers.location || '',
      budget_range: budgetToRange(answers.budget),
      systems_needed_json: [...selectedCategory.value.systems],
      description: [`H5 AI assessment for ${selectedCategory.value.label}.`, estimateNotice, transcript].join('\n\n'),
      contact_name: answers.contact?.split(',')?.[0] || 'AI Assessment Lead',
      contact_email: extractEmail(answers.contact || '') || 'unknown@ainerwise.local',
      contact_phone: answers.contact || '',
      site_info_json: { ...answers, category_key: selectedCategory.value.key, estimate_notice: estimateNotice, transcript: messages.value },
    } })
    submitted.value = true
    pushAi('Submitted. AinerWise admin will review the preliminary AI estimate before any quote.')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Submission failed'
  } finally { loading.value = false }
}

function reset() { selectedKey.value = null; messages.value = []; Object.keys(answers).forEach((k) => delete answers[k]); idx.value = 0; submitted.value = false; aiComplete.value = false; error.value = '' }
</script>
