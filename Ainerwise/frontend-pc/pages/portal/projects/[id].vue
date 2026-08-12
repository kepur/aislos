<template>
  <div class="space-y-6">
    <NuxtLink :to="localized('/portal/projects')" class="inline-flex items-center gap-1 text-sm font-medium ws-accent hover:opacity-80">
      <span aria-hidden="true">&larr;</span>
      {{ $t('pProjD.back') }}
    </NuxtLink>

    <template v-if="project">
      <section class="portal-card">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 class="text-xl font-bold ws-title">{{ project.title || project.name }}</h1>
            <p class="mt-1 text-sm ws-faint">{{ project.region || '-' }}</p>
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
              :class="currentStepIndex >= index ? 'bg-gradient-to-r from-blue-500 to-indigo-500' : 'ws-soft'"
            />
          </div>
          <div class="mt-2 flex justify-between text-[10px] font-medium uppercase tracking-wider ws-faint">
            <span>{{ $t('pProj.planning') }}</span>
            <span>{{ $t('pProj.delivery') }}</span>
            <span>{{ $t('pProjD.maintenance') }}</span>
            <span>{{ $t('pProj.closed') }}</span>
          </div>
        </div>
      </section>

      <template v-if="storageguard">
        <section class="portal-card">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 class="text-base font-bold ws-title">{{ $t('pProjD.sgMonitoring') }}</h2>
              <p v-if="storageguard.scenario" class="mt-1 text-sm leading-relaxed ws-muted">{{ storageguard.scenario }}</p>
            </div>
            <span v-if="storageguard.sample" class="rounded-full bg-cyan-50 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-cyan-600">
              {{ $t('pProjD.sample') }}
            </span>
          </div>
          <div class="mt-5 grid gap-3 sm:grid-cols-4">
            <div v-for="metric in monitoringMetrics" :key="metric.label" class="rounded-xl ws-sunken p-4 text-center">
              <p class="text-2xl font-bold ws-title">{{ metric.value ?? '—' }}</p>
              <p class="mt-1 text-xs font-medium ws-faint">{{ metric.label }}</p>
            </div>
          </div>
        </section>

        <div class="grid gap-6 lg:grid-cols-3">
          <section v-if="storageguard.compliance" class="portal-card">
            <div class="flex items-center justify-between gap-3">
              <h2 class="text-sm font-bold ws-title">{{ $t('pProjD.complianceRisk') }}</h2>
              <span :class="['rounded-full px-2.5 py-1 text-[10px] font-semibold', riskClass(storageguard.compliance.risk_level)]">
                {{ $t('pProjD.riskSuffix', { level: storageguard.compliance.risk_level }) }}
              </span>
            </div>
            <p class="mt-3 text-sm leading-relaxed ws-muted">{{ storageguard.compliance.risk_note }}</p>
          </section>

          <section v-if="storageguard.economics" class="portal-card">
            <h2 class="text-sm font-bold ws-title">{{ $t('pProjD.lifecycleEcon') }}</h2>
            <dl class="mt-3 space-y-2 text-sm">
              <div class="flex justify-between gap-3">
                <dt class="ws-faint">{{ $t('pProjD.initialCost') }}</dt>
                <dd class="font-medium ws-title">{{ money(storageguard.economics.initial_cost_min, storageguard.economics.initial_cost_max, storageguard.economics.currency) }}</dd>
              </div>
              <div class="flex justify-between gap-3">
                <dt class="ws-faint">{{ $t('pProjD.annualRecurring') }}</dt>
                <dd class="font-medium ws-title">{{ money(storageguard.economics.arr_min, storageguard.economics.arr_max, storageguard.economics.currency) }}</dd>
              </div>
              <div class="flex justify-between gap-3">
                <dt class="ws-faint">{{ $t('pProjD.amcPlan') }}</dt>
                <dd class="font-medium ws-title">{{ storageguard.economics.amc_plan }}</dd>
              </div>
            </dl>
          </section>

          <section v-if="storageguard.calibration" class="portal-card">
            <h2 class="text-sm font-bold ws-title">{{ $t('pProjD.calibration') }}</h2>
            <dl class="mt-3 space-y-2 text-sm">
              <div class="flex justify-between gap-3">
                <dt class="ws-faint">{{ $t('pProjD.cycle') }}</dt>
                <dd class="font-medium ws-title">{{ $t('pProjD.everyMonths', { n: storageguard.calibration.cycle_months }) }}</dd>
              </div>
              <div class="flex justify-between gap-3">
                <dt class="ws-faint">{{ $t('pProjD.lastCalibrated') }}</dt>
                <dd class="font-medium ws-title">{{ storageguard.calibration.last_calibrated || '—' }}</dd>
              </div>
              <div class="flex justify-between gap-3">
                <dt class="ws-faint">{{ $t('pProjD.nextDue') }}</dt>
                <dd class="font-semibold text-cyan-600">{{ storageguard.calibration.next_due || '—' }}</dd>
              </div>
            </dl>
          </section>
        </div>

        <section v-if="storageguard.alert_flow?.length" class="portal-card">
          <h2 class="text-sm font-bold ws-title">{{ $t('pProjD.alertFlow') }}</h2>
          <ol class="mt-4 grid gap-3 md:grid-cols-5">
            <li v-for="(step, index) in storageguard.alert_flow" :key="step" class="rounded-xl ws-sunken p-3 text-xs leading-relaxed ws-muted">
              <span class="mb-2 flex h-6 w-6 items-center justify-center rounded-full bg-cyan-100 text-[10px] font-bold text-cyan-700">{{ index + 1 }}</span>
              {{ step }}
            </li>
          </ol>
        </section>

        <StorageGuardReportPreview v-if="storageguard.report_preview" :report="storageguard.report_preview" />
      </template>

      <section class="portal-card">
        <h2 class="text-sm font-bold ws-title">{{ $t('pProjD.projectDetails') }}</h2>
        <dl class="mt-4 grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt class="ws-faint">{{ $t('pProjD.startDate') }}</dt>
            <dd class="mt-1 font-medium ws-title">{{ project.start_date || $t('pProjD.notScheduled') }}</dd>
          </div>
          <div>
            <dt class="ws-faint">{{ $t('pProjD.expectedDelivery') }}</dt>
            <dd class="mt-1 font-medium ws-title">{{ project.expected_delivery_date || $t('pProjD.notScheduled') }}</dd>
          </div>
          <div>
            <dt class="ws-faint">{{ $t('pProjD.created') }}</dt>
            <dd class="mt-1 font-medium ws-title">{{ formatDay(project.created_at) }}</dd>
          </div>
        </dl>
      </section>
    </template>

    <div v-else class="portal-card py-16 text-center text-sm ws-faint">
      {{ loading ? $t('pProjD.loading') : $t('pProjD.notFound') }}
    </div>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
const { formatDay } = useLocaleFormat()
definePageMeta({ layout: 'procurement', middleware: 'auth' })

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
  { label: t('pProjD.metricPoints'), value: storageguard.value?.monitoring_points?.total },
  { label: t('pProjD.metricTempHum'), value: storageguard.value?.monitoring_points?.temperature_humidity },
  { label: t('pProjD.metricDoorEvents'), value: storageguard.value?.monitoring_points?.door_events },
  { label: t('pProjD.metricOutage'), value: storageguard.value?.monitoring_points?.outage_alert },
])

function statusClass(status: string) {
 if (['closed', 'handover'].includes(status)) return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
 if (['planning', 'site_survey'].includes(status)) return 'bg-blue-500/15 ws-accent dark:text-blue-300'
 return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
}

function riskClass(level: string) {
 if (level === 'high') return 'bg-red-500/15 text-red-600 dark:text-red-300'
 if (level === 'medium') return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
 return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
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
