<template>
  <div class="space-y-6">
    <NuxtLink to="/portal/projects" class="inline-flex items-center gap-1 text-sm font-medium text-blue-500 hover:text-blue-600">
      <span aria-hidden="true">&larr;</span>
      Back to Projects
    </NuxtLink>

    <template v-if="project">
      <section class="portal-card">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 class="text-xl font-bold text-slate-800">{{ project.title || project.name }}</h1>
            <p class="mt-1 text-sm text-slate-400">{{ project.region || '-' }}</p>
          </div>
          <span :class="['rounded-full px-3 py-1 text-xs font-semibold', statusClass(project.status)]">
            {{ project.status?.replace(/_/g, ' ') }}
          </span>
        </div>
        <div class="mt-5">
          <div class="flex items-center gap-1">
            <div
              v-for="(step, index) in statusSteps"
              :key="step.key"
              class="h-2 flex-1 rounded-full"
              :class="currentStepIndex >= index ? 'bg-gradient-to-r from-blue-500 to-indigo-500' : 'bg-slate-100'"
            />
          </div>
          <div class="mt-2 flex justify-between text-[10px] font-medium uppercase tracking-wider text-slate-400">
            <span>Planning</span>
            <span>Delivery</span>
            <span>Maintenance</span>
            <span>Closed</span>
          </div>
        </div>
      </section>

      <template v-if="storageguard">
        <section class="portal-card">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 class="text-base font-bold text-slate-800">StorageGuard Monitoring</h2>
              <p v-if="storageguard.scenario" class="mt-1 text-sm leading-relaxed text-slate-500">{{ storageguard.scenario }}</p>
            </div>
            <span v-if="storageguard.sample" class="rounded-full bg-cyan-50 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-cyan-600">
              Sample
            </span>
          </div>
          <div class="mt-5 grid gap-3 sm:grid-cols-4">
            <div v-for="metric in monitoringMetrics" :key="metric.label" class="rounded-xl bg-slate-50 p-4 text-center">
              <p class="text-2xl font-bold text-slate-800">{{ metric.value ?? '—' }}</p>
              <p class="mt-1 text-xs font-medium text-slate-400">{{ metric.label }}</p>
            </div>
          </div>
        </section>

        <div class="grid gap-6 lg:grid-cols-3">
          <section v-if="storageguard.compliance" class="portal-card">
            <div class="flex items-center justify-between gap-3">
              <h2 class="text-sm font-bold text-slate-800">Compliance Risk</h2>
              <span :class="['rounded-full px-2.5 py-1 text-[10px] font-semibold', riskClass(storageguard.compliance.risk_level)]">
                {{ storageguard.compliance.risk_level }} risk
              </span>
            </div>
            <p class="mt-3 text-sm leading-relaxed text-slate-500">{{ storageguard.compliance.risk_note }}</p>
          </section>

          <section v-if="storageguard.economics" class="portal-card">
            <h2 class="text-sm font-bold text-slate-800">Lifecycle Economics</h2>
            <dl class="mt-3 space-y-2 text-sm">
              <div class="flex justify-between gap-3">
                <dt class="text-slate-400">Initial cost</dt>
                <dd class="font-medium text-slate-700">{{ money(storageguard.economics.initial_cost_min, storageguard.economics.initial_cost_max, storageguard.economics.currency) }}</dd>
              </div>
              <div class="flex justify-between gap-3">
                <dt class="text-slate-400">Annual recurring</dt>
                <dd class="font-medium text-slate-700">{{ money(storageguard.economics.arr_min, storageguard.economics.arr_max, storageguard.economics.currency) }}</dd>
              </div>
              <div class="flex justify-between gap-3">
                <dt class="text-slate-400">AMC plan</dt>
                <dd class="font-medium text-slate-700">{{ storageguard.economics.amc_plan }}</dd>
              </div>
            </dl>
          </section>

          <section v-if="storageguard.calibration" class="portal-card">
            <h2 class="text-sm font-bold text-slate-800">Calibration</h2>
            <dl class="mt-3 space-y-2 text-sm">
              <div class="flex justify-between gap-3">
                <dt class="text-slate-400">Cycle</dt>
                <dd class="font-medium text-slate-700">Every {{ storageguard.calibration.cycle_months }} months</dd>
              </div>
              <div class="flex justify-between gap-3">
                <dt class="text-slate-400">Last calibrated</dt>
                <dd class="font-medium text-slate-700">{{ storageguard.calibration.last_calibrated || '—' }}</dd>
              </div>
              <div class="flex justify-between gap-3">
                <dt class="text-slate-400">Next due</dt>
                <dd class="font-semibold text-cyan-600">{{ storageguard.calibration.next_due || '—' }}</dd>
              </div>
            </dl>
          </section>
        </div>

        <section v-if="storageguard.alert_flow?.length" class="portal-card">
          <h2 class="text-sm font-bold text-slate-800">Alert Flow</h2>
          <ol class="mt-4 grid gap-3 md:grid-cols-5">
            <li v-for="(step, index) in storageguard.alert_flow" :key="step" class="rounded-xl bg-slate-50 p-3 text-xs leading-relaxed text-slate-600">
              <span class="mb-2 flex h-6 w-6 items-center justify-center rounded-full bg-cyan-100 text-[10px] font-bold text-cyan-700">{{ index + 1 }}</span>
              {{ step }}
            </li>
          </ol>
        </section>

        <StorageGuardReportPreview v-if="storageguard.report_preview" :report="storageguard.report_preview" />
      </template>

      <section class="portal-card">
        <h2 class="text-sm font-bold text-slate-800">Project Details</h2>
        <dl class="mt-4 grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt class="text-slate-400">Start date</dt>
            <dd class="mt-1 font-medium text-slate-700">{{ project.start_date || 'Not scheduled' }}</dd>
          </div>
          <div>
            <dt class="text-slate-400">Expected delivery</dt>
            <dd class="mt-1 font-medium text-slate-700">{{ project.expected_delivery_date || 'Not scheduled' }}</dd>
          </div>
          <div>
            <dt class="text-slate-400">Created</dt>
            <dd class="mt-1 font-medium text-slate-700">{{ new Date(project.created_at).toLocaleDateString() }}</dd>
          </div>
        </dl>
      </section>
    </template>

    <div v-else class="portal-card py-16 text-center text-sm text-slate-400">
      {{ loading ? 'Loading project...' : 'Project not found' }}
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'portal', middleware: 'auth' })

const route = useRoute()
const { apiFetch } = useApi()
const project = ref<any>(null)
const loading = ref(true)

const statusSteps = [
  { key: 'planning' }, { key: 'site_survey' }, { key: 'quotation_confirmed' },
  { key: 'procurement' }, { key: 'delivery' }, { key: 'installation' },
  { key: 'testing' }, { key: 'handover' }, { key: 'maintenance' }, { key: 'closed' },
]

const currentStepIndex = computed(() => statusSteps.findIndex(step => step.key === project.value?.status))
const storageguard = computed(() => {
  const plan = project.value?.project_plan_json
  return plan?.solution_line === 'storageguard' ? plan : null
})
const monitoringMetrics = computed(() => [
  { label: 'Points', value: storageguard.value?.monitoring_points?.total },
  { label: 'Temp / humidity', value: storageguard.value?.monitoring_points?.temperature_humidity },
  { label: 'Door events', value: storageguard.value?.monitoring_points?.door_events },
  { label: 'Outage alerts', value: storageguard.value?.monitoring_points?.outage_alert },
])

function statusClass(status: string) {
  if (['closed', 'handover'].includes(status)) return 'bg-emerald-50 text-emerald-600'
  if (['planning', 'site_survey'].includes(status)) return 'bg-blue-50 text-blue-600'
  return 'bg-amber-50 text-amber-600'
}

function riskClass(level: string) {
  if (level === 'high') return 'bg-red-50 text-red-600'
  if (level === 'medium') return 'bg-amber-50 text-amber-600'
  return 'bg-emerald-50 text-emerald-600'
}

function money(min: number, max: number, currency = 'EUR') {
  const symbol = currency === 'EUR' ? '€' : `${currency} `
  const format = (value: number) => symbol + Number(value).toLocaleString()
  if (min && max && min !== max) return `${format(min)} - ${format(max)}`
  return format(max || min || 0)
}

onMounted(async () => {
  try {
    project.value = await apiFetch<any>(`/projects/${route.params.id}`)
  } finally {
    loading.value = false
  }
})
</script>
