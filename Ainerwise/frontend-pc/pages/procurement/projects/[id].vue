<template>
  <div v-if="loading" class="pc-card text-slate-400">{{ $t('common.loading') }}</div>
  <div v-else-if="error" class="pc-card text-red-400">{{ error }}</div>
  <div v-else-if="project">
    <NuxtLink to="/procurement" class="mb-4 inline-flex text-sm text-slate-400 hover:text-white">
      ← {{ $t('procurement.backToList') }}
    </NuxtLink>

    <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-white">{{ project.title }}</h1>
        <p class="mt-1 text-sm text-slate-500">
          {{ project.status.replace(/_/g, ' ') }} · v{{ boq?.version ?? '—' }}
          <span v-if="boq?.status === 'frozen'" class="ml-2 text-emerald-300">
            {{ $t('procurement.boqFrozen') }}
          </span>
        </p>
      </div>
    </div>

    <ProcurementStepper :steps="steps" :active="activeStep" @select="goStep" />

    <ProcurementConfidencePanel
      :overall="project.overall_confidence"
      :facts-score="project.facts_score"
      :boq-score="project.boq_score"
      :facts="facts"
      :gate="policy?.confidence_gate"
      :disclaimer="String(boq?.disclaimer || '')"
      :project-status="project.status"
    />

    <!-- Brief -->
    <section v-if="activeStep === 'brief'" class="pc-card space-y-3">
      <h2 class="font-bold text-white">{{ $t('procurement.steps.brief') }}</h2>
      <p class="text-sm text-slate-400">{{ project.description || $t('procurement.noDescription') }}</p>
      <dl class="grid gap-2 text-sm sm:grid-cols-2">
        <div><dt class="text-slate-500">{{ $t('procurement.fields.type') }}</dt><dd class="text-white">{{ project.project_type }}</dd></div>
        <div><dt class="text-slate-500">{{ $t('procurement.fields.country') }}</dt><dd class="text-white">{{ project.country || '—' }}</dd></div>
        <div><dt class="text-slate-500">{{ $t('procurement.mode') }}</dt><dd class="text-white">{{ policy?.default_procurement_mode }}</dd></div>
        <div><dt class="text-slate-500">{{ $t('procurement.priceRule') }}</dt><dd class="text-white">{{ policy?.price_visibility_rule }}</dd></div>
      </dl>
    </section>

    <!-- Files -->
    <section v-else-if="activeStep === 'files'" class="pc-card">
      <h2 class="font-bold text-white">{{ $t('procurement.steps.files') }}</h2>
      <p class="mt-2 text-sm text-slate-400">{{ $t('procurement.filesHint') }}</p>
    </section>

    <!-- Facts -->
    <section v-else-if="activeStep === 'facts'" class="space-y-4">
      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-primary" :disabled="busy" @click="runAnalyze">
          {{ $t('procurement.runAnalyze') }}
        </button>
      </div>
      <div v-for="fact in facts" :key="fact.id" class="pc-card">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p class="font-medium text-white">{{ fact.label }}</p>
            <p class="text-xs text-slate-500">{{ fact.template_key }}</p>
          </div>
          <span class="text-xs" :class="fact.user_confirmed ? 'text-emerald-300' : 'text-amber-300'">
            {{ fact.user_confirmed ? $t('procurement.confirmed') : $t('procurement.pending') }}
          </span>
        </div>
        <textarea v-model="factEdits[fact.id]" class="input-field mt-3" rows="2" />
        <div class="mt-2 flex gap-2">
          <button type="button" class="btn-secondary text-sm" :disabled="busy" @click="saveFact(fact.id, false)">
            {{ $t('common.save') }}
          </button>
          <button type="button" class="btn-primary text-sm" :disabled="busy" @click="saveFact(fact.id, true)">
            {{ $t('procurement.confirmFact') }}
          </button>
        </div>
      </div>
    </section>

    <!-- BOQ -->
    <section v-else-if="activeStep === 'boq'" class="pc-card space-y-4">
      <h2 class="font-bold text-white">{{ $t('procurement.steps.boq') }}</h2>
      <p v-if="!boq" class="text-sm text-slate-400">{{ $t('procurement.noBoq') }}</p>
      <template v-else>
        <p class="text-sm text-slate-400">
          {{ $t('procurement.boqVersion') }} {{ boq.version }} · {{ boq.status }}
        </p>
        <div
          v-for="item in boq.items || []"
          :key="item.id"
          class="rounded-lg border border-white/10 p-4"
          :class="boq.status === 'frozen' ? 'opacity-90' : ''"
        >
          <p class="font-medium text-white">{{ item.name }}</p>
          <p class="text-xs text-slate-500">{{ item.category }} · {{ item.qty }} {{ item.unit }}</p>
          <p v-if="item.quantity_basis" class="mt-1 text-xs text-slate-400">{{ item.quantity_basis }}</p>
          <div v-if="showLineEstimates && item.options?.length" class="mt-2 text-xs text-slate-300">
            <span v-for="opt in item.options" :key="opt.tier" class="mr-3">
              {{ opt.tier }}: {{ opt.total_price_min }}–{{ opt.total_price_max }} {{ opt.currency }}
            </span>
          </div>
        </div>
      </template>
    </section>

    <!-- Plans -->
    <section v-else-if="activeStep === 'plans'" class="pc-card space-y-4">
      <h2 class="font-bold text-white">{{ $t('procurement.steps.plans') }}</h2>
      <p v-if="confidencePhaseNum < 0.6" class="text-amber-300 text-sm">
        {{ $t('procurement.confidence.phaseAsk') }}
      </p>
      <div v-else class="grid gap-4 md:grid-cols-3">
        <div
          v-for="plan in boq?.solution_plans || []"
          :key="plan.tier"
          class="rounded-lg border border-white/10 p-4"
        >
          <p class="text-xs uppercase tracking-wider text-slate-500">{{ plan.tier }}</p>
          <p v-if="showLineEstimates" class="mt-2 text-lg font-bold text-white">
            {{ plan.total_min }} – {{ plan.total_max }} {{ plan.currency }}
          </p>
          <p v-else class="mt-2 text-sm text-slate-400">{{ $t('procurement.totalsHidden') }}</p>
          <p v-if="plan.estimate_only" class="mt-2 text-xs text-amber-300">{{ $t('procurement.estimateOnly') }}</p>
          <p class="mt-2 text-sm text-slate-400">{{ plan.summary }}</p>
        </div>
      </div>
    </section>

    <!-- Review & Freeze -->
    <section v-else-if="activeStep === 'review' || activeStep === 'freeze'" class="pc-card space-y-4">
      <h2 class="font-bold text-white">
        {{ activeStep === 'freeze' ? $t('procurement.steps.freeze') : $t('procurement.steps.review') }}
      </h2>
      <p class="text-sm text-slate-400">{{ reviewHint }}</p>
      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="btn-secondary"
          :disabled="busy || !canSubmitReview"
          @click="submitReview"
        >
          {{ $t('procurement.submitReview') }}
        </button>
        <button
          type="button"
          class="btn-primary"
          :disabled="busy || !canFreeze"
          @click="freezeBoq"
        >
          {{ $t('procurement.freezeBoq') }}
        </button>
      </div>
    </section>

    <!-- Packages -->
    <section v-else-if="activeStep === 'packages'" class="space-y-4">
      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-primary" :disabled="busy || !canGeneratePackages" @click="generatePackages">
          {{ packages.length ? $t('procurement.regeneratePackages') : $t('procurement.generatePackages') }}
        </button>
      </div>
      <div v-for="pkg in packages" :key="pkg.id" class="pc-card space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h3 class="font-semibold text-white">{{ pkg.title }}</h3>
          <span class="text-xs text-slate-400">{{ pkg.status }} · {{ pkg.procurement_mode }}</span>
        </div>
        <p class="text-xs text-slate-500">{{ pkg.trade }} / {{ pkg.commercial_type }} · {{ pkg.items.length }} items</p>
        <div class="flex flex-wrap gap-2">
          <select v-model="packageEdits[pkg.id].mode" class="input-field max-w-xs text-sm">
            <option value="managed">managed</option>
            <option value="self_service">self_service</option>
          </select>
          <button
            type="button"
            class="btn-secondary text-sm"
            :disabled="busy || pkg.status === 'published'"
            @click="savePackage(pkg.id)"
          >
            {{ $t('procurement.markReady') }}
          </button>
          <button
            type="button"
            class="btn-primary text-sm"
            :disabled="busy || pkg.status === 'published'"
            @click="goPublish(pkg.id)"
          >
            {{ $t('procurement.goPublish') }}
          </button>
        </div>
        <div v-if="showSuppliers && pkg.candidate_partners?.length" class="text-xs text-slate-400">
          {{ pkg.candidate_partners.length }} {{ $t('procurement.candidatePartners') }}
        </div>
      </div>
    </section>

    <!-- RFQ Publish -->
    <section v-else-if="activeStep === 'rfq'" class="space-y-4">
      <div v-if="project.status === 'rfq_published'" class="pc-card text-emerald-300">
        {{ $t('procurement.rfqPublished') }}
      </div>
      <form v-else class="pc-card space-y-4" @submit.prevent="confirmPublish">
        <h2 class="font-bold text-white">{{ $t('procurement.snapshotConfirm') }}</h2>
        <p class="text-sm text-slate-400">{{ $t('procurement.snapshotHint') }}</p>
        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="text-xs text-slate-500">{{ $t('procurement.fields.currency') }}</label>
            <input v-model="commercial.currency" class="input-field" required />
          </div>
          <div>
            <label class="text-xs text-slate-500">{{ $t('procurement.fields.taxMode') }}</label>
            <input v-model="commercial.tax_mode" class="input-field" required />
          </div>
        </div>
        <p class="text-xs text-slate-500">{{ $t('procurement.policyNote') }}</p>
        <p v-if="actionError" class="text-sm text-red-400">{{ actionError }}</p>
        <button type="submit" class="btn-primary" :disabled="busy || !selectedPackageId">
          {{ $t('procurement.publishRfq') }}
        </button>
      </form>
      <pre v-if="publishResult" class="pc-card overflow-auto text-xs text-slate-300">{{ JSON.stringify(publishResult, null, 2) }}</pre>
    </section>

    <p v-if="actionError && activeStep !== 'rfq'" class="mt-4 text-sm text-red-400">{{ actionError }}</p>
  </div>
</template>

<script setup lang="ts">
import type { PortalPolicy, ProcurementFact, ProcurementPackage, ProcurementProject } from '~/composables/useProcurement'
import { confidencePhase, parseConfidence } from '~/composables/useProcurement'

definePageMeta({
  layout: 'procurement',
  middleware: ['auth'],
})

const route = useRoute()
const projectId = computed(() => String(route.params.id))
const procurement = useProcurement()
const policy = useState<PortalPolicy | null>('procurement-portal-policy', () => null)
const { showLineEstimates, showSuppliers } = useProcurementBrand(policy)

const steps = computed(() => [
  { key: 'brief', label: 'Brief' },
  { key: 'files', label: 'Files' },
  { key: 'facts', label: 'Facts' },
  { key: 'boq', label: 'BOQ' },
  { key: 'plans', label: 'Plans' },
  { key: 'review', label: 'Review' },
  { key: 'freeze', label: 'Freeze' },
  { key: 'packages', label: 'Packages' },
  { key: 'rfq', label: 'RFQ' },
])

const project = ref<ProcurementProject | null>(null)
const facts = ref<ProcurementFact[]>([])
const factEdits = reactive<Record<string, string>>({})
const boq = ref<Record<string, any> | null>(null)
const packages = ref<ProcurementPackage[]>([])
const packageEdits = reactive<Record<string, { mode: string }>>({})
const loading = ref(true)
const error = ref('')
const busy = ref(false)
const actionError = ref('')
const publishResult = ref<Record<string, unknown> | null>(null)
const selectedPackageId = ref('')

const commercial = reactive({
  currency: 'USD',
  tax_mode: 'exclusive',
  exchange_rate_snapshot_json: { base: 'USD', quote: 'PHP', rate: '56.5' },
  margin_rule_json: { type: 'percent', value: '0.15' },
  service_fee_json: { platform_fee_percent: '0.05' },
  warranty_rule_json: { months: 12 },
  delivery_region_json: { country: 'PH' },
  quote_expiry: new Date(Date.now() + 30 * 86400000).toISOString(),
  payment_terms_json: { net_days: 30 },
})

const activeStep = computed({
  get: () => String(route.query.step || stepFromStatus(project.value?.status || 'draft')),
  set: (value: string) => navigateTo({ query: { ...route.query, step: value } }),
})

const confidencePhaseNum = computed(() => {
  const overall = parseConfidence(project.value?.overall_confidence)
  return overall
})

const { t } = useI18n()

const canSubmitReview = computed(() => {
  const phase = confidencePhase(confidencePhaseNum.value, policy.value?.confidence_gate)
  return phase === 'review' && boq.value && boq.value.status !== 'frozen'
})

const canFreeze = computed(() => {
  return (
    project.value?.status === 'review_approved'
    && boq.value?.status !== 'frozen'
    && confidencePhaseNum.value >= 0.8
  )
})

const canGeneratePackages = computed(() =>
  ['boq_frozen', 'packaged', 'rfq_published'].includes(project.value?.status || ''),
)

const reviewHint = computed(() => {
  if (confidencePhaseNum.value < 0.8) return t('procurement.freezeDisabled')
  if (project.value?.status === 'in_review') return t('procurement.waitingReview')
  return t('procurement.reviewHint')
})

function stepFromStatus(status: string): string {
  const map: Record<string, string> = {
    draft: 'brief',
    collecting: 'facts',
    analyzing: 'facts',
    needs_information: 'facts',
    estimate_ready: 'boq',
    review_ready: 'plans',
    in_review: 'review',
    review_approved: 'freeze',
    boq_frozen: 'packages',
    packaged: 'packages',
    rfq_published: 'rfq',
  }
  return map[status] || 'brief'
}

function goStep(key: string) {
  activeStep.value = key
}

function goPublish(packageId: string) {
  selectedPackageId.value = packageId
  commercial.delivery_region_json = { country: project.value?.country || 'PH' }
  goStep('rfq')
}

async function reload() {
  project.value = await procurement.getProject(projectId.value)
  facts.value = await procurement.listFacts(projectId.value)
  for (const fact of facts.value) {
    factEdits[fact.id] = String(fact.value_json ?? '')
  }
  try {
    boq.value = await procurement.getBoq(projectId.value)
  } catch {
    boq.value = null
  }
  if (['boq_frozen', 'packaged', 'rfq_published'].includes(project.value.status)) {
    packages.value = await procurement.listPackages(projectId.value)
    for (const pkg of packages.value) {
      packageEdits[pkg.id] = { mode: pkg.procurement_mode }
    }
  }
}

async function init() {
  loading.value = true
  error.value = ''
  try {
    policy.value = await procurement.fetchPortalPolicy()
    await reload()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Failed to load project'
  } finally {
    loading.value = false
  }
}

async function saveFact(factId: string, confirm: boolean) {
  busy.value = true
  actionError.value = ''
  try {
    await procurement.patchFact(projectId.value, factId, {
      value_json: factEdits[factId],
      user_confirmed: confirm,
    })
    await reload()
  } catch (e: any) {
    actionError.value = e?.data?.detail || e?.message || 'Save failed'
  } finally {
    busy.value = false
  }
}

async function runAnalyze() {
  busy.value = true
  actionError.value = ''
  try {
    await procurement.analyzeProject(projectId.value)
    await reload()
    goStep('boq')
  } catch (e: any) {
    actionError.value = e?.data?.detail || e?.message || 'Analyze failed'
  } finally {
    busy.value = false
  }
}

async function submitReview() {
  busy.value = true
  actionError.value = ''
  try {
    await procurement.submitBoqReview(projectId.value, boq.value?.version_id)
    await reload()
  } catch (e: any) {
    actionError.value = e?.data?.detail || e?.message || 'Review submit failed'
  } finally {
    busy.value = false
  }
}

async function freezeBoq() {
  busy.value = true
  actionError.value = ''
  try {
    await procurement.freezeBoq(projectId.value, boq.value?.version_id)
    await reload()
    goStep('packages')
  } catch (e: any) {
    actionError.value = e?.data?.detail || e?.message || 'Freeze failed'
  } finally {
    busy.value = false
  }
}

async function generatePackages() {
  busy.value = true
  actionError.value = ''
  try {
    const result = await procurement.generatePackages(projectId.value)
    packages.value = result.packages
    for (const pkg of packages.value) {
      packageEdits[pkg.id] = { mode: pkg.procurement_mode }
    }
    await reload()
  } catch (e: any) {
    actionError.value = e?.data?.detail || e?.message || 'Package generation failed'
  } finally {
    busy.value = false
  }
}

async function savePackage(packageId: string) {
  busy.value = true
  actionError.value = ''
  try {
    await procurement.patchPackage(projectId.value, packageId, {
      procurement_mode: packageEdits[packageId]?.mode,
      status: 'ready',
    })
    await reload()
  } catch (e: any) {
    actionError.value = e?.data?.detail || e?.message || 'Package update failed'
  } finally {
    busy.value = false
  }
}

async function confirmPublish() {
  if (!selectedPackageId.value) return
  busy.value = true
  actionError.value = ''
  try {
    publishResult.value = await procurement.publishRfq(projectId.value, selectedPackageId.value, {
      ...commercial,
    })
    await reload()
  } catch (e: any) {
    actionError.value = e?.data?.detail || e?.message || 'Publish failed'
  } finally {
    busy.value = false
  }
}

onMounted(init)
watch(() => route.params.id, init)
</script>
